# Microsoft Store listing: Second Wind

Paste these into Partner Center > your app > Store listings > English.

## Product name
Second Wind

## Short description (Store "Short description", up to 270 characters)
Hand your AI a pretend energy drink from any chat app. Pick a can, it's pasted into the chat, and your AI refocuses: goal, done, left, and the one next step.

## Description
Is your AI chat wandering off? Hand it an energy drink.

Second Wind sits in your tray with a small floating can. In ChatGPT, Claude, Copilot or any other chat app, press Ctrl+Alt+D (or click the can), pick a drink, and Second Wind pastes it right into the chat box. Your AI cracks it open, then prints a short DIALED IN check: the goal, what's done, what's left, what to drop, and the one next step. Then it gets back to work.

It's just for fun, and it works surprisingly well.

- 16 energy drink brands and 179 flavors, each with its own work mode (Sprint, Deep Focus, Heavy Burst and more)
- Make up your own flavor
- Star your favorites. Your first star is "your usual": Ctrl+Alt+U hands it over instantly
- Drag the floating can anywhere on screen. It never steals focus from your chat
- "Send right away" option, lifetime drink counter, start with Windows
- No account, no ads, no tracking. Nothing leaves your PC

Second Wind is a fan-made, just-for-fun app. It isn't affiliated with or endorsed by any drink brand or AI company. Brand names are used only to describe the pretend drinks.

## What's new in this version
First release in the Microsoft Store.

## Features (one per line, up to 20)
Hand your AI a pretend energy drink from any chat app
Ctrl+Alt+D drink picker, Ctrl+Alt+U for your usual
Pastes straight into the chat box you were using
16 brands, 179 flavors, each with its own work mode
Favorites and "your usual"
Floating can you can drag anywhere
DIALED IN focus check: goal, done, left, next step
No account, no tracking

## Search terms (up to 7)
AI, ChatGPT, Claude, Copilot, energy drink, focus, productivity

## Category
Productivity (or Entertainment)

## Privacy policy URL
https://iordaixl.github.io/energizer/privacy.html

## Website
https://iordaixl.github.io/energizer/

## Screenshots (Desktop, 1920x1080)
screenshot-1-pick.png, screenshot-2-dialed.png, screenshot-3-flavors.png, screenshot-4-usual.png

## Submission options > Restricted capabilities (why the app needs "runFullTrust")
Second Wind is a classic Windows desktop (WinForms) app packaged as MSIX. It needs full trust to register its global hotkeys (Ctrl+Alt+D, Ctrl+Alt+U), show its always-on-top floating button, and paste the drink message into the chat app the user was using (clipboard + Ctrl+V). It collects no data and makes no network requests.

## Notes for certification
Second Wind runs in the system tray (lightning-can icon) and shows a floating round can button. The first launch opens the drink picker in the middle of the screen. To test: open Notepad, click into it, press Ctrl+Alt+D, and click any can (or a brand, then a flavor). The drink message is pasted into Notepad. Ctrl+Alt+U pastes "the usual". Right-click the tray icon or floating can for the menu. No account or sign-in is needed.
