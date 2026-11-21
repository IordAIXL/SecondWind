"""Second Wind can art.

One hand-drawn SVG can per brand, styled after each brand's real can
(colors, layout, flavor color schemes). Every flavor gets its own colors,
taken from data/brands.json -> brand["flavor_colors"].

To swap the art for a brand, edit (or replace) its ART_<id> function below,
or drop a finished SVG over docs/cans/<id>.svg after the build.

Used by tools/build.py. Entry point: can_svg(brand, flavor=None).
"""
import html
import math
import os
import re

# Lettering is drawn as vector outlines from the open-source (OFL) fonts in
# tools/fonts/, so every can looks the same on every device.
BLACK = "anton"          # tall condensed impact style
WIDE = "archivo"         # wide heavy grotesk
SANS = "inter"           # small print (weight picks Bold / ExtraBold / Black)
SERIF = "dmserif"
SCRIPT = "pacifico"
MONO = "inter"
RYSE_FONT = "saira"      # heavy condensed, used slanted
GHOST_FONT = "rubik"     # chunky rounded
REIGN_FONT = "russo"     # sharp squared
COND = "oswald"

FONT_FILES = {
    "anton": "Anton-Regular.ttf", "archivo": "ArchivoBlack-Regular.ttf",
    "inter700": "Inter-Bold.ttf", "inter800": "Inter-ExtraBold.ttf", "inter900": "Inter-Black.ttf",
    "dmserif": "DMSerifDisplay-Regular.ttf", "pacifico": "Pacifico-Regular.ttf",
    "saira": "SairaCondensed-Black.ttf", "rubik": "Rubik-Black.ttf", "russo": "RussoOne-Regular.ttf",
    "oswald": "Oswald-Bold.ttf",
}
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_FONTS = {}


