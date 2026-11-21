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
    cans_html = []
    for b in DATA["brands"] + [dict(DATA["mystery"], flavors=["Your Made-Up Flavor"], vibe="Any brand or flavor we don't know. Claude will be delighted.")]:
        flv = ", ".join(b["flavors"])
        cmd = "/secondwind" if b["id"] == "redbull" else (
            "/secondwind pickle-flavored rocket fuel" if b["id"] == "mystery" else f"/secondwind {b['aliases'][0]}")
        chips = ""
        if b["id"] != "mystery":
            chips = '<div class="chips">' + "".join(
                f'<button type="button" class="chip" data-src="cans/{b["id"]}/{slug(f)}.svg" '
                f'title="{html.escape(f)}" aria-label="Show {html.escape(f)}" '
                f'style="background:{html.escape(chip_color(b, f))}"></button>' for f in b["flavors"]) + "</div>"
        cans_html.append(f'''<figure class="can">
  <div class="art"><img src="cans/{b["id"]}.svg" alt="{html.escape(b["name"])} can" width="120" height="220" loading="lazy"></div>
  <figcaption><strong>{html.escape(b["name"])}</strong>
  <span class="cur">{html.escape(b["flavors"][0])}</span>
  {chips}
  <span class="vibe">{html.escape(b["vibe"])}</span>
  <span class="flv">{html.escape(flv)}</span>
  <code>{html.escape(cmd)}</code></figcaption>
</figure>''')
    raw = f"https://github.com/{REPO}/blob/main/prompts"
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Second Wind</title>
<meta name="description" content="Give your AI an energy drink. A just-for-fun Claude Code plugin plus prompts for ChatGPT, Codex, Grok and more.">
<link rel="icon" href="cans/redbull.svg">
<style>
:root {{ --bg:#0b0d12; --fg:#f3f4f6; --muted:#9ca3af; --card:#151922; --line:#262c38; --hot:#facc15; --hot2:#f43f5e; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f7f7f5; --fg:#111827; --muted:#4b5563; --card:#ffffff; --line:#e5e7eb; --hot:#ca8a04; --hot2:#e11d48; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:40px 16px 80px; }}
h1 {{ font-size:clamp(2.2rem,6vw,3.8rem); margin:0; letter-spacing:-0.02em; }}
h1 span {{ background:linear-gradient(90deg,var(--hot),var(--hot2)); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.lede {{ color:var(--muted); font-size:1.15rem; max-width:640px; }}
h2 {{ margin-top:56px; font-size:1.5rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:16px; margin-top:20px; }}
.can {{ margin:0; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 12px; text-align:center; transition:transform .15s; }}
.can:hover {{ transform:translateY(-4px) rotate(-1deg); }}
.art img {{ width:110px; height:auto; display:block; margin:0 auto; }}
.cur {{ font-size:.85rem; font-weight:600; }}
.chips {{ display:flex; flex-wrap:wrap; justify-content:center; gap:5px; }}
.chip {{ width:16px; height:16px; border-radius:50%; border:2px solid var(--line); padding:0; cursor:pointer; }}
.chip[aria-pressed="true"] {{ border-color:var(--fg); }}
figcaption {{ display:flex; flex-direction:column; gap:6px; margin-top:8px; }}
.vibe {{ font-size:.85rem; color:var(--muted); }}
.flv {{ font-size:.75rem; color:var(--muted); opacity:.85; }}
code {{ font:13px ui-monospace,SFMono-Regular,Menlo,monospace; background:rgba(127,127,127,.15); padding:3px 6px; border-radius:6px; word-break:break-word; }}
pre {{ white-space:pre-wrap; word-break:break-word; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; overflow-x:auto; font:14px ui-monospace,Menlo,monospace; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px; }}
.card h3 {{ margin:0 0 6px; }}
.card p {{ margin:0 0 10px; color:var(--muted); font-size:.95rem; }}
a {{ color:var(--hot); }}
.btn {{ display:inline-block; background:var(--hot); color:#111; font-weight:700; padding:10px 18px; border-radius:999px; text-decoration:none; margin:16px 8px 0 0; }}
.btn.alt {{ background:transparent; color:var(--fg); border:1px solid var(--line); }}
footer {{ margin-top:64px; color:var(--muted); font-size:.85rem; border-top:1px solid var(--line); padding-top:20px; }}
</style>
</head>
<body>
<main>
<h1>Second <span>Wind</span> ⚡</h1>
<p class="lede">Give your AI an energy drink. It cracks one open, says something dumb about the flavor, then snaps back into focus: goal, done, left, next step, go. Just for fun. v{VERSION}</p>
<a class="btn" href="https://github.com/{REPO}/archive/refs/heads/main.zip">Download everything (.zip)</a>
<a class="btn alt" href="https://github.com/{REPO}">View on GitHub</a>

<h2>The cooler</h2>
<p class="lede">Tap the dots under a can to see each flavor. Ask for any brand and flavor. Make one up and watch your AI get excited about it.</p>
<div class="grid">
{chr(10).join(cans_html)}
</div>
<script>
document.querySelectorAll('.chip').forEach(function (c) {{
  c.addEventListener('click', function () {{
    var fig = c.closest('.can');
    fig.querySelector('img').src = c.dataset.src;
    fig.querySelector('.cur').textContent = c.title;
    fig.querySelectorAll('.chip').forEach(function (o) {{ o.setAttribute('aria-pressed', o === c); }});
  }});
}});
</script>

<h2>Get it for your AI</h2>
<div class="cards">
  <div class="card"><h3>Claude Code</h3><p>Real plugin with a <code>/secondwind</code> command and a lifetime counter.</p>
<pre>/plugin marketplace add {REPO}
/plugin install second-wind@energizer</pre></div>
  <div class="card"><h3>ChatGPT</h3><p>Make a Custom GPT or paste into Custom Instructions.</p><a href="{raw}/chatgpt.md">Get the ChatGPT prompt</a></div>
  <div class="card"><h3>Codex</h3><p>Drop-in <code>AGENTS.md</code>. Also works for Cursor, Aider and friends.</p><a href="{raw}/codex.md">Get the Codex setup</a></div>
  <div class="card"><h3>Grok</h3><p>Paste into Grok's custom instructions.</p><a href="{raw}/grok.md">Get the Grok prompt</a></div>
  <div class="card"><h3>Gemini</h3><p>Make a Gem with it.</p><a href="{raw}/gemini.md">Get the Gemini prompt</a></div>
  <div class="card"><h3>Anything else</h3><p>Copilot, Claude.ai, Perplexity, local models.</p><a href="{raw}/any-ai.md">Get the universal prompt</a></div>
</div>

<h2>What a drink looks like</h2>
<pre>&gt; /secondwind ghost citrus

*pssht* ... spooky smooth. Ghosting distractions.
Bright citrus, zero chill. Drink #12. Lifetime total: 12 cans.

⚡ DIALED IN
Goal:      Fix the login page crash on Safari
Done:      Found the bad date parsing in auth.js
Left:      Patch it, add a test
Dropping:  The CSS cleanup idea (parked)
Next step: Replace Date.parse with the ISO helper</pre>

<footer>Second Wind is a fan-made joke. It is not affiliated with, endorsed by, or sponsored by any drink brand. All brand names belong to their owners and are used only to name the pretend drinks. The can art is hand-drawn fan art inspired by each brand's real cans, made without any official logo files or images. The drinks are pretend: no AI was actually caffeinated. Please drink real energy drinks responsibly.</footer>
</main>
</body>
</html>
'''
    open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(page)

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
    print(f"Built Second Wind v{VERSION}: {len(DATA['brands'])+1} brands, {sum(len(b['flavors']) for b in DATA['brands'])} flavor cans, command, prompts, page.")


if __name__ == "__main__":
    main()
