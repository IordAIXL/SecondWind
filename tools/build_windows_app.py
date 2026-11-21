#!/usr/bin/env python3
"""Prepare the Second Wind Windows app (Microsoft Store) for building.

Writes:
  - windows-app/SecondWind/app.ico
  - windows-app/package/Images/*.png   (Store tiles and logos)
  - windows-app/package/AppxManifest.xml (from AppxManifest.template.xml + windows-app/store.json + VERSION)

The app reads desktop/data.json and desktop/cans directly (linked in SecondWind.csproj).
The app itself is compiled and packaged (MSIX) on GitHub's Windows machines:
.github/workflows/windows-app.yml. Run after build_desktop (tools/build.py calls this for you).
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_extension  # noqa: E402  (brand data + icon drawing)

APP = os.path.join(ROOT, "windows-app")
PROJ = os.path.join(APP, "SecondWind")
PKG = os.path.join(APP, "package")
VERSION = build_extension.VERSION

# Logo name -> (width, height) at scale 100. Each is also written at scale 200.
LOGOS = {
    "Square44x44Logo": (44, 44),
    "Square150x150Logo": (150, 150),
    "Wide310x150Logo": (310, 150),
    "StoreLogo": (50, 50),
}
TASKBAR_SIZES = (16, 24, 32, 48, 256)


def logo(icon, w, h, fill):
    """The can icon centered on a transparent w x h canvas, taking up `fill` of the height."""
    from PIL import Image
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s = max(1, int(round(min(w, h) * fill)))
    small = icon.resize((s, s), Image.LANCZOS)
    im.paste(small, ((w - s) // 2, (h - s) // 2), small)
    return im


def images():
    icon = build_extension.draw_icon()
    icon.save(os.path.join(PROJ, "app.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    d = os.path.join(PKG, "Images")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for name, (w, h) in LOGOS.items():
        fill = 0.92 if name in ("Square44x44Logo", "StoreLogo") else 0.62
        for scale in (100, 200):
            im = logo(icon, w * scale // 100, h * scale // 100, fill)
            suffix = "" if scale == 100 else f".scale-{scale}"
            im.save(os.path.join(d, f"{name}{suffix}.png"))
    # Taskbar and Start menu list icons (exact pixel sizes, no plate behind them).
    for s in TASKBAR_SIZES:
        im = logo(icon, s, s, 1.0)
        im.save(os.path.join(d, f"Square44x44Logo.targetsize-{s}.png"))
        im.save(os.path.join(d, f"Square44x44Logo.targetsize-{s}_altform-unplated.png"))


def manifest():
    store = json.load(open(os.path.join(APP, "store.json"), encoding="utf-8"))
    parts = (VERSION.split(".") + ["0", "0", "0"])[:3]
    text = open(os.path.join(PKG, "AppxManifest.template.xml"), encoding="utf-8").read()
    for key, val in {
        "IDENTITY_NAME": store["identity_name"],
        "PUBLISHER": store["publisher"],
        "PUBLISHER_DISPLAY_NAME": store["publisher_display_name"],
        "VERSION": ".".join(parts) + ".0",   # the Store needs the last number to be 0
    }.items():
        text = text.replace("{{" + key + "}}", val)
    assert "{{" not in text, "unfilled placeholder in AppxManifest.template.xml"
    open(os.path.join(PKG, "AppxManifest.xml"), "w", encoding="utf-8").write(text)


def main():
    images()
    manifest()
    print(f"Prepared Windows app v{VERSION}: windows-app/ (compiled + packaged on GitHub, see .github/workflows/windows-app.yml)")


if __name__ == "__main__":
    main()
