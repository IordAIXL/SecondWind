# Changelog

## 1.10.0 (2026-11-21)

- New Windows desktop helper (`desktop/`, download `docs/downloads/second-wind-desktop.zip`). Works with the ChatGPT, Claude, Copilot and other desktop apps. Nothing to install: it runs on the Windows PowerShell every PC already has.
  - A floating can you can drag anywhere on screen. It remembers its spot and never steals focus from your chat app.
  - Click the can or press Ctrl+Alt+D to pick a drink; Ctrl+Alt+U hands over your usual instantly. The drink is pasted into the chat box you were using (your clipboard is put back afterwards).
  - Tray menu with your usual, your favorites, Send right away, Start with Windows and Quit.
- Favorites and a one-click "usual" everywhere. Star any flavor (or a made-up one); the first star is your usual.
  - Browser button: favorites row at the top of the picker, a "My usual" button, and a "One-click usual" switch so clicking the can hands it over right away (right-click or the little arrow opens the menu).
  - Desktop helper: right-click a can to star it or make it your usual.
- Drag the browser can button anywhere. It remembers its spot on each site; "Snap back" puts it next to the chat box again.
- Drink messages use each brand's own mode and work style when the brand data has one (from the per-brand purpose update).
- Claude Desktop skill: `docs/downloads/second-wind-skill.zip`, upload it in Claude under Settings, Capabilities, Skills.
- Download page: new "Desktop apps" tab with the Windows download, the skill and install steps.

## 1.8.0 (2026-11-21)

- Fixed: typing `/secondwind` in Claude Code loaded an empty command, so Claude improvised instead of following Second Wind. The cause was a permissions line in the command file. Only the long name `/second-wind:secondwind` worked.
- The command is now a Claude Code skill (the current format). `/secondwind` works directly after install.
- The counter is saved with Claude's Read and Write tools only, so there are no permission pop-ups for a shell command.
- Install steps on the README and download page now include reloading plugins, the long-name fallback, and how to update an older install.

## 1.7.0 (2026-11-21)

- New browser button (a Chrome, Edge and Firefox extension in `extension/`). It puts a can button right above the chat box on ChatGPT, Claude, Gemini, Grok, Copilot, Perplexity, DeepSeek, Mistral, Meta AI, Poe and Google AI Studio.
- Click the can to open a picker with every brand and flavor can. Pick one (or make up a flavor, or hit Surprise me) and a drink message with the "dialed in" block goes into the chat box. No prompt setup needed on the AI's side.
- Optional "Send right away", a lifetime can counter, the button shows your last can, and "Hide here" for any site.
- Download page: new "Browser button" tab in Pick your AI with a one-click download and install steps. The zip lives at `docs/downloads/second-wind-extension.zip`.
- `tools/build.py` now also builds the extension and its zip.

## 1.6.0 (2026-11-21)

- New "Pick your AI" chooser on the download page. Tap Claude Code, ChatGPT, Codex, Grok, Gemini or Other AI to see only the steps for that one.
- One-click button copies the full prompt for each AI, so nobody has to dig through GitHub.
- The page remembers your pick, and links like #get-chatgpt open straight to that AI.
- Phone fixes: the step lists wrap cleanly and the hero cans no longer cause sideways scrolling.

## 1.5.0 (2026-11-21)

- Flavor audit: every brand's flavor list was checked against current lineups online (179 flavors now). Discontinued flavors are gone and new ones are in, each with its own can colors.
  - Red Bull: added Apple, Iced and Pink Editions; dropped Blueberry and Dragon Fruit.
  - Monster: added Ultra Peachy Keen, Ultra Strawberry Dreams, Ultra Blue Hawaiian; dropped Ultra Blue and Khaotic.
  - Celsius: added 9 current flavors (Mango Lemonade, Fuji Apple Pear, Dragon Fruit Lime, Astro, Oasis, Playa and Cosmic Vibe, and more).
  - Ryse: current Fuel lineup (Cream Soda, Frosted Lemonade, White Mystery Airheads, Root Beer Float, Firecracker Popsicle, Cotton Candy, Sour Punch Blue Raspberry).
  - Ghost: added Warheads Sour Green Apple, Sour Strips Rainbow, Sour Pink Lemonade, 7UP, A&W Root Beer; FaZe Pop is now 'Merica Pop.
  - Bang: current lineup incl. Delish Strawberry Kiss, Candy Apple Crisp, Wyldin' Watermelon, Lime Pop Drop, American Berry.
  - Reign: 17 current flavors incl. Sour Gummy Worm, Peach Fizz, Watermelon Sour Gummy; dropped Red Dragon.
  - C4: current Performance lineup (Jolly Rancher, Popsicle and more).
  - Alani Nu: added Dream Float, Watermelon Wave, Orange Kiss, Blue, Pink and Lime Slush, Strawberry Sunrise.
  - Prime: added Original, Cherry Limeade, Dripsicle; dropped Grape.
  - Rockstar, 3D, Bucked Up and Zoa updated to their current lineups.
- New download page: a hero with cans, a "How it works" section, search that jumps to the matching flavor, one-click copy for every command, and flavor-aware commands.
- README rewritten: cover image of every can, cleaner install steps, and a full menu table that is generated from the data.

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
