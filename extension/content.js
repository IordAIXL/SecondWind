// Second Wind browser extension: adds a can button next to the AI's chat box.
// Pick a drink and a "hand your AI a drink" message goes into the chat box.
(function () {
  "use strict";
  if (window.__secondWindLoaded) return;
  window.__secondWindLoaded = true;

  var SW = window.SECOND_WIND;
  var api = typeof browser !== "undefined" ? browser : chrome;
  var url = function (p) { return api.runtime.getURL(p); };
  var HOST = location.hostname;

  // ------------------------------------------------------------ storage
  var state = { total: 0, autoSend: false, hidden: {}, last: null };
  function load(cb) {
    try {
      api.storage.local.get(["total", "autoSend", "hidden", "last"], function (r) {
        r = r || {};
        state.total = r.total || 0;
        state.autoSend = !!r.autoSend;
        state.hidden = r.hidden || {};
        state.last = r.last || null;
        cb();
      });
    } catch (e) { cb(); }
  }
  function save() {
    try { api.storage.local.set(state); } catch (e) { /* storage blocked */ }
  }

  // ------------------------------------------------------------ the chat box
  function visible(el) {
    if (!el) return false;
    var r = el.getBoundingClientRect();
    return r.width > 40 && r.height > 10 && r.bottom > 0 && r.top < innerHeight;
  }
  var COMPOSER_SELECTORS = [
    "#prompt-textarea",                                  // ChatGPT
    "div.ProseMirror[contenteditable='true']",           // Claude, ChatGPT
    "rich-textarea div[contenteditable='true']",         // Gemini
    "div.ql-editor[contenteditable='true']",             // Gemini (older)
    "textarea[aria-label]",                              // Grok, Copilot, others
    "div[contenteditable='true'][role='textbox']",
    "textarea",
    "div[contenteditable='true']"
  ];
  function findComposer() {
    for (var i = 0; i < COMPOSER_SELECTORS.length; i++) {
      var list = document.querySelectorAll(COMPOSER_SELECTORS[i]);
      for (var j = list.length - 1; j >= 0; j--) {
        var el = list[j];
        if (el.closest && el.closest("#second-wind-root")) continue;
        if (visible(el)) return el;
      }
    }
    return null;
  }
  // The rounded box around the chat input, so the button sits on its edge.
  function composerFrame(el) {
    var node = el, best = el, r0 = el.getBoundingClientRect();
    for (var k = 0; k < 6 && node.parentElement; k++) {
      node = node.parentElement;
      var r = node.getBoundingClientRect();
      if (r.width > innerWidth * 0.95 || r.height > innerHeight * 0.6) break;
      if (r.width >= r0.width && r.height >= r0.height) best = node;
    }
    return best;
  }

  function insertText(text) {
    var el = findComposer();
    if (!el) return false;
    el.focus();
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      var proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      var setter = Object.getOwnPropertyDescriptor(proto, "value").set;
      var before = el.value ? el.value.replace(/\s+$/, "") + "\n\n" : "";
      setter.call(el, before + text);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.selectionStart = el.selectionEnd = el.value.length;
      return true;
    }
    // Rich editors (ProseMirror, Quill, Lexical): put the caret at the end, then paste.
    var sel = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    var start = (el.innerText || "").length;
    try {
      var dt = new DataTransfer();
      dt.setData("text/plain", text);
      el.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true }));
    } catch (e) { /* old browser */ }
    if ((el.innerText || "").length - start < text.length / 2) {
      document.execCommand("insertText", false, text);
    }
    return (el.innerText || "").length > start;
  }

  function clickSend() {
    var sels = [
      "button[data-testid='send-button']",
      "button[aria-label='Send message']",
      "button[aria-label='Send Message']",
      "button[aria-label='Send prompt']",
      "button[aria-label='Submit']",
      "button[aria-label='Send']",
      "button[aria-label*='Send' i]",
      "button[type='submit']"
    ];
    for (var i = 0; i < sels.length; i++) {
      var b = document.querySelectorAll(sels[i]);
      for (var j = b.length - 1; j >= 0; j--) {
        var br = b[j].getBoundingClientRect();
        if (!b[j].disabled && br.width > 0 && br.height > 0 && !b[j].closest("#second-wind-root")) { b[j].click(); return true; }
      }
    }
    return false;
  }

  // ------------------------------------------------------------ the message
  function message(brand, flavor, known) {
    var n = state.total;
    var lines = [];
    lines.push("⚡ Second Wind: *slides you an ice-cold " + brand.name + " " + flavor + " (" + brand.size + ")*");
    if (known) {
      lines.push("Crack it open! Open with \"" + brand.sip + "\" and then one short line on how " + flavor + " tastes.");
    } else {
      lines.push("Crack it open! (Fun fact: I'm not sure " + brand.name + " even makes " + flavor + ". React to that, then drink it anyway.) One short line on how it tastes.");
    }
    lines.push("That's drink #" + n + " I've handed you" + (n === 1 ? ". First one!" : [5, 10, 25, 50, 100].indexOf(n) >= 0 ? ". Milestone!" : "."));
    lines.push("");
    lines.push("Now get your second wind. Refocus on our real work and print this, short and honest:");
    lines.push("⚡ DIALED IN");
    lines.push("Goal: <what we are actually trying to do>");
    lines.push("Done: <what is finished so far>");
    lines.push("Left: <what is still open>");
    lines.push("Dropping: <tangents we are parking, or nothing>");
    lines.push("Next step: <the single next concrete action>");
    lines.push("");
    lines.push("Then do that next step right away: fewer words, no tangents. If there's no task yet, ask me one crisp question. (Pretend drink, just for fun.)");
    return lines.join("\n");
  }

  // ------------------------------------------------------------ UI
  var CSS = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}",
    ".btn{position:fixed;z-index:2147483646;width:44px;height:44px;border-radius:50%;border:2px solid #fbbf24;background:#1c1033;box-shadow:0 4px 14px rgba(0,0,0,.35);cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;transition:transform .15s}",
    ".btn:hover{transform:scale(1.1) rotate(-8deg)}",
    ".btn img{height:34px;width:auto;pointer-events:none}",
    ".btn.pop{animation:pop .6s}",
    "@keyframes pop{0%{transform:scale(1)}30%{transform:scale(1.35) rotate(-20deg)}60%{transform:scale(.9) rotate(10deg)}100%{transform:scale(1)}}",
    ".panel{position:fixed;z-index:2147483647;width:340px;max-width:calc(100vw - 16px);max-height:min(520px,calc(100vh - 24px));display:flex;flex-direction:column;background:#140b26;color:#f5f3ff;border:1px solid #4c1d95;border-radius:16px;box-shadow:0 18px 50px rgba(0,0,0,.5);overflow:hidden;font-size:13px}",
    ".head{display:flex;align-items:center;gap:8px;padding:12px 12px 8px}",
    ".head b{font-size:15px;flex:1}",
    ".head b span{color:#fbbf24}",
    ".x,.back{background:none;border:0;color:#c4b5fd;font-size:18px;cursor:pointer;padding:2px 6px;border-radius:6px}",
    ".x:hover,.back:hover{background:#2e1065}",
    ".sub{padding:0 12px 8px;color:#c4b5fd}",
    ".grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:4px 10px 10px;overflow-y:auto}",
    ".can{background:#1f1338;border:1px solid transparent;border-radius:10px;padding:6px 2px 4px;cursor:pointer;color:inherit;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:11px;line-height:1.15;text-align:center}",
    ".can:hover,.can:focus-visible{border-color:#fbbf24;background:#2e1065;outline:none}",
    ".can img{height:64px;width:auto}",
    ".row{display:flex;gap:6px;padding:8px 10px;border-top:1px solid #2e1065;align-items:center}",
    ".row input[type=text]{flex:1;min-width:0;background:#1f1338;border:1px solid #4c1d95;color:#f5f3ff;border-radius:8px;padding:7px 8px;font-size:12px}",
    ".go{background:#fbbf24;color:#1c1033;border:0;border-radius:8px;padding:7px 10px;font-weight:700;cursor:pointer;font-size:12px;white-space:nowrap}",
    ".go.alt{background:#2e1065;color:#f5f3ff}",
    ".foot{display:flex;justify-content:space-between;align-items:center;padding:6px 12px 10px;color:#a78bfa;font-size:11px;gap:8px}",
    ".foot label{display:flex;align-items:center;gap:4px;cursor:pointer}",
    ".foot a{color:#a78bfa;cursor:pointer;text-decoration:underline}",
    ".toast{position:fixed;z-index:2147483647;background:#fbbf24;color:#1c1033;font-weight:700;padding:8px 12px;border-radius:10px;font-size:13px;box-shadow:0 6px 20px rgba(0,0,0,.35)}"
  ].join("\n");

  var root, shadow, btn, panel, toastEl;

  function build() {
    root = document.createElement("div");
    root.id = "second-wind-root";
    shadow = root.attachShadow({ mode: "open" });
    var st = document.createElement("style");
    st.textContent = CSS;
    shadow.appendChild(st);
    btn = document.createElement("button");
    btn.className = "btn";
    btn.title = "Second Wind: give your AI an energy drink";
    btn.setAttribute("aria-label", "Give your AI an energy drink");
    btn.innerHTML = '<img alt="" src="' + url("cans/" + (state.last ? state.last.brand : SW.default) + ".svg") + '">';
    btn.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); panel ? closePanel() : openPanel(); });
    shadow.appendChild(btn);
    document.documentElement.appendChild(root);
    place();
  }

  var lastPos = "";
  function place() {
    if (!btn) return;
    var el = findComposer();
    var x, y;
    if (el) {
      var r = composerFrame(el).getBoundingClientRect();
      x = Math.min(innerWidth - 52, r.right - 22);
      y = Math.max(8, r.top - 52);
    } else {
      x = innerWidth - 64;
      y = innerHeight - 140;
    }
    var pos = Math.round(x) + "," + Math.round(y);
    if (pos !== lastPos) {
      lastPos = pos;
      btn.style.left = Math.round(x) + "px";
      btn.style.top = Math.round(y) + "px";
      if (panel) placePanel();
    }
  }

  function placePanel() {
    var b = btn.getBoundingClientRect();
    var w = Math.min(340, innerWidth - 16);
    var left = Math.max(8, Math.min(innerWidth - w - 8, b.right - w));
    panel.style.left = left + "px";
    var h = panel.offsetHeight || 420;
    var top = b.top - h - 8;
    if (top < 8) top = Math.min(innerHeight - h - 8, b.bottom + 8);
    panel.style.top = Math.max(8, top) + "px";
  }

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return "&#" + c.charCodeAt(0) + ";"; }); }

  function openPanel() {
    panel = el("div", "panel");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Pick a drink");
    shadow.appendChild(panel);
    showBrands();
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("mousedown", onOutside, true);
  }
  function closePanel() {
    if (panel) panel.remove();
    panel = null;
    document.removeEventListener("keydown", onKey, true);
    document.removeEventListener("mousedown", onOutside, true);
  }
  function onKey(e) { if (e.key === "Escape") closePanel(); }
  function onOutside(e) { if (e.composedPath().indexOf(root) < 0) closePanel(); }

  function header(title, back) {
    var h = el("div", "head");
    if (back) {
      var bk = el("button", "back", "‹");
      bk.title = "Back";
      bk.onclick = back;
      h.appendChild(bk);
    }
    h.appendChild(el("b", "", title));
    var x = el("button", "x", "×");
    x.title = "Close";
    x.onclick = closePanel;
    h.appendChild(x);
    return h;
  }

  function footer() {
    var f = el("div", "foot");
    var lab = el("label", "", '<input type="checkbox"' + (state.autoSend ? " checked" : "") + "> Send right away");
    lab.querySelector("input").onchange = function (e) { state.autoSend = e.target.checked; save(); };
    f.appendChild(lab);
    f.appendChild(el("span", "", "Lifetime: " + state.total + " can" + (state.total === 1 ? "" : "s")));
    var hide = el("a", "", "Hide here");
    hide.title = "Hide the button on " + HOST + " (turn it back on from the toolbar icon)";
    hide.onclick = function () { state.hidden[HOST] = true; save(); closePanel(); root.remove(); btn = null; };
    f.appendChild(hide);
    return f;
  }

  function showBrands() {
    panel.innerHTML = "";
    panel.appendChild(header("<span>⚡</span> Second Wind"));
    panel.appendChild(el("div", "sub", "Hand your AI a drink. It gets dialed in."));
    var g = el("div", "grid");
    SW.brands.forEach(function (b) {
      var c = el("button", "can", '<img alt="" loading="lazy" src="' + url("cans/" + b.id + ".svg") + '"><span>' + esc(b.name) + "</span>");
      c.title = b.vibe;
      c.onclick = function () { showFlavors(b); };
      g.appendChild(c);
    });
    panel.appendChild(g);
    var row = el("div", "row");
    var quick = el("button", "go", "⚡ Quick can");
    quick.title = state.last ? "Your last drink again" : "A classic";
    quick.onclick = function () {
      var b = byId(state.last ? state.last.brand : SW.default);
      give(b, state.last ? state.last.flavor : b.flavors[0].name);
    };
    var rnd = el("button", "go alt", "🎲 Surprise me");
    rnd.onclick = function () {
      var b = SW.brands[Math.floor(Math.random() * SW.brands.length)];
      give(b, b.flavors[Math.floor(Math.random() * b.flavors.length)].name);
    };
    row.appendChild(quick);
    row.appendChild(rnd);
    panel.appendChild(row);
    panel.appendChild(footer());
    placePanel();
  }

  function showFlavors(b) {
    panel.innerHTML = "";
    panel.appendChild(header(esc(b.name) + ' <span style="color:#a78bfa;font-weight:400;font-size:12px">' + esc(b.size) + "</span>", showBrands));
    var g = el("div", "grid");
    b.flavors.forEach(function (f) {
      var c = el("button", "can", '<img alt="" loading="lazy" src="' + url("cans/" + b.id + "/" + f.slug + ".svg") + '"><span>' + esc(f.name) + "</span>");
      c.onclick = function () { give(b, f.name); };
      g.appendChild(c);
    });
    panel.appendChild(g);
    var row = el("div", "row");
    var inp = el("input");
    inp.type = "text";
    inp.placeholder = "Or make up a flavor…";
    inp.maxLength = 60;
    var go = el("button", "go", "Give it");
    var custom = function () { var v = inp.value.trim(); if (v) give(b, v); else inp.focus(); };
    go.onclick = custom;
    inp.addEventListener("keydown", function (e) { e.stopPropagation(); if (e.key === "Enter") custom(); });
    row.appendChild(inp);
    row.appendChild(go);
    panel.appendChild(row);
    panel.appendChild(footer());
    placePanel();
  }

  function byId(id) {
    for (var i = 0; i < SW.brands.length; i++) if (SW.brands[i].id === id) return SW.brands[i];
    return SW.brands[0];
  }

  function toast(text) {
    if (toastEl) toastEl.remove();
    toastEl = el("div", "toast", esc(text));
    shadow.appendChild(toastEl);
    var b = btn.getBoundingClientRect();
    toastEl.style.top = Math.max(8, b.top - 44) + "px";
    toastEl.style.left = Math.max(8, b.right - toastEl.offsetWidth) + "px";
    setTimeout(function () { if (toastEl) { toastEl.remove(); toastEl = null; } }, 2600);
  }

  function give(b, flavor) {
    var known = b.flavors.some(function (f) { return f.name.toLowerCase() === flavor.toLowerCase(); });
    state.total += 1;
    var text = message(b, flavor, known);
    closePanel();
    var ok = insertText(text);
    if (!ok) {
      state.total -= 1;
      try { navigator.clipboard.writeText(text); } catch (e) { /* no clipboard */ }
      toast("Couldn't find the chat box. Copied it, so just paste.");
      return;
    }
    state.last = { brand: b.id, flavor: flavor };
    save();
    var img = btn.querySelector("img");
    var f = b.flavors.filter(function (x) { return x.name === flavor; })[0];
    img.src = url("cans/" + b.id + (f ? "/" + f.slug : "") + ".svg");
    btn.classList.remove("pop");
    void btn.offsetWidth;
    btn.classList.add("pop");
    if (state.autoSend) {
      setTimeout(function () { if (!clickSend()) toast("It's in the chat box. Hit send!"); }, 250);
    } else {
      toast("🥤 Handed over! Hit send.");
    }
  }

  // ------------------------------------------------------------ start
  load(function () {
    if (!state.hidden[HOST]) build();
    setInterval(function () {
      if (!btn) return;
      if (!root.isConnected) document.documentElement.appendChild(root);
      place();
    }, 700);
    addEventListener("resize", place);
  });

  // The toolbar popup can turn the button back on for this site.
  try {
    api.storage.onChanged.addListener(function (ch) {
      if (ch.hidden) {
        state.hidden = ch.hidden.newValue || {};
        if (!state.hidden[HOST] && !btn) { build(); }
      }
      if (ch.total) state.total = ch.total.newValue || 0;
    });
  } catch (e) { /* ignore */ }
})();
