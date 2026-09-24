"""A bounded, word-at-a-time native keyboard pipeline over a local CDP socket."""

from __future__ import annotations

import json
from urllib.request import ProxyHandler, build_opener
from urllib.parse import urlparse


def key_events(text: str):
    """Include keyDown for Turkish characters, unlike keyboard.type's US mapping."""
    for char in text:
        code = 32 if char == " " else ord(char.upper()) if char.isascii() and char.isalnum() else 0
        base = {"key": char, "windowsVirtualKeyCode": code}
        if char == " ":
            base["code"] = "Space"
        yield {**base, "type": "keyDown", "text": char, "unmodifiedText": char}
        yield {**base, "type": "keyUp"}


class CdpConnection:
    def __init__(self, address: str, target_id: str):
        try:
            import websocket
        except ImportError as exc:
            raise RuntimeError("Install websocket-client: python -m pip install '.[all]'") from exc
        parsed = urlparse("http://" + address)
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise RuntimeError("CDP must be bound to loopback.")
        opener = build_opener(ProxyHandler({}))
        with opener.open(f"http://{address}/json/list", timeout=5) as response:
            targets = json.load(response)
        target = next((t for t in targets if t.get("id") == target_id), None)
        if not target:
            raise RuntimeError("The typing page's CDP target was not found.")
        self.socket = websocket.create_connection(
            target["webSocketDebuggerUrl"], timeout=5, suppress_origin=True,
            http_no_proxy=["127.0.0.1", "localhost", "::1"],
        )
        self.sequence = 0

    def batch(self, commands):
        """Send in order; consume and check every response, including late errors."""
        try:
            return self._batch(commands)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"CDP connection failed: {exc}") from exc

    def _batch(self, commands):
        pending, replies, failures = set(), {}, []
        for method, params in commands:
            self.sequence += 1
            pending.add(self.sequence)
            self.socket.send(json.dumps({"id": self.sequence, "method": method, "params": params}))
        while pending:
            reply = json.loads(self.socket.recv())
            request_id = reply.get("id")
            if request_id not in pending:
                continue
            pending.remove(request_id)
            if "error" in reply:
                failures.append(reply["error"])
            replies[request_id] = reply.get("result", {})
        if failures:
            raise RuntimeError(f"CDP rejected keyboard commands: {failures}")
        return [replies[key] for key in sorted(replies)]

    def type_word(self, word: str):
        self.batch(("Input.dispatchKeyEvent", event) for event in key_events(word + " "))

    def evaluate(self, expression: str):
        result = self.batch([("Runtime.evaluate", {
            "expression": expression, "awaitPromise": True, "returnByValue": True,
        })])[0]
        if "exceptionDetails" in result:
            raise RuntimeError(f"Page adapter failed: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")

    def close(self):
        self.socket.close()
