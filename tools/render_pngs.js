// Render can SVGs to PNGs for the Windows desktop app (WinForms can't draw SVG).
// Usage: node tools/render_pngs.js <svg root> <png root> <height px>
// Only re-renders a PNG when its SVG is newer.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const [src, dst, hArg] = process.argv.slice(2);
const H = parseInt(hArg || "160", 10);
const W = Math.round(H * 120 / 220);

function walk(dir) {
  let out = [];
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) out = out.concat(walk(p));
    else if (f.endsWith(".svg")) out.push(p);
  }
  return out;
}

(async () => {
  const todo = walk(src).filter((svg) => {
    const png = path.join(dst, path.relative(src, svg)).replace(/\.svg$/, ".png");
    return !fs.existsSync(png) || fs.statSync(png).mtimeMs < fs.statSync(svg).mtimeMs;
  });
  if (!todo.length) { console.log("PNGs up to date"); return; }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  for (const svg of todo) {
    const png = path.join(dst, path.relative(src, svg)).replace(/\.svg$/, ".png");
    fs.mkdirSync(path.dirname(png), { recursive: true });
    const data = fs.readFileSync(svg, "utf8");
    await page.setContent(`<html><body style="margin:0;background:transparent">
      <img style="width:${W}px;height:${H}px;display:block" src="data:image/svg+xml;base64,${Buffer.from(data).toString("base64")}"></body></html>`);
    await page.waitForFunction(() => document.images[0].complete);
    await page.screenshot({ path: png, omitBackground: true });
  }
  await browser.close();
  console.log(`Rendered ${todo.length} PNGs`);
})();
