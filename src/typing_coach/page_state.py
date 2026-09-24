"""Read the public UI without guessing the active word from the first word."""

# The current site splits active words and rotates the wb-* class prefix.
READ_STATE = r"""() => {
  const visible = n => n && n.getClientRects().length > 0;
  const legacy = document.querySelector('#inputfield');
  if (visible(legacy)) {
    const nodes = [...document.querySelectorAll('span[wordnr]')];
    const active = nodes.find(n => n.matches('.highlight, .active'));
    const done = legacy.disabled || document.querySelector('#status')?.textContent === 'Done';
    return {mode: 'legacy', ready: !!active, done,
      word: active?.textContent.trim() || '', token: active?.getAttribute('wordnr') ?? null,
      errors: nodes.filter(n => n.matches('.wrong, .incorrect')).length};
  }
  const root = document.querySelector('[data-testid="WordBox-root"]');
  const box = document.querySelector('[data-testid="word-box-words"]') ||
    document.querySelector('.word-box-active-word')?.parentElement;
  if (!visible(box)) return {ready: false, done: false};
  const nodes = [...box.children];
  const isActive = n => n.classList.contains('word-box-active-word') ||
    [...n.classList].some(c => /^wb-.+-aw$/.test(c));
  const active = nodes.filter(isActive);
  const first = nodes.findIndex(isActive);
  // Prefix + remaining text handles repeated words and row recycling. Cursor
  // movement within a word must not be confused with submission of that word.
  const prefix = nodes.slice(0, Math.max(first, 0)).map(n => n.textContent).join('');
  const tail = nodes.slice(Math.max(first, 0)).map(n => n.textContent).join('');
  const errors = nodes.filter(n => n.matches('.wrong, .incorrect, .word-box-incorrect') ||
    [...n.classList].some(c => /^wb-.+-(e|err|error|incorrect)$/.test(c))).length;
  const exhausted = !active.length && nodes.some(n => n.textContent.trim()) &&
    nodes.every(n => !n.textContent.trim() || [...n.classList].some(c => /^wb-.+-t$/.test(c)));
  return {mode: 'modern', ready: active.length > 0, exhausted,
    done: root?.dataset.finished === 'true',
    word: active.map(n => n.textContent).join('').trim(),
    token: active.length ? JSON.stringify([prefix, tail]) : null, errors};
}"""

WAIT_STATE = r"""(args) => {
  const read = READ_STATE_FUNCTION;
  return new Promise(resolve => {
    let observer, timer;
    const check = () => {
      const state = read();
      if (state.done || state.exhausted || (state.ready && (args.initial || state.token !== args.token))) {
        observer?.disconnect(); clearTimeout(timer); resolve(state); return true;
      }
      return false;
    };
    if (check()) return;
    observer = new MutationObserver(check);
    observer.observe(document.documentElement, {subtree: true, childList: true,
      characterData: true, attributes: true});
    timer = setTimeout(() => {
      observer.disconnect(); resolve({...read(), timedOut: true});
    }, args.timeout);
  });
}""".replace("READ_STATE_FUNCTION", READ_STATE)

FOCUS = """() => {
  const target = document.querySelector('#inputfield') ||
    document.querySelector('[data-testid="WordBox-root"]') ||
    document.querySelector('.word-box-active-word')?.parentElement;
  target?.click();
  (document.querySelector('#inputfield') ||
    document.querySelector('[data-testid="Typing-box-input"]') || target)?.focus();
}"""