def _font(key, weight):
    if key == "inter":
        key = "inter" + str(800 if weight == 800 else (900 if weight >= 900 else 700))
    if key not in _FONTS:
        from fontTools.ttLib import TTFont
        f = TTFont(os.path.join(FONT_DIR, FONT_FILES[key]))
        _FONTS[key] = (f, f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    return _FONTS[key]


def _outline(s, size, key, weight, spacing=0.0):
    """Return (path_d, width) for string s at font size `size`, baseline y=0, starting x=0."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    f, gs, cmap, hmtx, upem = _font(key, weight)
    sc = size / upem
    pen = SVGPathPen(gs, lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    x = 0.0
    for ch in s:
        gname = cmap.get(ord(ch)) or cmap.get(ord("?"))
        if gname is None:
            continue
        gs[gname].draw(TransformPen(pen, (sc, 0, 0, -sc, x, 0)))
        x += hmtx[gname][0] * sc + spacing
    if s:
        x -= spacing
    return pen.getCommands(), x

SHAPES = {
    # x, y (top of lid), w, h  inside a 120 x 220 viewBox
    "tall": (16, 6, 88, 204),      # 16 oz tall can (Monster, Bang, Ghost...)
    "sleek": (31, 22, 58, 188),    # 12 oz skinny can (Celsius, Alani Nu, Zoa...)
    "slim": (34, 42, 52, 166),     # 8.4 oz small slim can (Red Bull)
    "stubby": (22, 70, 76, 138),   # 11 oz cold brew can
}

BRAND_SHAPE = {
    "redbull": "slim", "celsius": "sleek", "zoa": "sleek", "prime": "sleek",
    "alani": "sleek", "coffee": "stubby", "tea": "sleek",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "flavor"


def ink(bg, dark="#111111", light="#ffffff"):
    """Readable text color on top of a background color."""
    h = bg.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return dark if lum > 0.6 else light


def esc(s):
    return html.escape(str(s))


class G:
    """Geometry + colors for one can."""

    def __init__(self, brand, flavor, shape):
        x, y, w, h = SHAPES[shape]
        self.x, self.w = x, w
        self.r = x + w
        self.cx = x + w / 2
        self.lid = y
        self.t = y + 12            # top of printed body
        self.b = y + h - 12        # bottom of printed body
        self.h = self.b - self.t
        self.my = (self.t + self.b) / 2
        c = dict(brand["colors"])
        fc = brand.get("flavor_colors", {}).get(flavor)
        if isinstance(fc, str):
            c["accent"] = fc
        elif isinstance(fc, dict):
            c.update(fc)
        self.c = c
        self.id = brand["id"]
        self.name = brand["name"]
        self.flavor = flavor

    def y(self, f):
        """Fraction of the printed body height -> y coordinate."""
        return self.t + self.h * f


def text(x, y, s, size, fill, family=SANS, weight=700, anchor="middle", fit=None, extra=""):
    """Draw a line of lettering as a vector path.

    fit: squeeze the line to at most this width (or exactly this width when extra contains "force").
    extra may hold letter-spacing="N", font-style="italic", stroke attributes and opacity.
    """
    force = "force" in extra
    extra = extra.replace("force", "")
    m = re.search(r'letter-spacing="([\d.\-]+)"', extra)
    spacing = float(m.group(1)) if m else 0.0
    extra = re.sub(r'letter-spacing="[^"]*"', "", extra)
    italic = 'font-style="italic"' in extra or family == RYSE_FONT
    extra = extra.replace('font-style="italic"', "")
    d, wdt = _outline(str(s), size, family, weight, spacing)
    sx = 1.0
    if fit is not None and wdt > 0 and (wdt > fit or force):
        sx = fit / wdt
    tw = wdt * sx
    x0 = x - tw / 2 if anchor == "middle" else (x - tw if anchor == "end" else x)
    skew = " skewX(-12)" if italic else ""
    sw = ""
    if "stroke-width" in extra:
        # keep strokes even when the line is squeezed
        extra = extra.replace('stroke-width="', 'vector-effect="non-scaling-stroke" stroke-width="')
    return (f'<path transform="translate({x0:.2f} {y:.2f}){skew} scale({sx:.4f} 1)" d="{d}" '
            f'fill="{fill}" {extra.strip()}{sw}/>')


def flavor_lines(s, maxlen):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > maxlen:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    return lines[:3]


def flavor_text(g, y, size, fill, family=SANS, weight=700, maxlen=12, upper=True, width=None):
    s = g.flavor.upper() if upper else g.flavor
    lines = flavor_lines(s, maxlen)
    out = []
    width = width or g.w - 10
    for i, ln in enumerate(lines):
        out.append(text(g.cx, y + i * (size + 1.5), ln, size, fill, family, weight, fit=width))
    return "".join(out)


def star_pts(x, y, r, inner=0.45, n=5, rot=-90):
    p = []
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot) + math.pi * i / n
        p.append(f"{x + rr * math.cos(a):.1f},{y + rr * math.sin(a):.1f}")
    return " ".join(p)


def vtext(x, y, s, size, fill, family=BLACK, weight=900, fit=None, rot=-90, extra=""):
    """Text running up the can."""
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot})">' + text(0, 0, s, size, fill, family, weight, fit=fit, extra=extra) + "</g>"


# ------------------------------------------------------------------ brands

def shade(hexc, f):
    """Darken (f < 1) or lighten (f > 1) a hex color."""
    h = hexc.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if f < 1:
        rgb = [int(v * f) for v in rgb]
    else:
        rgb = [int(v + (255 - v) * (f - 1)) for v in rgb]
    return "#" + "".join(f"{max(0, min(255, v)):02x}" for v in rgb)


def ART_redbull(g):
    c = g.c
    s = c["band"]
    blue = c["body"]
    # checkered trapezoid tiles: top half and bottom half split into 4 tiles
    tiles = []
    hw = g.w / 2
    for row, (y0, y1) in enumerate([(g.t, g.my), (g.my, g.b)]):
        for col in range(2):
            x0 = g.x + col * hw
            colr = blue if (row + col) % 2 == 0 else s
            tiles.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{hw:.1f}" height="{y1 - y0:.1f}" fill="{colr}"/>')
    sy = g.my - 4
    # center emblem area
    emblem = (f'<ellipse cx="{g.cx}" cy="{sy}" rx="{hw - 2:.1f}" ry="36" fill="{s}"/>'
              f'<circle cx="{g.cx}" cy="{sy - 10}" r="13" fill="{c["accent2"]}"/>'
              # two charging bulls, abstract
              + bull(g.cx - 10.5, sy - 6, 1, c["accent"]) + bull(g.cx + 10.5, sy - 6, -1, c["accent"]) +
              text(g.cx, sy + 18, g.name, 13, c["accent"], SANS, 900, fit=hw * 2 - 10,
                   extra='font-style="italic" letter-spacing="-0.5"') +
              text(g.cx, sy + 27, "ENERGY DRINK", 5.5, "#1f3a8a", SANS, 800, fit=hw * 2 - 16))
    ed = "" if g.flavor in ("Original",) else (
        text(g.cx, g.y(0.12), g.flavor.upper() if len(g.flavor) < 14 else g.flavor.upper(), 6.5, c["text"], SANS, 900,
             fit=g.w - 8) + text(g.cx, g.y(0.17), "EDITION" if g.flavor not in ("Sugarfree", "Zero") else "", 4.5,
                                   c["text"], SANS, 700))
    return "".join(tiles) + emblem + ed


def bull(x, y, d, col):
    # a charging bull silhouette: head down, horns forward, facing the center
    return (f'<g transform="translate({x} {y}) scale({d * 0.72:.2f} 0.72)">'
            f'<path d="M-14 1 C-15 -4 -10 -7 -4 -6 L3 -7.5 C7 -8.5 9 -6.5 10 -3.5 L13.5 -0.5 L15 3 L12 3.4 '
            f'L10 1.6 L8.2 2.6 L8.6 7.5 L6.4 7.5 L5.6 3.4 L-5.5 3.4 L-7.5 8 L-9.7 8 L-9.6 3 '
            f'C-11 3.4 -13 5 -15.5 7.5 C-14 4.5 -13.5 3 -14 1 Z" fill="{col}"/>'
            f'<path d="M10.5 -3 q3.5 -3.2 6.5 -1.6" stroke="{col}" stroke-width="1.2" fill="none" stroke-linecap="round"/>'
            f'</g>')


def ART_monster(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    # three ragged claw marks: wide and torn at the top, sharp at the bottom
    import random
    rnd = random.Random(7)
    top, bot = g.y(0.05), g.y(0.64)
    for i, dx in enumerate((-21, 0, 21)):
        x0 = g.cx + dx
        n = 16
        right, left = [], []
        for k in range(n + 1):
            f = k / n
            yy = top + (bot - top) * f + (i - 1) * 2
            half = 7.5 * (1 - f) ** 0.7 + 0.4
            drift = math.sin(f * 7 + i) * 2.2 + (i - 1) * f * 3
            right.append((x0 + drift + half + rnd.uniform(-1.6, 1.6) * (k % 2), yy))
            left.append((x0 + drift - half - rnd.uniform(0, 2.2) * ((k + 1) % 2), yy))
        poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in right + left[::-1])
        out.append(f'<polygon points="{poly}" fill="{a}"/>')
        # torn specks
        for _ in range(3):
            out.append(f'<circle cx="{x0 + rnd.uniform(-9, 9):.1f}" cy="{top + rnd.uniform(-2, 30):.1f}" '
                       f'r="{rnd.uniform(0.5, 1.3):.1f}" fill="{a}"/>')
    out.append(text(g.cx, g.y(0.72), "MONSTER", 13, c["text"], BLACK, 900, fit=g.w - 16,
                    extra='letter-spacing="1" force'))
    out.append(text(g.cx, g.y(0.78), "ENERGY", 6, a if ink(a) != ink(c["body"]) else c["text"], BLACK, 900, fit=34, extra='force'))
    out.append(flavor_text(g, g.y(0.88), 6.5, c["text"], SANS, 800, maxlen=14))
    return "".join(out)


def ART_celsius(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           # flavor band across lower middle
           f'<path d="M{g.x} {g.y(0.48)} C{g.cx - 10} {g.y(0.42)},{g.cx + 10} {g.y(0.56)},{g.r} {g.y(0.5)} '
           f'L{g.r} {g.y(0.86)} L{g.x} {g.y(0.86)} Z" fill="{a}"/>',
           f'<rect x="{g.x}" y="{g.y(0.30)}" width="{g.w}" height="2.2" fill="{c["text"]}"/>',
           text(g.cx, g.y(0.22), "CELSIUS", 14, c["accent3"] if "accent3" in c else "#e11d2e", WIDE, 900,
                fit=g.w - 10, extra='force font-style="italic"'),
           text(g.cx, g.y(0.36), "LIVE FIT", 5, c["text"], SANS, 800, extra='letter-spacing="2"'),
           text(g.cx, g.y(0.41), "ESSENTIAL ENERGY", 3.8, c["text"], SANS, 700, extra='letter-spacing="1"'),
           ]
    # fruit circles
    for fx, fy, fr in ((g.cx - 14, g.y(0.66), 8), (g.cx + 10, g.y(0.62), 6), (g.cx + 4, g.y(0.75), 4)):
        out.append(f'<circle cx="{fx}" cy="{fy:.1f}" r="{fr}" fill="#fff" opacity="0.35"/>'
                   f'<circle cx="{fx}" cy="{fy:.1f}" r="{fr * 0.55:.1f}" fill="#fff" opacity="0.35"/>')
    out.append(flavor_text(g, g.y(0.93), 5.5, c["text"], SANS, 900, maxlen=16))
    return "".join(out)


def ART_ryse(g):
    c = g.c
    a = c["accent"]
    hi, lo = shade(a, 1.25), shade(a, 0.55)
    gid = f"ry-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="{hi}"/>'
           f'<stop offset="0.55" stop-color="{a}"/><stop offset="1" stop-color="{lo}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})"/>']
    # rising diagonal stripes in the background
    for i in range(7):
        x0 = g.x - 40 + i * 22
        out.append(f'<polygon points="{x0},{g.b} {x0 + 9},{g.b} {x0 + 69},{g.t} {x0 + 60},{g.t}" fill="#fff" opacity="0.07"/>')
    # logo block
    out.append(f'<polygon points="{g.cx},{g.y(0.035)} {g.cx + 8},{g.y(0.085)} {g.cx - 8},{g.y(0.085)}" fill="#111"/>')
    out.append(text(g.cx, g.y(0.19), "RYSE", 26, "#fff", RYSE_FONT, 900, fit=g.w - 16,
                    extra='force stroke="#111" stroke-width="1.6" paint-order="stroke"'))
    out.append(f'<rect x="{g.x}" y="{g.y(0.215)}" width="{g.w}" height="3" fill="#111"/>')
    # big FUEL across the can
    out.append(text(g.cx, g.y(0.46), "FUEL", 46, "#111", RYSE_FONT, 900, fit=g.w - 8, extra="force"))
    out.append(text(g.cx - 1.5, g.y(0.46) - 1.5, "FUEL", 46, "#fff", RYSE_FONT, 900, fit=g.w - 8, extra="force"))
    out.append(text(g.cx, g.y(0.52), "ENERGY", 7, "#111", SANS, 900, extra='letter-spacing="3"'))
    # slanted flavor ribbon
    nl = len(flavor_lines(g.flavor.upper(), 13))
    rh = 9 + nl * 7.5
    out.append(f'<g transform="rotate(-8 {g.cx} {g.y(0.70)})"><rect x="{g.x - 6}" y="{g.y(0.66)}" width="{g.w + 12}" '
               f'height="{rh}" fill="#111"/>'
               + flavor_text(g, g.y(0.66) + 9.5, 6.5, "#fff", RYSE_FONT, 900, maxlen=13, width=g.w - 18)
               + "</g>")
    out.append(text(g.cx, g.y(0.93), "ZERO SUGAR · 200MG CAFFEINE", 3.8, ink(lo), SANS, 800, fit=g.w - 14))
    return "".join(out)


def ART_ghost(g):
    c = g.c
    a = c["accent"]
    fg = ink(a, "#111111", "#ffffff")
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{a}"/>',
           f'<radialGradient id="gh-{slug(g.flavor)}" cx="0.5" cy="0.45" r="0.6"><stop offset="0" stop-color="#fff" stop-opacity="0.28"/>'
           f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#gh-{slug(g.flavor)})"/>']
    out.append(text(g.cx, g.y(0.15), "GHOST", 24, "#111", GHOST_FONT, 900, fit=g.w - 14, extra="force"))
    out.append(f'<rect x="{g.x + 12}" y="{g.y(0.175)}" width="{g.w - 24}" height="9" rx="1" fill="#111"/>')
    out.append(text(g.cx, g.y(0.175) + 7, "ENERGY", 6.5, a, GHOST_FONT, 900, extra='letter-spacing="3.5"'))
    # big ghost logo
    gx, gy, R = g.cx, g.y(0.47), 22
    out.append(f'<path d="M{gx - R} {gy + R + 6} V{gy} a{R} {R} 0 0 1 {2 * R} 0 V{gy + R + 6} '
               f'q-{R / 4:.1f} -7 -{R / 2:.1f} 0 q-{R / 4:.1f} 7 -{R / 2:.1f} 0 q-{R / 4:.1f} -7 -{R / 2:.1f} 0 '
               f'q-{R / 4:.1f} 7 -{R / 2:.1f} 0 z" fill="#fff" stroke="#111" stroke-width="3.2" stroke-linejoin="round"/>')
    out.append(f'<ellipse cx="{gx - 8}" cy="{gy + 2}" rx="4.2" ry="6.2" fill="#111"/>'
               f'<ellipse cx="{gx + 8}" cy="{gy + 2}" rx="4.2" ry="6.2" fill="#111"/>'
               f'<ellipse cx="{gx - 9.2}" cy="{gy - 0.5}" rx="1.3" ry="1.8" fill="#fff"/>'
               f'<ellipse cx="{gx + 6.8}" cy="{gy - 0.5}" rx="1.3" ry="1.8" fill="#fff"/>')
    nl = len(flavor_lines(g.flavor.upper(), 12))
    out.append(f'<rect x="{g.x + 6}" y="{g.y(0.72)}" width="{g.w - 12}" height="{9 + nl * 8.5}" rx="4" fill="#fff" stroke="#111" stroke-width="2"/>')
    out.append(flavor_text(g, g.y(0.72) + 10.5, 7, "#111", GHOST_FONT, 900, maxlen=12, width=g.w - 22))
    out.append(text(g.cx, g.y(0.95), "ZERO SUGAR · 200MG CAFFEINE", 3.8, fg, SANS, 800, fit=g.w - 16))
    return "".join(out)


def ART_bang(g):
    c = g.c
    a = c["accent"]
    gid = f"bg-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{a}"/>'
           f'<stop offset="0.5" stop-color="{c["accent2"]}"/><stop offset="1" stop-color="{a}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})" opacity="0.85"/>']
    # starburst lines
    for i in range(18):
        ang = math.pi * 2 * i / 18
        out.append(f'<line x1="{g.cx + 14:.1f}" y1="{g.y(0.45):.1f}" x2="{g.cx + 14 + 80 * math.cos(ang):.1f}" '
                   f'y2="{g.y(0.45) + 80 * math.sin(ang):.1f}" stroke="#fff" stroke-width="1.2" opacity="0.25"/>')
    out.append(vtext(g.cx - 8, g.y(0.43), "BANG", 34, "#fff", WIDE, 900, fit=g.h * 0.7,
                     extra=f'stroke="{c["body"]}" stroke-width="1.5" force'))
    out.append(vtext(g.cx + 20, g.y(0.5), "ENERGY", 7, c["body"], WIDE, 900, extra='letter-spacing="3"'))
    out.append(f'<rect x="{g.x}" y="{g.y(0.86)}" width="{g.w}" height="20" fill="{c["body"]}"/>')
    out.append(flavor_text(g, g.y(0.86) + 8, 6, "#fff", SANS, 900, maxlen=16))
    return "".join(out)


def ART_reign(g):
    c = g.c
    a = c["accent"]
    gid = f"re-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{shade(a, 1.1)}"/>'
           f'<stop offset="0.55" stop-color="{shade(a, 0.75)}"/><stop offset="1" stop-color="{shade(a, 0.22)}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})"/>',
           f'<rect x="{g.x + 5}" y="{g.t}" width="2.5" height="{g.h}" fill="#111" opacity="0.55"/>',
           f'<rect x="{g.r - 7.5}" y="{g.t}" width="2.5" height="{g.h}" fill="#111" opacity="0.55"/>']
    cy = g.y(0.1)
    out.append(f'<path d="M{g.cx - 16} {cy + 9} L{g.cx - 18} {cy - 7} L{g.cx - 8} {cy + 1} L{g.cx} {cy - 11} '
               f'L{g.cx + 8} {cy + 1} L{g.cx + 18} {cy - 7} L{g.cx + 16} {cy + 9} Z" fill="#111"/>'
               f'<circle cx="{g.cx}" cy="{cy - 12}" r="2" fill="#111"/><circle cx="{g.cx - 18}" cy="{cy - 8}" r="1.8" fill="#111"/>'
               f'<circle cx="{g.cx + 18}" cy="{cy - 8}" r="1.8" fill="#111"/>'
               f'<rect x="{g.cx - 16}" y="{cy + 11}" width="32" height="3.2" fill="#111"/>'
               f'<path d="M{g.cx} {cy - 2} l3 4 -3 4 -3 -4 z" fill="{a}"/>')
    out.append(vtext(g.cx + 11, g.y(0.52), "REIGN", 34, "#fff", REIGN_FONT, 400, fit=g.h * 0.52,
                     extra='stroke="#111" stroke-width="2" paint-order="stroke" force'))
    out.append(text(g.cx, g.y(0.835), "TOTAL BODY FUEL", 6, "#fff", COND, 700, extra='letter-spacing="1.2"'))
    out.append(flavor_text(g, g.y(0.9), 6.5, "#fff", COND, 700, maxlen=16, width=g.w - 20))
    return "".join(out)


def ART_c4(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           f'<polygon points="{g.x},{g.y(0.55)} {g.r},{g.y(0.40)} {g.r},{g.y(0.62)} {g.x},{g.y(0.77)}" fill="{a}"/>']
    # hazard stripes along band edges
    for i in range(12):
        x0 = g.x - 10 + i * 9
        out.append(f'<polygon points="{x0},{g.y(0.98)} {x0 + 4},{g.y(0.98)} {x0 + 10},{g.y(0.92)} {x0 + 6},{g.y(0.92)}" fill="{a}"/>')
    out.append(text(g.cx, g.y(0.34), "C4", 46, c["text"], WIDE, 900, fit=g.w - 24,
                    extra=f'stroke="{a}" stroke-width="2" force font-style="italic"'))
    out.append(text(g.cx, g.y(0.42), "ENERGY", 8, a, WIDE, 900, extra='letter-spacing="4"'))
    out.append(flavor_text(g, g.y(0.6), 6.5, ink(a), WIDE, 900, maxlen=12))
    out.append(text(g.cx, g.y(0.86), "EXPLOSIVE ENERGY", 4.5, c["text"], SANS, 800, extra='letter-spacing="1"'))
    return "".join(out)


def ART_alani(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{a}"/>',
           f'<path d="M{g.x} {g.y(0.62)} C{g.cx - 20} {g.y(0.5)},{g.cx + 20} {g.y(0.78)},{g.r} {g.y(0.62)} '
           f'L{g.r} {g.b} L{g.x} {g.b} Z" fill="#fff" opacity="0.35"/>',
           text(g.cx, g.y(0.34), "alani nu", 20, c["text"], SCRIPT, 700, fit=g.w - 14,
                extra='force font-style="italic"'),
           text(g.cx, g.y(0.42), "ENERGY", 6, c["text"], SANS, 800, extra='letter-spacing="4"')]
    for sx, sy, sr in ((g.x + 14, g.y(0.12), 5), (g.r - 16, g.y(0.18), 4), (g.x + 20, g.y(0.55), 3), (g.r - 12, g.y(0.5), 3.5)):
        out.append(f'<polygon points="{star_pts(sx, sy, sr, 0.35, 4, 0)}" fill="#fff"/>')
    out.append(flavor_text(g, g.y(0.74), 8, c["text"], SERIF, 700, maxlen=12, upper=False))
    out.append(text(g.cx, g.y(0.93), "200MG CAFFEINE", 4, c["text"], SANS, 700, extra='letter-spacing="1"'))
    return "".join(out)


def ART_prime(g):
    c = g.c
    gid = f"pr-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["accent"]}"/>'
           f'<stop offset="1" stop-color="{c["accent2"]}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})"/>']
    # faceted gem shape
    cx, cy = g.cx, g.y(0.47)
    out.append(f'<polygon points="{cx},{cy - 26} {cx + 22},{cy - 8} {cx + 14},{cy + 22} {cx - 14},{cy + 22} {cx - 22},{cy - 8}" '
               f'fill="#fff" opacity="0.92"/>'
               f'<polygon points="{cx},{cy - 26} {cx + 8},{cy - 6} {cx},{cy + 22} {cx - 8},{cy - 6}" fill="{c["accent"]}" opacity="0.35"/>'
               f'<polyline points="{cx - 22},{cy - 8} {cx - 8},{cy - 6} {cx + 8},{cy - 6} {cx + 22},{cy - 8}" '
               f'stroke="{c["accent2"]}" stroke-width="1" fill="none" opacity="0.6"/>')
    out.append(text(g.cx, g.y(0.17), "PRIME", 18, "#fff", WIDE, 900, fit=g.w - 12, extra="force"))
    out.append(f'<rect x="{g.cx - 16}" y="{g.y(0.205)}" width="32" height="9" rx="4.5" fill="#fff"/>')
    out.append(text(g.cx, g.y(0.205) + 6.8, "ENERGY", 5.5, c["accent2"], WIDE, 900))
    out.append(flavor_text(g, g.y(0.8), 6.5, ink(c["accent2"]), WIDE, 900, maxlen=12))
    out.append(text(g.cx, g.y(0.95), "ZERO SUGAR · 200MG", 3.8, "#fff", SANS, 700))
    return "".join(out)


def ART_rockstar(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    for i, xo in enumerate((4, 10)):
        out.append(f'<rect x="{g.x + xo}" y="{g.t}" width="3" height="{g.h}" fill="{a if i == 0 else c["accent2"]}"/>')
        out.append(f'<rect x="{g.r - xo - 3}" y="{g.t}" width="3" height="{g.h}" fill="{a if i == 0 else c["accent2"]}"/>')
    out.append(f'<polygon points="{star_pts(g.cx, g.y(0.36), 26, 0.42)}" fill="{a}"/>')
    out.append(f'<polygon points="{star_pts(g.cx, g.y(0.36), 15, 0.42)}" fill="{c["body"]}"/>')
    out.append(text(g.cx, g.y(0.66), "ROCKSTAR", 13, c["text"], WIDE, 900, fit=g.w - 30,
                    extra='force font-style="italic"'))
    out.append(text(g.cx, g.y(0.72), "ENERGY DRINK", 5, a, SANS, 900, extra='letter-spacing="1.5"'))
    out.append(flavor_text(g, g.y(0.84), 6, c["text"], SANS, 900, maxlen=13, width=g.w - 32))
    return "".join(out)


def ART_3d(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    # isometric cube pattern
    s = 10
    for row in range(int(g.h / (s * 1.5)) + 2):
        for col in range(int(g.w / (s * 1.73)) + 2):
            x0 = g.x + col * s * 1.73 + (row % 2) * s * 0.866
            y0 = g.t + row * s * 1.5
            out.append(f'<polygon points="{x0:.1f},{y0 - s:.1f} {x0 + s * 0.866:.1f},{y0 - s / 2:.1f} {x0:.1f},{y0:.1f} '
                       f'{x0 - s * 0.866:.1f},{y0 - s / 2:.1f}" fill="{c["band"]}" opacity="0.6"/>')
    out.append(text(g.cx, g.y(0.5), "3D", 54, c["body"], WIDE, 900, fit=g.w - 16,
                    extra=f'stroke="{a}" stroke-width="3" force'))
    out.append(text(g.cx, g.y(0.58), "ENERGY", 8, a, WIDE, 900, extra='letter-spacing="4"'))
    out.append(f'<rect x="{g.x}" y="{g.y(0.76)}" width="{g.w}" height="18" fill="{a}"/>')
    out.append(flavor_text(g, g.y(0.76) + 12, 7, ink(a), WIDE, 900, maxlen=14))
    return "".join(out)


def ART_buckedup(g):
    c = g.c
    a = c["accent"]
    fg = ink(a)
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{a}"/>',
           f'<rect x="{g.x}" y="{g.y(0.40)}" width="{g.w}" height="{g.h * 0.30:.1f}" fill="#111"/>']
    # deer head with antlers
    x, y = g.cx, g.y(0.25)
    def side(s):
        return (f'<path d="M{x + s * 5} {y - 4} C{x + s * 9} {y - 14},{x + s * 18} {y - 18},{x + s * 24} {y - 32} '
                f'M{x + s * 13} {y - 14} L{x + s * 24} {y - 16} M{x + s * 19} {y - 22} L{x + s * 15} {y - 33} '
                f'M{x + s * 22} {y - 28} L{x + s * 31} {y - 29}" stroke="#111" stroke-width="3.6" fill="none" stroke-linecap="round"/>')
    out.append(side(1) + side(-1))
    out.append(f'<path d="M{x - 7} {y - 6} Q{x} {y - 10} {x + 7} {y - 6} L{x + 4} {y + 10} Q{x} {y + 14} {x - 4} {y + 10} Z" fill="#111"/>'
               f'<path d="M{x - 7} {y - 5} l-6 -3 3 6 z M{x + 7} {y - 5} l6 -3 -3 6 z" fill="#111"/>')
    out.append(text(g.cx, g.y(0.40) + 20, "BUCKED", 15, "#fff", WIDE, 900, fit=g.w - 14, extra="force"))
    out.append(text(g.cx, g.y(0.40) + 38, "UP", 17, a, WIDE, 900))
    out.append(text(g.cx, g.y(0.40) + 48, "ENERGY", 5, "#fff", SANS, 800, extra='letter-spacing="3"'))
    out.append(flavor_text(g, g.y(0.80), 6.5, fg, WIDE, 900, maxlen=13, width=g.w - 16))
    out.append(text(g.cx, g.y(0.95), "300MG CAFFEINE · ZERO SUGAR", 3.4, fg, SANS, 800, fit=g.w - 14))
    return "".join(out)


def ART_zoa(g):
    c = g.c
    a = c["accent"]
    gid = f"zo-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0.25" stop-color="{c["body"]}"/>'
           f'<stop offset="1" stop-color="{a}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})"/>']
    out.append(vtext(g.x + 26, g.y(0.46), "ZOA", 30, c["text"], WIDE, 900, fit=g.h * 0.4, extra="force"))
    out.append(vtext(g.x + 36, g.y(0.46), "ENERGY", 6, c["text"], SANS, 800, extra='letter-spacing="3"'))
    for i in range(3):
        yy = g.y(0.74) + i * 6
        out.append(f'<path d="M{g.x} {yy} q8.5 -5 17 0 t17 0 t17 0 t17 0" stroke="#fff" stroke-width="2" fill="none" opacity="0.7"/>')
    out.append(text(g.r - 8, g.y(0.15), "PLANT", 4.5, c["text"], SANS, 800, anchor="end"))
    out.append(text(g.r - 8, g.y(0.19), "POWERED", 4.5, c["text"], SANS, 800, anchor="end"))
    out.append(flavor_text(g, g.y(0.9), 6, ink(a), SANS, 900, maxlen=14))
    return "".join(out)


def ART_coffee(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    for i in range(14):
        bx = g.x + 6 + (i * 23) % (g.w - 8)
        by = g.t + 6 + (i * 17) % (g.h - 10)
        out.append(f'<g transform="rotate({(i * 47) % 180} {bx} {by})"><ellipse cx="{bx}" cy="{by}" rx="3" ry="4.5" '
                   f'fill="{c["band"]}"/><path d="M{bx} {by - 4} q-1.5 4 0 8" stroke="{c["body"]}" stroke-width="0.8" fill="none"/></g>')
    out.append(f'<rect x="{g.x + 8}" y="{g.y(0.18)}" width="{g.w - 16}" height="{g.h * 0.62:.1f}" rx="3" fill="{a}"/>')
    out.append(text(g.cx, g.y(0.34), "COLD BREW", 11, c["body"], SERIF, 700, fit=g.w - 24, extra="force"))
    out.append(f'<line x1="{g.x + 16}" y1="{g.y(0.39)}" x2="{g.r - 16}" y2="{g.y(0.39)}" stroke="{c["accent2"]}" stroke-width="1"/>')
    out.append(flavor_text(g, g.y(0.52), 8, c["accent2"], SERIF, 700, maxlen=12, upper=False, width=g.w - 24))
    out.append(text(g.cx, g.y(0.74), "SMALL BATCH · STRONG", 4, c["body"], SANS, 700, extra='letter-spacing="0.5"'))
    return "".join(out)


def ART_tea(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           f'<circle cx="{g.cx}" cy="{g.y(0.4)}" r="22" fill="none" stroke="{a}" stroke-width="6" '
           f'stroke-dasharray="120 20" stroke-linecap="round" transform="rotate(-60 {g.cx} {g.y(0.4)})"/>',
           f'<path d="M{g.cx} {g.y(0.4) - 14} q12 14 0 28 q-12 -14 0 -28 z" fill="{c["accent2"]}"/>',
           f'<line x1="{g.cx}" y1="{g.y(0.4) - 10}" x2="{g.cx}" y2="{g.y(0.4) + 12}" stroke="{c["body"]}" stroke-width="1.2"/>',
           text(g.cx, g.y(0.14), "TEA", 18, c["text"], SERIF, 700, extra='letter-spacing="6"'),
           f'<rect x="{g.x}" y="{g.y(0.66)}" width="{g.w}" height="26" fill="{a}"/>']
    out.append(flavor_text(g, g.y(0.66) + 11, 7, "#fff", SERIF, 700, maxlen=12, upper=False))
    out.append(text(g.cx, g.y(0.92), "STEEPED · UNSWEETENED", 3.8, c["text"], SANS, 700, extra='letter-spacing="0.5"'))
    return "".join(out)


def ART_mystery(g):
    c = g.c
    gid = f"my-{slug(g.flavor)}"
    out = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["band"]}"/>'
           f'<stop offset="1" stop-color="{c["body"]}"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="url(#{gid})"/>']
    for row in range(9):
        for col in range(4):
            out.append(text(g.x + 10 + col * 22 + (row % 2) * 11, g.t + 14 + row * 21, "?", 14, "#fff", SERIF, 700,
                            extra='opacity="0.12"'))
    out.append(text(g.cx, g.y(0.16), "MYSTERY", 14, c["accent"], WIDE, 900, fit=g.w - 16, extra="force"))
    out.append(text(g.cx, g.y(0.22), "CAN", 8, c["text"], WIDE, 900, extra='letter-spacing="6"'))
    # sticker label with the made-up flavor
    out.append(f'<g transform="rotate(-6 {g.cx} {g.y(0.5)})"><rect x="{g.x + 8}" y="{g.y(0.36)}" width="{g.w - 16}" '
               f'height="{g.h * 0.28:.1f}" rx="6" fill="#fff"/>'
               + text(g.cx, g.y(0.36) + 10, "FLAVOR:", 5, c["body"], SANS, 900, extra='letter-spacing="1"')
               + flavor_text(g, g.y(0.36) + 23, 9, c["body"], SCRIPT, 700, maxlen=10, upper=False, width=g.w - 24)
               + "</g>")
    out.append(f'<circle cx="{g.cx}" cy="{g.y(0.82)}" r="12" fill="{c["accent"]}"/>'
               + text(g.cx, g.y(0.82) + 6, "?", 17, c["body"], SERIF, 700))
    return "".join(out)


def ART_generic(g):
    c = g.c
    return (f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>'
            f'<rect x="{g.x}" y="{g.y(0.1)}" width="{g.w}" height="26" fill="{c["band"]}"/>'
            + text(g.cx, g.y(0.1) + 18, g.name.upper(), 14, c["text"], WIDE, 900, fit=g.w - 12)
            + flavor_text(g, g.y(0.85), 7, c["text"]))


# ------------------------------------------------------------------ shell

SIZE_LABEL = {
    "tall": "16 FL OZ (473 mL)", "sleek": "12 FL OZ (355 mL)",
    "slim": "8.4 FL OZ (250 mL)", "stubby": "11 FL OZ (325 mL)",
}


def can_svg(brand, flavor=None):
    bid = brand["id"]
    flavor = flavor or brand.get("flavors", ["???"])[0]
    shape = BRAND_SHAPE.get(bid, "tall")
    g = G(brand, flavor, shape)
    art = globals().get(f"ART_{bid}", ART_generic)(g)
    x, r, cx, lid, t, b, w = g.x, g.r, g.cx, g.lid, g.t, g.b, g.w
    u = f"{bid}-{slug(flavor)}"
    rx = w / 2
    ry = round(max(3.0, w * 0.075), 1)  # perspective: we look down at the can a little
    trx = rx - 6                        # lid radius (the neck is narrower than the body)
    tcy = lid + 3                       # lid center
    lry = round(ry * 0.9, 1)
    tw = round(trx * 0.55, 1)           # pull tab width
    label = f"{brand['name']} {flavor} can, Second Wind art"
    size_col = ink(g.c["body"])
    body_path = f"M{x} {t} A{rx} {ry} 0 0 0 {r} {t} L{r} {b} A{rx} {ry} 0 0 1 {x} {b} Z"
    H = round(g.h + ry * 2, 1)
    ty = round(t - ry, 1)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 220" width="120" height="220" role="img" aria-label="{esc(label)}">
  <defs>
    <linearGradient id="shade-{u}" x1="0" x2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0.55"/>
      <stop offset="0.07" stop-color="#000" stop-opacity="0.22"/>
      <stop offset="0.17" stop-color="#fff" stop-opacity="0.10"/>
      <stop offset="0.23" stop-color="#fff" stop-opacity="0.45"/>
      <stop offset="0.29" stop-color="#fff" stop-opacity="0.08"/>
      <stop offset="0.42" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.70" stop-color="#000" stop-opacity="0.08"/>
      <stop offset="0.84" stop-color="#000" stop-opacity="0.28"/>
      <stop offset="0.91" stop-color="#fff" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.62"/>
    </linearGradient>
    <linearGradient id="vshade-{u}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0.28"/>
      <stop offset="0.05" stop-color="#000" stop-opacity="0"/>
      <stop offset="0.94" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.32"/>
    </linearGradient>
    <linearGradient id="metal-{u}" x1="0" x2="1">
      <stop offset="0" stop-color="#5d626b"/><stop offset="0.12" stop-color="#9aa0a8"/>
      <stop offset="0.24" stop-color="#ffffff"/><stop offset="0.36" stop-color="#c5cad1"/>
      <stop offset="0.62" stop-color="#e3e6ea"/><stop offset="0.86" stop-color="#8d939b"/>
      <stop offset="1" stop-color="#4b5058"/>
    </linearGradient>
    <linearGradient id="lid-{u}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f4f6f8"/><stop offset="0.5" stop-color="#bfc4cb"/>
      <stop offset="1" stop-color="#8e949c"/>
    </linearGradient>
    <linearGradient id="well-{u}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#9ea4ac"/><stop offset="0.55" stop-color="#d9dde2"/>
      <stop offset="1" stop-color="#eef0f3"/>
    </linearGradient>
    <radialGradient id="floor-{u}"><stop offset="0" stop-color="#000" stop-opacity="0.4"/>
      <stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
    <clipPath id="body-{u}"><path d="{body_path}"/></clipPath>
  </defs>
  <ellipse cx="{cx}" cy="{b + 9}" rx="{rx + 8}" ry="{ry + 3}" fill="url(#floor-{u})"/>
  <path d="M{x} {b} A{rx} {ry} 0 0 0 {r} {b} L{r - 5} {b + 7} A{rx - 5} {lry} 0 0 1 {x + 5} {b + 7} Z" fill="url(#metal-{u})"/>
  <path d="M{x + 5} {b + 7} A{rx - 5} {lry} 0 0 0 {r - 5} {b + 7}" stroke="#3f444b" stroke-width="0.8" fill="none" opacity="0.6"/>
  <path d="M{x} {t} C{x} {t - 5},{x + 5} {tcy + 6},{x + 6} {tcy} L{r - 6} {tcy} C{r - 5} {tcy + 6},{r} {t - 5},{r} {t} A{rx} {ry} 0 0 1 {x} {t} Z" fill="url(#metal-{u})"/>
  <path d="M{x + 2} {t - 3} A{rx - 2} {ry} 0 0 0 {r - 2} {t - 3}" stroke="#fff" stroke-width="0.6" fill="none" opacity="0.5"/>
  <g clip-path="url(#body-{u})">
    {art}
    <text x="{cx}" y="{b - 2.5}" font-family="{SANS}" font-size="3.1" font-weight="700" text-anchor="middle" fill="{size_col}" opacity="0.75">{SIZE_LABEL[shape]}</text>
    <rect x="{x}" y="{ty}" width="{w}" height="{H}" fill="url(#vshade-{u})"/>
    <rect x="{x}" y="{ty}" width="{w}" height="{H}" fill="url(#shade-{u})"/>
    <rect x="{x + w * 0.205:.1f}" y="{ty}" width="{w * 0.025:.1f}" height="{H}" fill="#fff" opacity="0.3"/>
  </g>
  <path d="{body_path}" fill="none" stroke="#000" stroke-opacity="0.25" stroke-width="0.5"/>
  <ellipse cx="{cx}" cy="{tcy}" rx="{trx}" ry="{lry}" fill="url(#lid-{u})" stroke="#6e747c" stroke-width="0.7"/>
  <ellipse cx="{cx}" cy="{tcy + 0.4}" rx="{trx - 2.2:.1f}" ry="{lry - 1.3:.1f}" fill="url(#well-{u})" stroke="#8a9098" stroke-width="0.5"/>
  <path d="M{cx - tw * 0.45:.1f} {tcy + lry * 0.3:.1f} q{tw * 0.45:.1f} {lry * 0.55:.1f} {tw * 0.9:.1f} 0 l-{tw * 0.12:.1f} -{lry * 0.35:.1f} h-{tw * 0.66:.1f} z" fill="#a9aeb5" stroke="#7c828a" stroke-width="0.4"/>
  <path d="M{cx - tw / 2:.1f} {tcy - lry * 0.38:.1f} h{tw} a{lry * 0.38:.1f} {lry * 0.38:.1f} 0 0 1 0 {lry * 0.76:.1f} h-{tw} a{lry * 0.38:.1f} {lry * 0.38:.1f} 0 0 1 0 -{lry * 0.76:.1f} z" fill="#d6dade" stroke="#737981" stroke-width="0.5"/>
  <ellipse cx="{cx - tw * 0.22:.1f}" cy="{tcy}" rx="{tw * 0.17:.1f}" ry="{lry * 0.18:.1f}" fill="#7f858d"/>
  <circle cx="{cx + tw * 0.2:.1f}" cy="{tcy}" r="{lry * 0.15:.1f}" fill="#9097a0" stroke="#6b717a" stroke-width="0.3"/>
  <path d="M{cx - trx + 1.5:.1f} {tcy - 0.4} A{trx - 1.5:.1f} {lry - 0.6:.1f} 0 0 1 {cx + trx - 1.5:.1f} {tcy - 0.4}" stroke="#fff" stroke-width="0.7" fill="none" opacity="0.8"/>
</svg>
"""
