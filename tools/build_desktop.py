#!/usr/bin/env python3
"""Build the Second Wind desktop app (Windows tray app) and the Claude Desktop skill.

Writes:
  - desktop/data.json, desktop/cans/*.png, desktop/icon.ico
  - docs/downloads/second-wind-desktop.zip   (the Windows tray app)
  - docs/downloads/second-wind-skill.zip     (skill for the Claude Desktop app / claude.ai)

Hand-written files: desktop/SecondWind.ps1, desktop/Start Second Wind.bat, desktop/README.txt.
PNG rendering needs Node + Playwright (only redraws cans whose SVG changed).
"""
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_extension  # noqa: E402  (reuses brand data + icon)

DESK = os.path.join(ROOT, "desktop")
DL = os.path.join(ROOT, "docs", "downloads")
VERSION = build_extension.VERSION


def data_json():
    js = build_extension.data_js()
    payload = json.loads(js.split("window.SECOND_WIND = ", 1)[1].rstrip().rstrip(";"))
    json.dump(payload, open(os.path.join(DESK, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def pngs():
    subprocess.run(["node", os.path.join(ROOT, "tools", "render_pngs.js"),
                    os.path.join(ROOT, "docs", "cans"), os.path.join(DESK, "cans"), "160"], check=True)


def icon():
    from PIL import Image
    src = os.path.join(ROOT, "extension", "icons", "icon128.png")
    Image.open(src).save(os.path.join(DESK, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)])


def stamp(name, rel):
    info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def zip_desktop():
    out = os.path.join(DL, "second-wind-desktop.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(DESK):
            for f in sorted(files):
                p = os.path.join(base, f)
                rel = os.path.relpath(p, DESK).replace(os.sep, "/")
                data = open(p, "rb").read()
                if f.endswith(".bat") or f.endswith(".txt"):
                    data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")  # Windows line endings
                z.writestr(stamp("Second Wind/" + rel, rel), data)
    return out


def zip_skill():
    """A skill for the Claude Desktop app / claude.ai (Settings > Capabilities > Skills > Upload)."""
    import build
    body = build.generic_prompt(
        "Keep a running lifetime total of drinks. If you have memory, save it there as \"Second Wind lifetime drinks: N\" "
        "and update it each drink. If you don't, count the drinks in this conversation and say the total is for this chat.",
        "The user can give you a (pretend) energy drink at any time.")
    skill = ("---\n"
             "name: second-wind\n"
             "description: Give Claude a pretend energy drink. Use when the user types /secondwind, says \"second wind\", "
             "hands Claude an energy drink, or pastes a Second Wind drink message. Claude cracks it open, counts it, "
             "then prints a DIALED IN focus block and gets back to the real task.\n"
             "---\n\n" + body)
    out = os.path.join(DL, "second-wind-skill.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(stamp("second-wind/SKILL.md", ""), skill.encode("utf-8"))
    return out


def main():
    os.makedirs(DESK, exist_ok=True)
    os.makedirs(DL, exist_ok=True)
    data_json()
    pngs()
    icon()
    a = zip_desktop()
    b = zip_skill()
    print(f"Built desktop app v{VERSION}: {os.path.relpath(a, ROOT)} ({os.path.getsize(a)//1024} KB), "
          f"{os.path.relpath(b, ROOT)} ({os.path.getsize(b)//1024} KB)")


if __name__ == "__main__":
    main()
