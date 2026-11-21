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
import re

BLACK = "Impact,'Arial Black','Inter Black','Helvetica Neue',Arial,sans-serif"
WIDE = "'Arial Black','Inter Black','Helvetica Neue',Arial,sans-serif"
SANS = "'Helvetica Neue',Arial,Inter,sans-serif"
SERIF = "Georgia,'Times New Roman',serif"
SCRIPT = "'Brush Script MT','Segoe Script','Lucida Handwriting',Georgia,cursive"
MONO = "'Courier New',Courier,monospace"

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
    s = esc(s)
    tl = ""
    if fit is not None:
        est = len(s) * size * 0.6
        if est > fit or "force" in extra:
            tl = f' textLength="{fit:.1f}" lengthAdjust="spacingAndGlyphs"'
        extra = extra.replace("force", "")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}"{tl} {extra}>{s}</text>')


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
              + bull(g.cx - 14, sy - 6, 1, c["accent"]) + bull(g.cx + 14, sy - 6, -1, c["accent"]) +
              text(g.cx, sy + 18, g.name, 13, c["accent"], SANS, 900, fit=hw * 2 - 10,
                   extra='font-style="italic" letter-spacing="-0.5"') +
              text(g.cx, sy + 27, "ENERGY DRINK", 5.5, "#1f3a8a", SANS, 800, fit=hw * 2 - 16))
    ed = "" if g.flavor in ("Original",) else (
        text(g.cx, g.y(0.12), g.flavor.upper() if len(g.flavor) < 14 else g.flavor.upper(), 6.5, c["text"], SANS, 900,
             fit=g.w - 8) + text(g.cx, g.y(0.17), "EDITION" if g.flavor not in ("Sugarfree", "Zero") else "", 4.5,
                                   c["text"], SANS, 700))
    return "".join(tiles) + emblem + ed + text(g.cx, g.y(0.93), "VITALIZES BODY AND MIND", 3.6, c["text"], SANS, 700, fit=g.w - 10)


def bull(x, y, d, col):
    # a stylized charging bull silhouette facing the center
    return (f'<g transform="translate({x} {y}) scale({d} 1)">'
            f'<path d="M-10 4 Q-11 -2 -6 -4 L2 -5 Q6 -8 9 -6 L12 -9 L11 -4 Q13 -2 11 1 L8 2 L7 7 L5 7 L4 3 '
            f'L-4 4 L-5 8 L-7 8 L-7 4 Z" fill="{col}"/></g>')


def ART_monster(g):
    c = g.c
    a = c["accent"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    # three ragged claw marks
    top, bot = g.y(0.08), g.y(0.62)
    for i, dx in enumerate((-20, 0, 20)):
        x = g.cx + dx
        pts = []
        n = 9
        for k in range(n + 1):
            yy = top + (bot - top) * k / n
            wob = (3 if k % 2 else -2) + (i - 1) * 0.6
            wdt = 6.5 - abs(k - n / 2) * 0.55
            pts.append((x + wob + wdt, yy))
        left = []
        for k in range(n, -1, -1):
            yy = top + (bot - top) * k / n
            wob = (3 if k % 2 else -2) + (i - 1) * 0.6
            wdt = 6.5 - abs(k - n / 2) * 0.55
            jag = 1.8 if k % 3 == 0 else 0
            left.append((x + wob - wdt - jag, yy))
        poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts + left)
        out.append(f'<polygon points="{poly}" fill="{a}"/>')
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
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           f'<linearGradient id="ry-{slug(g.flavor)}" x1="0" y1="1" x2="0" y2="0">'
           f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></linearGradient>',
           f'<rect x="{g.x}" y="{g.y(0.35)}" width="{g.w}" height="{g.h * 0.65:.1f}" fill="url(#ry-{slug(g.flavor)})"/>']
    # up arrows
    for i in range(3):
        yy = g.y(0.62) - i * 14
        out.append(f'<path d="M{g.cx - 24} {yy + 12} L{g.cx} {yy - 4} L{g.cx + 24} {yy + 12}" stroke="{c["text"]}" '
                   f'stroke-width="5" fill="none" stroke-linejoin="miter" opacity="{0.9 - i * 0.25:.2f}"/>')
    out.append(text(g.cx, g.y(0.16), "RYSE", 22, c["text"], WIDE, 900, fit=g.w - 20, extra='force font-style="italic"'))
    out.append(text(g.cx, g.y(0.22), "FUEL", 7, a, WIDE, 900, extra='letter-spacing="4"'))
    out.append(f'<rect x="{g.x + 10}" y="{g.y(0.74)}" width="{g.w - 20}" height="25" rx="3" fill="{c["body"]}" opacity="0.85"/>')
    out.append(flavor_text(g, g.y(0.74) + 8, 6, c["text"], SANS, 900, maxlen=14, width=g.w - 26))
    out.append(text(g.cx, g.y(0.94), "ZERO SUGAR · 200MG", 4, c["text"], SANS, 700))
    return "".join(out)


