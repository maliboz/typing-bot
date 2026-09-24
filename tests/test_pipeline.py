import json
import unittest
from unittest.mock import Mock

from typing_coach.automation import _drive_loop, _validate
from typing_coach.cdp import CdpConnection, key_events


def state(token, word="aynı", **extra):
    return dict(ready=True, word=word, token=token, errors=0, **extra)


class PipelineTest(unittest.TestCase):
    def test_repeated_words_need_distinct_positions(self):
        send = Mock()
        wait = Mock(side_effect=[state("1"), state("2")])
        result = _drive_loop(state("0"), send, wait, duration=10, max_words=2, delay=0)
        self.assertEqual(result[:2], (2, 2))
        self.assertEqual([c.args[0] for c in send.call_args_list], ["aynı", "aynı"])
        self.assertEqual([c.args[0]["token"] for c in wait.call_args_list], ["0", "1"])

    def test_stalled_submission_is_not_counted_or_retried(self):
        send = Mock()
        wait = Mock(return_value=state("0", timedOut=True))
        result = _drive_loop(state("0"), send, wait, duration=10, max_words=100, delay=0)
        self.assertEqual(result[:2], (0, 1))
        self.assertEqual(result[3], "stalled")
        send.assert_called_once()

    def test_finite_word_list_exhaustion_is_not_a_stall(self):
        result = _drive_loop(state("last"), Mock(), Mock(return_value={"exhausted": True}),
                             duration=10, max_words=100, delay=0)
        self.assertEqual(result[:2], (1, 1))
        self.assertEqual(result[3], "words_exhausted")

    def test_pacing_respects_overall_deadline(self):
        from unittest.mock import patch
        now = [0.0]
        def sleep(seconds):
            now[0] += seconds
        send = Mock()
        with patch('typing_coach.automation.time.perf_counter', side_effect=lambda: now[0]), \
             patch('typing_coach.automation.time.sleep', side_effect=sleep):
            result = _drive_loop(state("0", word="test"), send, Mock(return_value=state("1")),
                                 duration=1, max_words=100, delay=0, wpm=1)
        self.assertEqual(result[:2], (1, 1))
        self.assertEqual(result[3], 'duration')
        self.assertEqual(now[0], 1)

    def test_no_active_marker_never_guesses_first_word(self):
        send = Mock()
        result = _drive_loop({"ready": False}, send, Mock(), duration=10, max_words=100, delay=0)
        self.assertEqual(result[3], "unsupported_page")
        send.assert_not_called()

    def test_increased_error_count_stops_typing(self):
        send = Mock()
        next_state = state("1")
        next_state["errors"] = 1
        result = _drive_loop(state("0"), send, Mock(return_value=next_state),
                             duration=10, max_words=100, delay=0)
        self.assertEqual(result[3], "input_error")
        send.assert_called_once()

    def test_invalid_limits_rejected_before_launch(self):
        for args in [(0, 0, 1, "turbo", 0), (1, -1, 1, "turbo", 0),
                     (1, float("nan"), 1, "turbo", 0), (1, 0, 0, "turbo", 0),
                     (1, 0, 1, "bad", 0), (1, 0, 1, "turbo", -1)]:
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                _validate(*args)


class CdpTest(unittest.TestCase):
    def test_turkish_characters_have_native_down_and_up(self):
        text = "çğıöşüİ "
        events = list(key_events(text))
        self.assertEqual(len(events), len(text) * 2)
        for char, down, up in zip(text, events[::2], events[1::2]):
            self.assertEqual(down["key"], char)
            self.assertEqual(down["text"], char)
            self.assertEqual(down["type"], "keyDown")
            self.assertEqual(up["key"], char)
            self.assertEqual(up["type"], "keyUp")
            self.assertNotIn("text", up)
        self.assertEqual(events[-1]["code"], "Space")

    def test_out_of_order_responses_and_events_are_drained(self):
        connection = CdpConnection.__new__(CdpConnection)
        connection.sequence = 0
        connection.socket = Mock()
        connection.socket.recv.side_effect = [json.dumps(r) for r in [
            {"method": "Page.loadEventFired"}, {"id": 2, "result": {"ok": 2}},
            {"id": 1, "result": {"ok": 1}}]]
        self.assertEqual(connection.batch([("one", {}), ("two", {})]), [{"ok": 1}, {"ok": 2}])

    def test_late_protocol_error_is_not_lost(self):
        connection = CdpConnection.__new__(CdpConnection)
        connection.sequence = 0
        connection.socket = Mock()
        connection.socket.recv.side_effect = [json.dumps(r) for r in [
            {"id": 2, "result": {}}, {"id": 1, "error": {"message": "bad key"}}]]
        with self.assertRaisesRegex(RuntimeError, "bad key"):
            connection.batch([("one", {}), ("two", {})])


if __name__ == "__main__":
    unittest.main()
