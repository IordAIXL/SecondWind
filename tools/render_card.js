// Render the link-preview card (X / social) to PNG.
// Usage: node tools/render_card.js <card.html> <out.png>
const path = require("path");
const { chromium } = require("playwright");
const [src, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 675 }, deviceScaleFactor: 1 });
  await page.goto("file://" + path.resolve(src));
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: out });
  await browser.close();
})();