def ART_ghost(g):
    c = g.c
    body = c["accent"]
    ink = c["text"]
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{body}"/>',
           f'<rect x="{g.x}" y="{g.y(0.06)}" width="{g.w}" height="22" fill="{ink}"/>',
           text(g.cx, g.y(0.06) + 17, "GHOST", 18, body, WIDE, 900, fit=g.w - 18, extra="force"),
           text(g.cx, g.y(0.22), "ENERGY", 7, ink, WIDE, 900, extra='letter-spacing="5"')]
    gx, gy = g.cx, g.y(0.5)
    out.append(f'<path d="M{gx - 22} {gy + 26} V{gy - 4} a22 22 0 0 1 44 0 V{gy + 26} '
               f'l-7.3 -6 -7.3 6 -7.3 -6 -7.3 6 -7.3 -6 z" fill="#fff" stroke="{ink}" stroke-width="3"/>')
    out.append(f'<ellipse cx="{gx - 8}" cy="{gy - 2}" rx="4" ry="6" fill="{ink}"/>'
               f'<ellipse cx="{gx + 8}" cy="{gy - 2}" rx="4" ry="6" fill="{ink}"/>')
    out.append(f'<rect x="{g.x}" y="{g.y(0.75)}" width="{g.w}" height="30" fill="#fff"/>')
    out.append(flavor_text(g, g.y(0.75) + 9, 6.5, ink, WIDE, 900, maxlen=14))
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
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>',
           f'<rect x="{g.x + 6}" y="{g.t}" width="7" height="{g.h}" fill="{a}"/>',
           f'<rect x="{g.r - 13}" y="{g.t}" width="7" height="{g.h}" fill="{a}"/>',
           f'<rect x="{g.x + 15}" y="{g.t}" width="2" height="{g.h}" fill="{a}" opacity="0.6"/>',
           f'<rect x="{g.r - 17}" y="{g.t}" width="2" height="{g.h}" fill="{a}" opacity="0.6"/>']
    cy = g.y(0.13)
    out.append(f'<path d="M{g.cx - 16} {cy + 8} L{g.cx - 16} {cy - 6} L{g.cx - 8} {cy + 1} L{g.cx} {cy - 10} '
               f'L{g.cx + 8} {cy + 1} L{g.cx + 16} {cy - 6} L{g.cx + 16} {cy + 8} Z" fill="{a}"/>')
    out.append(vtext(g.cx + 9, g.y(0.5), "REIGN", 26, c["text"], WIDE, 900, fit=g.h * 0.48, extra="force"))
    out.append(text(g.cx, g.y(0.84), "TOTAL BODY FUEL", 4.2, a, SANS, 800, extra='letter-spacing="1"'))
    out.append(flavor_text(g, g.y(0.91), 5.5, c["text"], SANS, 900, maxlen=14, width=g.w - 40))
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
    out = [f'<rect x="{g.x}" y="{g.t}" width="{g.w}" height="{g.h}" fill="{c["body"]}"/>']
    # camo blobs
    blobs = [(0.15, 0.1, 14, 8), (0.7, 0.05, 12, 7), (0.4, 0.3, 16, 9), (0.9, 0.35, 10, 8), (0.1, 0.5, 12, 10),
             (0.6, 0.6, 15, 8), (0.25, 0.8, 13, 9), (0.85, 0.85, 12, 7), (0.5, 0.95, 14, 6)]
    for i, (fx, fy, rx, ry) in enumerate(blobs):
        col = c["band"] if i % 2 else "#0b2e17"
        out.append(f'<ellipse cx="{g.x + g.w * fx:.1f}" cy="{g.y(fy):.1f}" rx="{rx}" ry="{ry}" fill="{col}" '
                   f'transform="rotate({(i * 37) % 60 - 30} {g.x + g.w * fx:.1f} {g.y(fy):.1f})"/>')
    # antlers
    def side(s):
        x = g.cx
        y = g.y(0.38)
        return (f'<path d="M{x + s * 4} {y} C{x + s * 10} {y - 14},{x + s * 22} {y - 18},{x + s * 30} {y - 34} '
                f'M{x + s * 15} {y - 14} L{x + s * 28} {y - 16} M{x + s * 22} {y - 22} L{x + s * 18} {y - 34} '
                f'M{x + s * 26} {y - 28} L{x + s * 36} {y - 30}" stroke="{a}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    out.append(side(1) + side(-1))
    out.append(f'<rect x="{g.x}" y="{g.y(0.44)}" width="{g.w}" height="34" fill="{c["accent2"]}"/>')
    out.append(text(g.cx, g.y(0.44) + 15, "BUCKED", 13, c["body"], WIDE, 900, fit=g.w - 16, extra="force"))
    out.append(text(g.cx, g.y(0.44) + 29, "UP", 13, a, WIDE, 900))
    out.append(f'<rect x="{g.x + 8}" y="{g.y(0.74)}" width="{g.w - 16}" height="22" rx="2" fill="{a}"/>')
    out.append(flavor_text(g, g.y(0.74) + 9, 6, ink(a), WIDE, 900, maxlen=13, width=g.w - 22))
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

def can_svg(brand, flavor=None):
    bid = brand["id"]
    flavor = flavor or brand.get("flavors", ["???"])[0]
    shape = BRAND_SHAPE.get(bid, "tall")
    g = G(brand, flavor, shape)
    art = globals().get(f"ART_{bid}", ART_generic)(g)
    x, r, cx, lid, t, b = g.x, g.r, g.cx, g.lid, g.t, g.b
    lrx = g.w / 2 - 6
    label = f"{brand['name']} {flavor} can, Second Wind art"
    u = f"{bid}-{slug(flavor)}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 220" width="120" height="220" role="img" aria-label="{esc(label)}">
  <defs>
    <linearGradient id="shade-{u}" x1="0" x2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0.38"/>
      <stop offset="0.18" stop-color="#fff" stop-opacity="0.22"/>
      <stop offset="0.32" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.75" stop-color="#000" stop-opacity="0.05"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.45"/>
    </linearGradient>
    <linearGradient id="metal-{u}" x1="0" x2="1">
      <stop offset="0" stop-color="#7c818a"/><stop offset="0.3" stop-color="#f1f3f5"/>
      <stop offset="0.65" stop-color="#b9bec6"/><stop offset="1" stop-color="#5f646d"/>
    </linearGradient>
    <clipPath id="body-{u}"><rect x="{x}" y="{t}" width="{g.w}" height="{g.h}"/></clipPath>
  </defs>
  <ellipse cx="{cx}" cy="{b + 14}" rx="{g.w / 2 + 2}" ry="4" fill="#000" opacity="0.2"/>
  <path d="M{x + 6} {lid + 2} L{r - 6} {lid + 2} L{r} {t} L{x} {t} Z" fill="url(#metal-{u})"/>
  <ellipse cx="{cx}" cy="{lid + 2}" rx="{lrx}" ry="4" fill="#dfe2e6" stroke="#8f959d" stroke-width="1"/>
  <ellipse cx="{cx}" cy="{lid + 2}" rx="{lrx - 3}" ry="2.6" fill="none" stroke="#b3b8bf" stroke-width="0.8"/>
  <path d="M{cx - 3} {lid + 0.5} h10 a2.2 2.2 0 0 1 0 4.4 h-10 z" fill="#a6abb3" stroke="#8a9098" stroke-width="0.6"/>
  <g clip-path="url(#body-{u})">
    {art}
    <rect x="{x}" y="{t}" width="{g.w}" height="{g.h}" fill="url(#shade-{u})"/>
  </g>
  <path d="M{x} {b} L{r} {b} L{r - 5} {b + 9} Q{cx} {b + 13} {x + 5} {b + 9} Z" fill="url(#metal-{u})"/>
</svg>
'''
