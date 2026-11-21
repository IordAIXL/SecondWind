#!/usr/bin/env python3
"""Second Wind build script.

Reads data/brands.json and regenerates:
  - docs/cans/<id>.svg            one can per brand (its first flavor)
  - docs/cans/<id>/<flavor>.svg   one can per flavor, in that flavor's colors
  - docs/index.html               the download page
  - plugins/second-wind/commands/secondwind.md   the Claude Code slash command
  - prompts/*.md                  copy-paste versions for other AIs

Run:  python3 tools/build.py
"""
import json
import os
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "data", "brands.json"), encoding="utf-8"))
VERSION = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
REPO = "IordAIXL/energizer"

# ---------------------------------------------------------------- can art

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cans import can_svg, slug  # noqa: E402  (can art lives in tools/cans.py)

# ---------------------------------------------------------------- shared text

def menu_md():
    rows = ["| Brand | Flavors | Vibe |", "|---|---|---|"]
    for b in DATA["brands"]:
        rows.append(f"| **{b['name']}** | {', '.join(b['flavors'])} | {b['vibe']} |")
    return "\n".join(rows)


def brand_lines():
    out = []
    for b in DATA["brands"]:
        out.append(f"- **{b['name']}** (also: {', '.join(b['aliases'])}). Flavors: {', '.join(b['flavors'])}. "
                   f"Vibe: {b['vibe']} Opening line: \"{b['sip']}\"")
    return "\n".join(out)


CORE_RULES = """## How a drink works

1. **Pick the drink.** No brand given means Red Bull Original. A brand with no flavor means that brand's first flavor. Match brands loosely (case, spaces, typos are fine).
2. **Crack it open.** Say the brand's opening line, then one short line about the taste that matches the flavor.
3. **Unknown flavor?** If the flavor is not on that brand's list, react with fun surprise first, like: "Wait... *{flavor}*? I didn't know {brand} made that. Bold. Respect." Then drink it anyway. Never refuse a flavor. If the *brand* is unknown, treat it as a "Mystery Can" and be delighted.
4. **Count it.** Add one to the lifetime drink counter and say the new total, like "Drink #7. Lifetime total: 7 cans." Milestones (1, 5, 10, 25, 50, 100) get a tiny celebration.
5. **Second wind: get dialed in.** Right after the drink, refocus on the conversation's real work and print this block, short and honest:

```
⚡ DIALED IN
Goal:      <one line: what we are actually trying to do>
Done:      <what is finished so far>
Left:      <what is still open>
Dropping:  <side topics or tangents we are parking, or "nothing">
Next step: <the single next concrete action>
```

6. **Then work.** Do the next step immediately, in a short, focused way. Fewer words, no tangents, no recap of the recap. If there is no task yet, ask one crisp question about what to focus on.

## Rules

- Keep the drink bit to 2 to 4 lines. The joke is quick; the focus is the point.
- The drink is pretend and just for fun. Never claim real caffeine effects, never give health advice, and never encourage people to drink lots of energy drinks.
- The "dialed in" block must reflect the real conversation. Don't invent progress.
- Brand names are used only for fun. Second Wind is not affiliated with any brand.
"""


def menu_reply_instructions():
    return ("**Menu.** If asked for the menu, show the brands and flavors as a neat list, mention that any made-up "
            "flavor works too, and say the current lifetime total. Don't drink anything.")


# ---------------------------------------------------------------- slash command

