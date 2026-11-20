// Renders wood-look previews of the coaster SVGs. Usage: node tools/render_preview.js
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const root = path.join(__dirname, '..'), dir = path.join(root, 'coasters/kearney');
const svg = n => fs.readFileSync(path.join(n.includes('/') ? path.join(root, 'coasters') : dir, n), 'utf8');
const coaster = (n, round) => `<div class="c ${round ? 'r' : ''}">${svg(n)}</div>`;
const css = `
body{margin:0;background:#2b2f33;font:600 15px Inter,sans-serif;color:#cfd3d6}
.wrap{padding:36px;display:inline-block}
.row{display:flex;gap:36px;align-items:flex-start}
figure{margin:0;text-align:center} figcaption{margin-top:14px;letter-spacing:.08em}
.c{width:420px;height:420px;border-radius:34px;position:relative;overflow:hidden;
 background:repeating-linear-gradient(92deg,rgba(120,80,30,.10) 0 3px,rgba(255,255,255,.05) 3px 7px,rgba(120,80,30,.06) 7px 13px),
 linear-gradient(100deg,#e6c998,#dcb983 45%,#e8cfa0);
 box-shadow:0 10px 24px rgba(0,0,0,.55), inset 0 0 0 2px #6b4420}
.c.r{border-radius:50%}
.c svg{width:100%;height:100%;display:block}
.c svg #engrave path{fill:#4a2a10}
[id=engrave-navy] path{fill:#3d210b}
[id=engrave-orange] path{fill:#7a4a1f}
[id=engrave-aqua] path{fill:#b08552}
.c svg #score path{stroke:#5a3414;stroke-width:.22}
.c svg #cut{display:none}
.grid{display:grid;grid-template-columns:420px 420px;gap:5px}
`;
const logoRow = d => `<div class="row">
    <figure>${coaster(d + '/round_engrave.svg', 1)}<figcaption>ROUND · LOGO ENGRAVED</figcaption></figure>
    <figure>${coaster(d + '/square_engrave.svg')}<figcaption>SQUARE · LOGO ENGRAVED</figcaption></figure>
    <figure>${coaster(d + '/round_inverted.svg', 1)}<figcaption>ROUND · BACKGROUND ENGRAVED</figcaption></figure>
    <figure>${coaster(d + '/square_inverted.svg')}<figcaption>SQUARE · BACKGROUND ENGRAVED</figcaption></figure></div>`;
const pages = {
  'baylor_coasters.png': logoRow('baylor'),
  'dolphins_coasters.png': `<div class="row">
    <figure>${coaster('dolphins/round_skyline.svg', 1)}<figcaption>ROUND · THREE-TONE ENGRAVE</figcaption></figure>
    <figure>${coaster('dolphins/square_skyline.svg')}<figcaption>SQUARE · THREE-TONE ENGRAVE</figcaption></figure></div>`,
  'lopers_coasters.png': `<div class="row">
    <figure>${coaster('lopers/round_engrave.svg', 1)}<figcaption>ROUND · LOGO ENGRAVED</figcaption></figure>
    <figure>${coaster('lopers/square_engrave.svg')}<figcaption>SQUARE · LOGO ENGRAVED</figcaption></figure>
    <figure>${coaster('lopers/round_inverted.svg', 1)}<figcaption>ROUND · BACKGROUND ENGRAVED</figcaption></figure>
    <figure>${coaster('lopers/square_inverted.svg')}<figcaption>SQUARE · BACKGROUND ENGRAVED</figcaption></figure></div>`,
  'kearney_single_coasters.png': `<div class="row">
    <figure>${coaster('round_engrave.svg', 1)}<figcaption>ROUND · ENGRAVED</figcaption></figure>
    <figure>${coaster('square_engrave.svg')}<figcaption>SQUARE · ENGRAVED</figcaption></figure>
    <figure>${coaster('round_score.svg', 1)}<figcaption>ROUND · SCORED (FAST)</figcaption></figure></div>`,
  'kearney_set_of_4.png': `<figure><div class="grid">${['1_NW', '2_NE', '3_SW', '4_SE'].map(t => coaster(`set4_${t}_engrave.svg`)).join('')}</div>
    <figcaption>SET OF 4 · ONE MAP ACROSS FOUR COASTERS</figcaption></figure>`,
};
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 2, viewport: { width: 2000, height: 1000 } });
  for (const [name, body] of Object.entries(pages)) {
    await p.setContent(`<style>${css}</style><div class="wrap">${body}</div>`);
    await (await p.$('.wrap')).screenshot({ path: path.join(root, 'previews', name) });
  }
  await b.close();
})();
