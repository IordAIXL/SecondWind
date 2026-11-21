#!/usr/bin/env python3
"""Second Wind build script.

Reads data/brands.json and regenerates:
  - docs/cans/<id>.svg            one original can illustration per brand
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

def motif_svg(m, c):
    a, b, t = c["accent"], c["accent2"], c["text"]
    if m == "sun":
        rays = "".join(
            f'<rect x="58" y="88" width="4" height="14" fill="{b}" transform="rotate({i*30} 60 128)"/>'
            for i in range(12))
        return rays + f'<circle cx="60" cy="128" r="17" fill="{b}"/><circle cx="60" cy="128" r="11" fill="{a}"/>'
    if m == "scratch":
        return "".join(
            f'<path d="M{40+i*14} 95 C{36+i*14} 125,{46+i*14} 140,{38+i*14} 168" stroke="{a}" '
            f'stroke-width="7" fill="none" stroke-linecap="round"/>' for i in range(3))
    if m == "thermo":
        return (f'<rect x="54" y="90" width="12" height="62" rx="6" fill="none" stroke="{t}" stroke-width="3"/>'
                f'<rect x="57" y="112" width="6" height="40" fill="{a}"/>'
                f'<circle cx="60" cy="158" r="11" fill="{a}" stroke="{t}" stroke-width="3"/>'
                f'<path d="M28 100 q8 -8 16 0 t16 0" stroke="{b}" stroke-width="3" fill="none"/>'
                f'<path d="M64 170 q8 -8 16 0 t16 0" stroke="{b}" stroke-width="3" fill="none"/>')
    if m == "chevrons":
        return "".join(
            f'<path d="M34 {160-i*20} L60 {140-i*20} L86 {160-i*20}" stroke="{a if i%2==0 else b}" '
            f'stroke-width="8" fill="none" stroke-linejoin="round"/>' for i in range(4))
    if m == "ghost":
        return (f'<path d="M40 165 V122 a20 20 0 0 1 40 0 V165 l-7 -7 -6 7 -7 -7 -7 7 -6 -7 z" fill="{t}"/>'
                f'<circle cx="52" cy="124" r="4" fill="{b}"/><circle cx="68" cy="124" r="4" fill="{b}"/>'
                f'<ellipse cx="60" cy="140" rx="5" ry="7" fill="{b}"/>')
    if m == "burst":
        pts = []
        import math
        for i in range(16):
            r = 34 if i % 2 == 0 else 16
            ang = math.pi * 2 * i / 16
            pts.append(f"{60+r*math.cos(ang):.1f},{128+r*math.sin(ang):.1f}")
        return (f'<polygon points="{" ".join(pts)}" fill="{a}"/>'
                f'<circle cx="60" cy="128" r="10" fill="{b}"/>')
    if m == "crown":
        return (f'<path d="M34 150 L34 110 L47 128 L60 102 L73 128 L86 110 L86 150 Z" fill="{a}"/>'
                f'<rect x="34" y="150" width="52" height="8" fill="{a}"/>'
                f'<circle cx="60" cy="138" r="5" fill="{b}"/><circle cx="45" cy="142" r="3" fill="{b}"/>'
                f'<circle cx="75" cy="142" r="3" fill="{b}"/>')
    if m == "hazard":
        stripes = "".join(
            f'<polygon points="{18+i*16},180 {26+i*16},180 {42+i*16},164 {34+i*16},164" fill="{a}"/>'
            for i in range(6))
        return (f'<polygon points="60,96 88,148 32,148" fill="{a}"/>'
                f'<polygon points="60,108 79,142 41,142" fill="{c["body"]}"/>'
                f'<rect x="57" y="116" width="6" height="16" fill="{b}"/><circle cx="60" cy="137" r="3" fill="{b}"/>'
                + stripes)
    if m == "hearts":
        def heart(x, y, s, col):
            return (f'<path transform="translate({x} {y}) scale({s})" d="M0 6 C0 -2 12 -2 12 6 '
                    f'C12 -2 24 -2 24 6 C24 14 12 20 12 24 C12 20 0 14 0 6 Z" fill="{col}"/>')
        return heart(38, 112, 1.8, a) + heart(26, 96, 0.8, b) + heart(78, 150, 0.9, b) + heart(80, 98, 0.6, a)
    if m == "diamond":
        return (f'<polygon points="60,96 86,122 60,162 34,122" fill="{a}"/>'
                f'<polygon points="60,96 72,122 60,162 48,122" fill="{b}" opacity="0.9"/>'
                f'<line x1="34" y1="122" x2="86" y2="122" stroke="{t}" stroke-width="2"/>'
                f'<path d="M24 100 l4 -8 l4 8 l-4 8 z M90 150 l3 -6 l3 6 l-3 6 z" fill="{t}"/>')
    if m == "prism":
        return (f'<polygon points="60,98 84,152 36,152" fill="none" stroke="{t}" stroke-width="3"/>'
                f'<line x1="18" y1="128" x2="48" y2="126" stroke="{t}" stroke-width="3"/>'
                f'<polygon points="70,124 104,112 104,120" fill="{a}"/>'
                f'<polygon points="70,126 104,122 104,130" fill="{b}"/>'
                f'<polygon points="70,128 104,132 104,140" fill="#facc15"/>')
    if m == "stars":
        def star(x, y, r, col):
            import math
            p = []
            for i in range(10):
                rr = r if i % 2 == 0 else r * 0.45
                ang = -math.pi / 2 + math.pi * i / 5
                p.append(f"{x+rr*math.cos(ang):.1f},{y+rr*math.sin(ang):.1f}")
            return f'<polygon points="{" ".join(p)}" fill="{col}"/>'
        return star(60, 128, 24, a) + star(32, 100, 9, b) + star(88, 160, 10, b) + star(86, 100, 6, a)
    if m == "cube":
        return (f'<polygon points="60,98 88,112 60,126 32,112" fill="{a}"/>'
                f'<polygon points="32,112 60,126 60,158 32,144" fill="{b}"/>'
                f'<polygon points="88,112 60,126 60,158 88,144" fill="{t}" opacity="0.85"/>')
    if m == "antlers":
        side = lambda s: (f'<path d="M60 150 C{60+s*4} 130,{60+s*20} 118,{60+s*30} 98 '
                          f'M{60+s*14} 128 L{60+s*30} 120 M{60+s*22} 112 L{60+s*20} 96" '
                          f'stroke="{a}" stroke-width="5" fill="none" stroke-linecap="round"/>')
        return side(1) + side(-1) + f'<ellipse cx="60" cy="158" rx="10" ry="13" fill="{b}"/>'
    if m == "waves":
        return "".join(
            f'<path d="M14 {118+i*16} q11.5 -10 23 0 t23 0 t23 0 t23 0" stroke="{a if i%2==0 else b}" '
            f'stroke-width="5" fill="none"/>' for i in range(4)) + f'<circle cx="80" cy="98" r="10" fill="{b}"/>'
    if m == "beans":
        def bean(x, y, rot):
            return (f'<g transform="rotate({rot} {x} {y})"><ellipse cx="{x}" cy="{y}" rx="11" ry="16" fill="{a}"/>'
                    f'<path d="M{x} {y-14} q-6 14 0 28" stroke="{b}" stroke-width="3" fill="none"/></g>')
        return (bean(48, 120, -20) + bean(72, 138, 25) +
                f'<path d="M50 100 q-6 -8 0 -14 M60 100 q-6 -8 0 -14 M70 100 q-6 -8 0 -14" stroke="{t}" '
                f'stroke-width="2.5" fill="none" opacity="0.8"/>')
    if m == "leaves":
        def leaf(x, y, rot, col):
            return (f'<g transform="rotate({rot} {x} {y})"><path d="M{x} {y-22} q16 22 0 44 q-16 -22 0 -44 z" '
                    f'fill="{col}"/><line x1="{x}" y1="{y-18}" x2="{x}" y2="{y+20}" stroke="{c["body"]}" '
                    f'stroke-width="2"/></g>')
        return leaf(48, 130, -30, a) + leaf(72, 128, 30, a) + leaf(60, 112, 0, b)
    if m == "question":
        return (f'<circle cx="60" cy="128" r="30" fill="{a}"/>'
                f'<text x="60" y="144" font-family="Georgia,serif" font-size="46" font-weight="700" '
                f'text-anchor="middle" fill="{c["body"]}">?</text>'
                f'<circle cx="28" cy="98" r="4" fill="{b}"/><circle cx="92" cy="164" r="5" fill="{b}"/>'
                f'<circle cx="94" cy="100" r="3" fill="{b}"/>')
    return ""


def can_svg(brand, flavor=None):
    c = brand["colors"]
    bid = brand["id"]
    name = html.escape(brand["name"].upper())
    fs = 15 if len(name) <= 7 else (12 if len(name) <= 10 else 10)
    flav = html.escape(flavor or brand.get("flavors", ["?"])[0])
    ffs = 8 if len(flav) <= 16 else 6.5
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 220" width="120" height="220" role="img" aria-label="{html.escape(brand['name'])} can, original Second Wind art">
  <defs>
    <linearGradient id="shade-{bid}" x1="0" x2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0.35"/>
      <stop offset="0.25" stop-color="#fff" stop-opacity="0.18"/>
      <stop offset="0.45" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.4"/>
    </linearGradient>
    <linearGradient id="metal-{bid}" x1="0" x2="1">
      <stop offset="0" stop-color="#8a8f98"/><stop offset="0.3" stop-color="#eef0f3"/>
      <stop offset="0.7" stop-color="#b7bcc4"/><stop offset="1" stop-color="#6b7079"/>
    </linearGradient>
    <clipPath id="body-{bid}"><rect x="14" y="30" width="92" height="166" rx="6"/></clipPath>
  </defs>
  <ellipse cx="60" cy="212" rx="44" ry="5" fill="#000" opacity="0.18"/>
  <path d="M20 22 Q20 14 30 12 L90 12 Q100 14 100 22 L106 32 L14 32 Z" fill="url(#metal-{bid})"/>
  <ellipse cx="60" cy="13" rx="31" ry="5" fill="#d9dce1" stroke="#9aa0a8" stroke-width="1"/>
  <ellipse cx="66" cy="13" rx="9" ry="2.6" fill="#a3a9b1"/>
  <g clip-path="url(#body-{bid})">
    <rect x="14" y="30" width="92" height="166" fill="{c['body']}"/>
    <rect x="14" y="40" width="92" height="30" fill="{c['band']}"/>
    <text x="60" y="{60 if fs>=12 else 59}" font-family="'Arial Black','Helvetica Neue',Arial,sans-serif" font-size="{fs}" font-weight="900" text-anchor="middle" fill="{c['text'] if c['band']!=c['text'] else c['body']}" letter-spacing="0.5">{name}</text>
    {motif_svg(brand['motif'], c)}
    <rect x="14" y="174" width="92" height="14" fill="{c['band']}" opacity="0.9"/>
    <text x="60" y="184" font-family="Arial,Helvetica,sans-serif" font-size="{ffs}" font-weight="700" text-anchor="middle" fill="{c['text'] if c['band']!=c['text'] else c['body']}">{flav}</text>
    <text x="60" y="80" font-family="Arial,Helvetica,sans-serif" font-size="5.5" text-anchor="middle" fill="{c['text']}" opacity="0.75" letter-spacing="1.5">SECOND WIND · FOR AIs</text>
    <rect x="14" y="30" width="92" height="166" fill="url(#shade-{bid})"/>
  </g>
  <path d="M14 194 L18 204 Q20 208 30 208 L90 208 Q100 208 102 204 L106 194 Z" fill="url(#metal-{bid})"/>
</svg>
'''

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

def build_page():
    cans_html = []
    for b in DATA["brands"] + [dict(DATA["mystery"], flavors=["Your Made-Up Flavor"], vibe="Any brand or flavor we don't know. Claude will be delighted.")]:
        svg = open(os.path.join(ROOT, "docs", "cans", f"{b['id']}.svg"), encoding="utf-8").read()
        flv = ", ".join(b["flavors"])
        cmd = "/secondwind" if b["id"] == "redbull" else (
            "/secondwind pickle-flavored rocket fuel" if b["id"] == "mystery" else f"/secondwind {b['aliases'][0]}")
        cans_html.append(f'''<figure class="can">
  <div class="art">{svg}</div>
  <figcaption><strong>{html.escape(b["name"])}</strong>
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
.art svg {{ width:100px; height:auto; }}
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
<p class="lede">Every can is original art. Ask for any brand and flavor. Make one up and watch your AI get excited about it.</p>
<div class="grid">
{chr(10).join(cans_html)}
</div>

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

<footer>Second Wind is a fan-made joke. It is not affiliated with, endorsed by, or sponsored by any drink brand. All brand names belong to their owners and are used only to name the pretend drinks. The can art is original and doesn't copy any real logo or can design. The drinks are pretend: no AI was actually caffeinated. Please drink real energy drinks responsibly.</footer>
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
    m = DATA["mystery"]
    open(os.path.join(cans, "mystery.svg"), "w", encoding="utf-8").write(can_svg(m, "???"))
    build_command()
    build_prompts()
    build_page()
    print(f"Built Second Wind v{VERSION}: {len(DATA['brands'])+1} cans, command, prompts, page.")


if __name__ == "__main__":
    main()