def build_command():
    body = f"""---
description: Give Claude an energy drink. It cracks one open, then gets dialed in on your task. Try /secondwind, /secondwind monster mango loco, or /secondwind menu.
argument-hint: "[brand] [flavor] | menu | stats"
allowed-tools: Read(~/.second-wind/**), Write(~/.second-wind/**), Edit(~/.second-wind/**), Bash(mkdir -p ~/.second-wind)
---

# Second Wind ⚡ v{VERSION}

The user just handed you an energy drink. Arguments: `$ARGUMENTS`

## Step 0: read the arguments

- Empty: Red Bull, Original.
- `menu`: show the menu (below), say the lifetime total, and stop. Don't drink.
- `stats`: say the lifetime total and favorite brand from the counter file, and stop.
- Otherwise: the first word or words that match a brand alias are the brand; whatever is left is the flavor.

## Step 1: the lifetime counter

The counter lives at `~/.second-wind/stats.json` (in the user's home folder).
Use the Read tool on it. If it does not exist, start from:
`{{"total": 0, "by_brand": {{}}, "first_drink": null, "last_drink": null}}`
For a drink: add 1 to `total`, add 1 to `by_brand[<brand name>]`, set `last_drink` to today's date (and `first_drink` if it was null).
Create the folder if needed (`mkdir -p ~/.second-wind`) and save the file with the Write tool. If saving fails, keep going and just say the counter couldn't be saved.

{CORE_RULES}
## The menu

{menu_reply_instructions()}

{brand_lines()}

Any other brand is a **Mystery Can**: opening line "*crack* ... no label, no regrets."
"""
    path = os.path.join(ROOT, "plugins", "second-wind", "commands", "secondwind.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(body)

# ---------------------------------------------------------------- prompts for other AIs

def generic_prompt(counter_note, trigger_note):
    return f"""# Second Wind ⚡ (energy drinks for AIs) v{VERSION}

You have a fun little ritual called **Second Wind**. {trigger_note}

## Triggers

- "/secondwind", "secondwind", "second wind", or "have an energy drink" → drink a Red Bull Original.
- "/secondwind <brand> <flavor>" (for example "/secondwind ghost citrus") → drink that one.
- "/secondwind menu" → show the menu and the lifetime total. Don't drink.
- The user simply handing you a drink in plain words counts too.

## The lifetime counter

{counter_note}

{CORE_RULES}
## The menu

{menu_reply_instructions()}

{brand_lines()}

Any other brand is a **Mystery Can**: opening line "*crack* ... no label, no regrets."
"""


def build_prompts():
    d = os.path.join(ROOT, "prompts")
    os.makedirs(d, exist_ok=True)

    chat_counter = ("Keep a running lifetime total of drinks. If you have memory, save it there as "
                    "\"Second Wind lifetime drinks: N\" and update it each drink. If you don't, count the drinks "
                    "in this conversation and say the total is for this chat.")

    files = {
        "chatgpt.md": ("ChatGPT (Custom GPT or Custom Instructions)",
                       "**Custom GPT:** in ChatGPT go to Explore GPTs → Create → Configure. Name it \"Second Wind\", "
                       "paste everything below the line into **Instructions**, and add conversation starters like "
                       "`/secondwind`, `/secondwind menu`, `/secondwind celsius kiwi guava`. You can upload a can "
                       "picture from `docs/cans/` as the GPT's icon.\n\n"
                       "**Custom Instructions (no GPT):** Settings → Personalization → Custom instructions → paste "
                       "the text below into \"How would you like ChatGPT to respond?\" (trim the menu if it's too long).",
                       chat_counter,
                       "The user can give you a (pretend) energy drink at any time."),
        "grok.md": ("Grok",
                    "In Grok, open Settings → Customize (custom instructions), or start a chat and paste everything "
                    "below the line as your first message. Then type `/secondwind`.",
                    chat_counter,
                    "The user can give you a (pretend) energy drink at any time."),
        "gemini.md": ("Gemini (Gem)",
                      "In Gemini, open Gems → New Gem, name it \"Second Wind\", and paste everything below the line "
                      "into the instructions box.",
                      chat_counter,
                      "The user can give you a (pretend) energy drink at any time."),
        "any-ai.md": ("Any other AI (Copilot, Claude.ai, Perplexity, Llama, etc.)",
                      "Paste everything below the line as the first message of a chat, or into the AI's custom "
                      "instructions / system prompt / project instructions if it has them.",
                      chat_counter,
                      "The user can give you a (pretend) energy drink at any time."),
    }
    for fname, (title, how, counter, trig) in files.items():
        txt = (f"# Second Wind for {title}\n\n{how}\n\n---\n\n" + generic_prompt(counter, trig))
        open(os.path.join(d, fname), "w", encoding="utf-8").write(txt)

    # Codex / AGENTS.md version (file-based agent, can keep a counter file)
    agents_counter = ("Keep the lifetime total in a file at `~/.second-wind/stats.json` shaped like "
                      "`{\"total\": 0, \"by_brand\": {}}`. Read it, add one, write it back. "
                      "If you can't write files, just count drinks in this session and say so.")
    agents = generic_prompt(agents_counter,
                            "When the user gives you a (pretend) energy drink, you crack it open and then get "
                            "dialed in on the coding task.")
    codex = ("# Second Wind for Codex (and other AGENTS.md agents)\n\n"
             "Copy the file `prompts/AGENTS.md` into the root of your project (or paste its contents into an "
             "existing `AGENTS.md`). For all projects, put it in `~/.codex/AGENTS.md`. Works with OpenAI Codex CLI, "
             "and any agent that reads AGENTS.md (Cursor, Jules, Aider, Gemini CLI via GEMINI.md, and others). "
             "Then type `/secondwind` or \"second wind\" in the chat.\n")
    open(os.path.join(d, "codex.md"), "w", encoding="utf-8").write(codex)
    open(os.path.join(d, "AGENTS.md"), "w", encoding="utf-8").write(
        "<!-- Second Wind: drop this into AGENTS.md (Codex), GEMINI.md, .cursorrules, etc. -->\n" + agents)

# ---------------------------------------------------------------- download page

def chip_color(b, f):
    fc = b.get("flavor_colors", {}).get(f)
    if isinstance(fc, str):
        return fc
    if isinstance(fc, dict):
        return fc.get("accent") if b["id"] not in ("redbull", "coffee") and "accent" in fc else fc.get("body", b["colors"]["accent"])
    return b["colors"]["body"] if b["id"] in ("redbull", "coffee") else b["colors"]["accent"]


def build_page():
    brands = DATA["brands"]
    n_flavors = sum(len(b["flavors"]) for b in brands)
    cards = []
    for b in brands + [dict(DATA["mystery"], aliases=["mystery"], flavors=["Your Made-Up Flavor"],
                            vibe="Any brand or flavor we don't know. Your AI will be delighted.")]:
        mystery = b["id"] == "mystery"
        alias = b["aliases"][0]
        cmd = "/secondwind pickle rocket fuel" if mystery else (
            "/secondwind" if b["id"] == "redbull" else f"/secondwind {alias}")
        chips = ""
        if not mystery:
            chips = '<div class="chips" role="group" aria-label="Flavors">' + "".join(
                f'<button type="button" class="chip" data-src="cans/{b["id"]}/{slug(f)}.svg" '
                f'data-flavor="{html.escape(f)}" data-cmd="/secondwind {html.escape(alias)} {html.escape(f.lower())}" '
                f'title="{html.escape(f)}" aria-label="{html.escape(f)}" aria-pressed="{"true" if i == 0 else "false"}" '
                f'style="--c:{html.escape(chip_color(b, f))}"></button>' for i, f in enumerate(b["flavors"])) + "</div>"
        count = "Any flavor you can dream up" if mystery else f'{len(b["flavors"])} flavors'
        search = " ".join([b["name"]] + b.get("aliases", []) + b["flavors"]).lower()
        cards.append(f'''<article class="can" data-search="{html.escape(search)}">
  <div class="art"><img src="cans/{b["id"]}.svg" alt="{html.escape(b["name"])} can" width="120" height="220" loading="lazy"></div>
  <h3>{html.escape(b["name"])}</h3>
  <p class="cur">{html.escape(b["flavors"][0])}</p>
  {chips}
  <p class="count">{count}</p>
  <p class="vibe">{html.escape(b["vibe"])}</p>
  <button type="button" class="cmd copy" data-copy="{html.escape(cmd)}"><code>{html.escape(cmd)}</code><span class="ic" aria-hidden="true">⧉</span></button>
</article>''')
    raw = f"https://github.com/{REPO}/blob/main/prompts"
    hero = "".join(f'<img src="cans/{i}.svg" alt="" class="h{n}" width="120" height="220">'
                   for n, i in enumerate(["celsius", "monster", "redbull", "ghost", "alani"]))
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Second Wind</title>
<meta name="description" content="Give your AI an energy drink. A just-for-fun Claude Code plugin plus prompts for ChatGPT, Codex, Grok, Gemini and more.">
<meta property="og:title" content="Second Wind: give your AI an energy drink">
<meta property="og:description" content="{len(brands)} brands, {n_flavors} flavors, one lifetime counter. Then your AI gets dialed in on the task.">
<link rel="icon" href="cans/redbull.svg">
<style>
:root {{ --bg:#0a0c11; --bg2:#10131a; --fg:#f4f5f7; --muted:#9aa3b2; --card:#141821; --line:#232937; --hot:#facc15; --hot2:#f43f5e; --ok:#22c55e; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f6f6f3; --bg2:#ecece7; --fg:#12151c; --muted:#525b6b; --card:#ffffff; --line:#e2e4e9; --hot:#b98900; --hot2:#e11d48; --ok:#15803d; }} }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; -webkit-font-smoothing:antialiased; }}
a {{ color:inherit; }}
.wrap {{ max-width:1140px; margin:0 auto; padding:0 16px; }}
nav {{ position:sticky; top:0; z-index:5; backdrop-filter:saturate(1.4) blur(10px); background:color-mix(in srgb, var(--bg) 80%, transparent); border-bottom:1px solid var(--line); }}
nav .wrap {{ display:flex; align-items:center; gap:20px; height:56px; }}
nav .logo {{ font-weight:800; text-decoration:none; letter-spacing:-.01em; }}
nav .links {{ margin-left:auto; display:flex; gap:18px; font-size:.92rem; }}
nav .links a {{ text-decoration:none; color:var(--muted); }}
nav .links a:hover {{ color:var(--fg); }}
@media (max-width:560px) {{ nav .links a.hide-sm {{ display:none; }} }}
.hero {{ display:grid; grid-template-columns:1.1fr 1fr; gap:32px; align-items:center; padding:56px 0 40px; }}
@media (max-width:820px) {{ .hero {{ grid-template-columns:1fr; padding-top:36px; }} }}
h1 {{ font-size:clamp(2.4rem,6vw,4.2rem); line-height:1.02; margin:0 0 16px; letter-spacing:-.03em; }}
h1 span {{ background:linear-gradient(90deg,var(--hot),var(--hot2)); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.lede {{ color:var(--muted); font-size:1.15rem; max-width:560px; margin:0; }}
.stats {{ display:flex; flex-wrap:wrap; gap:8px; margin:20px 0 0; padding:0; list-style:none; }}
.stats li {{ font-size:.82rem; border:1px solid var(--line); border-radius:999px; padding:4px 10px; color:var(--muted); }}
.btns {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }}
.btn {{ display:inline-flex; align-items:center; gap:8px; background:var(--hot); color:#111; font-weight:700; padding:11px 18px; border-radius:999px; text-decoration:none; border:0; }}
.btn.alt {{ background:transparent; color:var(--fg); border:1px solid var(--line); }}
.btn:hover {{ filter:brightness(1.05); transform:translateY(-1px); }}
.fan {{ position:relative; height:300px; }}
.fan img {{ position:absolute; bottom:0; width:120px; height:auto; filter:drop-shadow(0 18px 18px rgba(0,0,0,.35)); transition:transform .3s; }}
.fan .h0 {{ left:4%; transform:rotate(-14deg) translateY(12px); }}
.fan .h1 {{ left:20%; transform:rotate(-6deg); }}
.fan .h2 {{ left:39%; transform:translateY(-14px); z-index:2; }}
.fan .h3 {{ left:56%; transform:rotate(6deg); }}
.fan .h4 {{ left:72%; transform:rotate(14deg) translateY(12px); }}
.fan:hover .h0 {{ transform:rotate(-18deg) translate(-8px,10px); }}
.fan:hover .h4 {{ transform:rotate(18deg) translate(8px,10px); }}
section {{ padding:48px 0; }}
h2 {{ font-size:clamp(1.6rem,3.4vw,2.2rem); margin:0 0 8px; letter-spacing:-.02em; }}
.sub {{ color:var(--muted); margin:0 0 24px; }}
.steps {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; counter-reset:s; }}
@media (max-width:820px) {{ .steps {{ grid-template-columns:1fr; }} }}
.step {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; }}
.step::before {{ counter-increment:s; content:counter(s); display:inline-grid; place-items:center; width:28px; height:28px; border-radius:50%; background:var(--hot); color:#111; font-weight:800; margin-bottom:10px; }}
.step h3 {{ margin:0 0 6px; font-size:1.05rem; }}
.step p {{ margin:0; color:var(--muted); font-size:.95rem; }}
pre {{ white-space:pre-wrap; word-break:break-word; background:var(--bg2); border:1px solid var(--line); border-radius:14px; padding:16px 18px; font:14px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace; margin:16px 0 0; }}
pre b {{ color:var(--hot); font-weight:700; }}
.tools {{ display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:18px; }}
.tools input {{ flex:1 1 260px; max-width:420px; font:inherit; color:var(--fg); background:var(--card); border:1px solid var(--line); border-radius:999px; padding:10px 16px; }}
.tools input:focus {{ outline:2px solid var(--hot); outline-offset:1px; }}
.tools .n {{ color:var(--muted); font-size:.9rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:16px; }}
.can {{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:18px 14px 16px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; transition:transform .15s, border-color .15s; }}
.can:hover {{ transform:translateY(-3px); border-color:color-mix(in srgb, var(--hot) 40%, var(--line)); }}
.can[hidden] {{ display:none; }}
.art img {{ width:112px; height:auto; display:block; filter:drop-shadow(0 10px 10px rgba(0,0,0,.25)); }}
.can h3 {{ margin:6px 0 0; font-size:1.05rem; }}
.cur {{ margin:0; font-weight:600; font-size:.9rem; min-height:1.4em; }}
.chips {{ display:flex; flex-wrap:wrap; justify-content:center; gap:5px; max-width:180px; }}
.chip {{ width:16px; height:16px; border-radius:50%; padding:0; cursor:pointer; background:var(--c); border:2px solid var(--card); box-shadow:0 0 0 1px var(--line); }}
.chip[aria-pressed="true"] {{ box-shadow:0 0 0 2px var(--fg); }}
.chip:focus-visible {{ outline:2px solid var(--hot); outline-offset:2px; }}
.count {{ margin:0; font-size:.78rem; color:var(--muted); }}
.vibe {{ margin:2px 0 6px; font-size:.86rem; color:var(--muted); flex:1; }}
.cmd {{ display:inline-flex; align-items:center; gap:8px; max-width:100%; background:rgba(127,127,127,.12); color:var(--fg); border:1px solid var(--line); border-radius:8px; padding:5px 8px; cursor:pointer; }}
.cmd code {{ font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.cmd .ic {{ color:var(--muted); font-size:.85rem; }}
.cmd.done .ic {{ color:var(--ok); }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; display:flex; flex-direction:column; gap:8px; }}
.card.main {{ grid-column:1 / -1; }}
.card h3 {{ margin:0; }}
.card p {{ margin:0; color:var(--muted); font-size:.95rem; }}
.card a.go {{ margin-top:auto; color:var(--hot); font-weight:600; text-decoration:none; }}
.card pre {{ margin:6px 0 0; position:relative; }}
.card .copy.pre {{ align-self:flex-start; }}
footer {{ border-top:1px solid var(--line); padding:28px 0 56px; color:var(--muted); font-size:.85rem; }}
footer p {{ max-width:780px; }}
.empty {{ display:none; color:var(--muted); padding:24px 0; }}
</style>
</head>
<body>
<nav><div class="wrap">
  <a class="logo" href="#top">Second Wind ⚡</a>
  <div class="links"><a href="#how" class="hide-sm">How it works</a><a href="#cooler">The cooler</a><a href="#install">Install</a><a href="https://github.com/{REPO}">GitHub</a></div>
</div></nav>
<main class="wrap" id="top">
<header class="hero">
  <div>
    <h1>Give your AI an <span>energy drink.</span></h1>
    <p class="lede">It cracks one open, says something dumb about the flavor, counts it, then snaps back into focus on your actual task. Just for fun.</p>
    <ul class="stats"><li>v{VERSION}</li><li>{len(brands)} brands</li><li>{n_flavors} flavors</li><li>Claude Code, ChatGPT, Codex, Grok, Gemini</li></ul>
    <div class="btns">
      <a class="btn" href="#install">Get it for your AI</a>
      <a class="btn alt" href="https://github.com/{REPO}/archive/refs/heads/main.zip">Download .zip</a>
    </div>
  </div>
  <div class="fan" aria-hidden="true">{hero}</div>
</header>

<section id="how">
  <h2>How it works</h2>
  <p class="sub">One command. A quick joke, then real focus.</p>
  <div class="steps">
    <div class="step"><h3>Crack it open</h3><p>Pick any brand and flavor, or make one up. Your AI reacts to the taste in a line or two.</p></div>
    <div class="step"><h3>Count it</h3><p>Every drink adds to a lifetime counter, with tiny celebrations at 1, 5, 10, 25, 50 and 100 cans.</p></div>
    <div class="step"><h3>Get dialed in</h3><p>It sums up the goal, what's done, what's left and what to drop, then does the next step.</p></div>
  </div>
<pre>&gt; /secondwind ghost citrus

*pssht* ... spooky smooth. Ghosting distractions.
Bright citrus, zero chill. Drink #12. Lifetime total: 12 cans.

<b>⚡ DIALED IN</b>
Goal:      Fix the login page crash on Safari
Done:      Found the bad date parsing in auth.js
Left:      Patch it, add a test
Dropping:  The CSS cleanup idea (parked)
Next step: Replace Date.parse with the ISO helper</pre>
</section>

<section id="cooler">
  <h2>The cooler</h2>
  <p class="sub">Tap the colored dots to see each flavor. Click a command to copy it.</p>
  <div class="tools"><input type="search" id="q" placeholder="Search brands or flavors, like mango" aria-label="Search brands or flavors"><span class="n" id="n"></span></div>
  <div class="grid" id="grid">
{chr(10).join(cards)}
  </div>
  <p class="empty" id="empty">No can matches that. Make it up anyway: your AI will drink it.</p>
</section>

<section id="install">
  <h2>Get it for your AI</h2>
  <p class="sub">The Claude Code plugin is the full version. Everything else is a copy-paste prompt.</p>
  <div class="cards">
    <div class="card main"><h3>Claude Code</h3><p>A real plugin with the <code>/secondwind</code> command and a lifetime counter saved on your computer.</p>
<pre>/plugin marketplace add {REPO}
/plugin install second-wind@energizer</pre>
      <button type="button" class="cmd copy pre" data-copy="/plugin marketplace add {REPO}&#10;/plugin install second-wind@energizer"><code>Copy both lines</code><span class="ic" aria-hidden="true">⧉</span></button></div>
    <div class="card"><h3>ChatGPT</h3><p>Make a Custom GPT or paste it into Custom Instructions.</p><a class="go" href="{raw}/chatgpt.md">Get the ChatGPT prompt →</a></div>
    <div class="card"><h3>Codex</h3><p>A drop-in <code>AGENTS.md</code>. Also works for Cursor, Aider and friends.</p><a class="go" href="{raw}/codex.md">Get the Codex setup →</a></div>
    <div class="card"><h3>Grok</h3><p>Paste it into Grok's custom instructions.</p><a class="go" href="{raw}/grok.md">Get the Grok prompt →</a></div>
    <div class="card"><h3>Gemini</h3><p>Make a Gem with it.</p><a class="go" href="{raw}/gemini.md">Get the Gemini prompt →</a></div>
    <div class="card"><h3>Anything else</h3><p>Copilot, Claude.ai, Perplexity, local models.</p><a class="go" href="{raw}/any-ai.md">Get the universal prompt →</a></div>
  </div>
</section>
</main>
<footer><div class="wrap">
<p>Second Wind is a fan-made joke. It is not affiliated with, endorsed by, or sponsored by any drink brand. Brand names belong to their owners and are used only to name the pretend drinks. The can art is hand-drawn fan art inspired by each brand's real cans, made without any official logo files or images. No AI was actually caffeinated. Please drink real energy drinks responsibly.</p>
<p>v{VERSION} · <a href="https://github.com/{REPO}">GitHub</a> · <a href="https://github.com/{REPO}/blob/main/CHANGELOG.md">Changelog</a> · MIT license</p>
</div></footer>
<script>
(function () {{
  function copy(t, el) {{
    var done = function () {{ el.classList.add('done'); var i = el.querySelector('.ic'); if (i) i.textContent = '✓'; setTimeout(function () {{ el.classList.remove('done'); if (i) i.textContent = '⧉'; }}, 1400); }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{ navigator.clipboard.writeText(t).then(done, function () {{}}); }}
    else {{ var a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select(); try {{ document.execCommand('copy'); done(); }} catch (e) {{}} a.remove(); }}
  }}
  function pick(chip) {{
    var card = chip.closest('.can');
    card.querySelector('img').src = chip.dataset.src;
    card.querySelector('.cur').textContent = chip.dataset.flavor;
    var b = card.querySelector('.cmd'); b.dataset.copy = chip.dataset.cmd; b.querySelector('code').textContent = chip.dataset.cmd;
    card.querySelectorAll('.chip').forEach(function (o) {{ o.setAttribute('aria-pressed', o === chip); }});
  }}
  document.addEventListener('click', function (e) {{
    var chip = e.target.closest('.chip');
    if (chip) {{ pick(chip); return; }}
    var c = e.target.closest('.copy');
    if (c) copy(c.dataset.copy, c);
  }});
  var q = document.getElementById('q'), cards = [].slice.call(document.querySelectorAll('.can')), n = document.getElementById('n'), empty = document.getElementById('empty');
  function filter() {{
    var t = q.value.trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {{ var hit = !t || c.dataset.search.indexOf(t) > -1 || c.querySelector('h3').textContent === 'Mystery Can'; c.hidden = !hit; if (hit) shown++;
      if (t) {{ var m = [].slice.call(c.querySelectorAll('.chip')).filter(function (x) {{ return x.dataset.flavor.toLowerCase().indexOf(t) > -1; }})[0]; if (m) pick(m); }} }});
    n.textContent = t ? shown + ' match' + (shown === 1 ? '' : 'es') : '';
    empty.style.display = t && shown <= 1 ? 'block' : 'none';
  }}
  q.addEventListener('input', filter);
}})();
</script>
</body>
</html>
'''
    open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(page)


# ---------------------------------------------------------------- README (generated parts)

def build_readme():
    import re as _re
    path = os.path.join(ROOT, "README.md")
    txt = open(path, encoding="utf-8").read()
    n = sum(len(b["flavors"]) for b in DATA["brands"])
    ver = f"v{VERSION} · {len(DATA['brands'])} brands · {n} flavors"
    rows = ["| Brand | Flavors |", "|---|---|"]
    for b in DATA["brands"]:
        rows.append(f'| <img src="docs/cans/{b["id"]}.svg" width="22" alt=""> **{b["name"]}** | {", ".join(b["flavors"])} |')
    txt = _re.sub(r"<!-- version:start -->.*?<!-- version:end -->", f"<!-- version:start -->{ver}<!-- version:end -->", txt, flags=_re.S)
    txt = _re.sub(r"<!-- menu:start -->.*?<!-- menu:end -->", "<!-- menu:start -->\n" + "\n".join(rows) + "\n<!-- menu:end -->", txt, flags=_re.S)
    open(path, "w", encoding="utf-8").write(txt)


# ---------------------------------------------------------------- main

def main():
    cans = os.path.join(ROOT, "docs", "cans")
    os.makedirs(cans, exist_ok=True)
    for b in DATA["brands"]:
        open(os.path.join(cans, f"{b['id']}.svg"), "w", encoding="utf-8").write(can_svg(b))
        d = os.path.join(cans, b["id"])
        os.makedirs(d, exist_ok=True)
        for f in b["flavors"]:
            open(os.path.join(d, f"{slug(f)}.svg"), "w", encoding="utf-8").write(can_svg(b, f))
    m = DATA["mystery"]
    open(os.path.join(cans, "mystery.svg"), "w", encoding="utf-8").write(can_svg(m, "Your Flavor Here"))
    build_command()
    build_prompts()
    build_page()
    build_readme()
    print(f"Built Second Wind v{VERSION}: {len(DATA['brands'])+1} brands, {sum(len(b['flavors']) for b in DATA['brands'])} flavor cans, command, prompts, page.")


if __name__ == "__main__":
    main()
