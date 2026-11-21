# Changelog

## 1.4.2 (2026-11-21)

- Better lettering on every can. Text is now drawn from real display fonts and baked into the art, so it looks the same on every phone and computer.
- Redid Ryse again: bold RYSE logo, big slanted FUEL, slanted flavor ribbon.
- Redid Ghost again: big GHOST wordmark, large ghost logo, flavor in a white sticker.
- New lettering on Reign: sharp REIGN letters, a crown with gems, condensed flavor text.

## 1.3.0 (2026-11-21)

- Can audit against the real brands. Redid four cans that didn't look right:
  - Ryse: full flavor-colored can, big slanted FUEL lettering, logo at the top.
  - Ghost: flavor-colored can with the ghost badge, GHOST wordmark and big ENERGY lettering.
  - Reign: flavor-colored can (was black), crown on top, big REIGN lettering.
  - Bucked Up: flavor-colored can with a deer head and a black name band (was camo).

## 1.2.0 (2026-11-21)

- More realistic cans: shiny aluminum shading and highlights, curved can bodies, real tops with rims and pull tabs, tapered bottoms and a soft floor shadow.
- Every can now shows its real size (16 FL OZ, 12 FL OZ, 8.4 FL OZ or 11 FL OZ).
- Closer brand detail: torn claw marks on Monster, charging bulls on Red Bull.

## 1.1.0 (2026-11-21)

- New can art for every brand, styled after each real can: colors, layout and look.
- Real can sizes: big 16 oz cans for Monster, Bang, Ghost and friends; skinny 12 oz cans for Celsius, Alani Nu, Zoa, Prime and Tea; a small slim can for Red Bull; a short cold brew can for Coffee.
- Real flavor lineups for every brand (142 flavors in all).
- Every flavor has its own can in that flavor's colors (docs/cans/<brand>/<flavor>.svg).
- Download page: tap the colored dots under a can to see each flavor.
- Can art now lives in tools/cans.py, one function per brand, so any can is easy to swap.

## 1.0.0 (2026-11-21)

- First release.
- Claude Code plugin with `/secondwind`, `/secondwind <brand> <flavor>`, `/secondwind menu` and `/secondwind stats`.
- 16 brands plus a Mystery Can for anything made up. Fun surprised reaction for unknown flavors.
- Lifetime drink counter with milestone celebrations.
- "Dialed in" focus block after every drink: goal, done, left, dropping, next step.
- Original SVG can art for every brand.
- Prompts for ChatGPT, Codex (AGENTS.md), Grok, Gemini and any other AI.
- Download page at docs/index.html.
