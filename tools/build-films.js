#!/usr/bin/env node
/*
  Films from the Land - static generator.

  Reads data/films.json and:
    1. Regenerates the film cards in films.html between the
       <!-- FILMS:START --> and <!-- FILMS:END --> markers, newest first.
    2. Writes one share page per film at f/<slug>.html with OG tags
       that use the film's YouTube thumbnail, so a single short link
       can be forwarded and previews correctly.

  Adding a film never touches HTML: edit data/films.json, then run
      npm run build:films
  (Netlify runs the same command on every deploy, so pushing
  films.json republishes everything.)
*/

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SITE = 'https://pray-the-land-golan.netlify.app';
const WHATSAPP = 'https://wa.me/972544442054?text=Tai%2C%20I%20am%20sending%20you%20my%20film%20from%20my%20side%20of%20the%20wall';

function fail(msg) {
  console.error('build:films FAILED: ' + msg);
  process.exit(1);
}

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ---------- load and validate ---------- */

const jsonPath = path.join(ROOT, 'data', 'films.json');
let films;
try {
  films = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
} catch (e) {
  fail('cannot read or parse data/films.json: ' + e.message);
}
if (!Array.isArray(films) || films.length === 0) fail('data/films.json must be a non-empty array');

const REQUIRED = ['num', 'slug', 'title', 'place', 'youtube_id', 'desc', 'date'];
const seenSlugs = new Set();
for (const f of films) {
  for (const k of REQUIRED) {
    if (typeof f[k] !== 'string' || f[k].trim() === '') fail(`film "${f.slug || f.title || '?'}" is missing "${k}"`);
  }
  if (!/^[a-z0-9-]+$/.test(f.slug)) fail(`slug "${f.slug}" may only contain lowercase letters, digits and hyphens`);
  if (!/^[A-Za-z0-9_-]{6,}$/.test(f.youtube_id)) fail(`"${f.youtube_id}" does not look like a YouTube video id`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(f.date)) fail(`date "${f.date}" must be YYYY-MM-DD`);
  if (seenSlugs.has(f.slug)) fail(`duplicate slug "${f.slug}"`);
  seenSlugs.add(f.slug);
}

/* newest first */
films.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

/* ---------- film cards in films.html ---------- */

function cardHtml(f) {
  const descHtml = f.desc.split('\n').map(esc).join('<br>');
  return `    <article class="film-card">
      <div class="frame">
        <iframe src="https://www.youtube-nocookie.com/embed/${esc(f.youtube_id)}" title="Film ${esc(f.num)} · ${esc(f.title)}"
          loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
      </div>
      <div class="film-meta">
        <div class="k">Film ${esc(f.num)} &middot; ${esc(f.place)}</div>
        <h3>${esc(f.title)}</h3>
        <p>${descHtml}</p>
        <p class="share"><a href="/f/${esc(f.slug)}.html">Share this film &rarr;</a></p>
      </div>
    </article>`;
}

const filmsPagePath = path.join(ROOT, 'films.html');
let page = fs.readFileSync(filmsPagePath, 'utf8');
const START = '<!-- FILMS:START -->';
const END = '<!-- FILMS:END -->';
const startIdx = page.indexOf(START);
const endIdx = page.indexOf(END);
if (startIdx === -1 || endIdx === -1 || endIdx < startIdx) fail('films.html is missing the FILMS:START / FILMS:END markers');

const generated = `${START}
    <!-- Generated from data/films.json by tools/build-films.js. Do not edit
         this section by hand: edit data/films.json, then run npm run build:films -->

${films.map(cardHtml).join('\n\n')}

    ${END}`;

page = page.slice(0, startIdx) + generated + page.slice(endIdx + END.length);
fs.writeFileSync(filmsPagePath, page);
console.log(`films.html: wrote ${films.length} film card(s)`);

/* ---------- share pages ---------- */

function sharePageHtml(f) {
  const title = `${f.title} · Films from the Land`;
  const descLines = f.desc.split('\n');
  const descText = descLines.join(' ');
  const descHtml = descLines.map(esc).join('<br>');
  const url = `${SITE}/f/${f.slug}.html`;
  const thumb = `https://img.youtube.com/vi/${f.youtube_id}/maxresdefault.jpg`;
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(descText)}">

<link rel="canonical" href="${esc(url)}">
<meta property="og:type" content="video.other">
<meta property="og:url" content="${esc(url)}">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(descText)}">
<meta property="og:image" content="${esc(thumb)}">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="720">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(descText)}">
<meta name="twitter:image" content="${esc(thumb)}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Frank+Ruhl+Libre:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{
    --basalt:#15110D; --basalt-2:#211C17;
    --parchment:#FAF6EC; --parchment-dim:#E8DEC6;
    --gold:#C9A227; --gold-soft:#D9B23F; --gold-deep:#7a6420;
    --ink:#221e19; --warm-white:#EAE2CE; --muted:#b3a890;
    --display:'Cormorant Garamond',Georgia,serif;
    --body:'Frank Ruhl Libre',Georgia,serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--body);background:var(--basalt);color:var(--parchment-dim);line-height:1.75;-webkit-font-smoothing:antialiased}
  .eyebrow{font-size:12px;letter-spacing:.32em;text-transform:uppercase;font-weight:700;color:var(--gold)}
  a{color:inherit}

  nav{position:sticky;top:0;z-index:50;display:flex;justify-content:space-between;align-items:center;
    padding:14px clamp(20px,5vw,52px);background:rgba(21,17,13,.94);border-bottom:1px solid #3a322a;backdrop-filter:blur(8px)}
  nav .brand{font-family:var(--display);font-size:21px;color:var(--warm-white);letter-spacing:.02em;text-decoration:none}
  nav .brand span{color:var(--gold)}
  nav .back{color:var(--parchment-dim);text-decoration:none;font-size:13.5px;letter-spacing:.04em}
  nav .back:hover{color:var(--gold)}

  main{max-width:760px;margin:0 auto;padding:clamp(40px,7vw,72px) clamp(20px,5vw,40px) clamp(56px,8vw,90px);text-align:center}
  h1{font-family:var(--display);font-weight:500;font-size:clamp(34px,6.5vw,58px);line-height:1.1;color:var(--warm-white);margin:14px 0 6px}
  .place{font-family:var(--display);font-style:italic;font-size:clamp(18px,2.6vw,24px);color:var(--parchment-dim)}
  .frame{position:relative;aspect-ratio:16/9;background:#0f0c08;border:1px solid #3a322a;border-radius:3px;overflow:hidden;margin:34px 0 26px}
  .frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
  .desc{color:var(--muted);font-size:clamp(16px,1.8vw,18px);line-height:1.9}
  .allfilms{display:inline-block;margin-top:22px;color:var(--gold);text-decoration:none;font-weight:700;font-size:14px;letter-spacing:.04em}
  .allfilms:hover{text-decoration:underline}

  .btn{font-family:var(--body);font-weight:700;font-size:14px;letter-spacing:.06em;text-decoration:none;
    padding:15px 30px;border-radius:2px;display:inline-block;transition:transform .2s ease,background .2s ease}
  .btn-gold{background:var(--gold);color:var(--basalt)}
  .btn-gold:hover{transform:translateY(-2px);background:var(--gold-soft)}

  .reply{margin-top:clamp(44px,6vw,64px);border-top:1px solid #3a322a;padding-top:clamp(38px,5vw,54px)}
  .reply h2{font-family:var(--display);font-weight:500;font-size:clamp(24px,3.6vw,34px);color:var(--warm-white)}
  .reply p{max-width:520px;margin:16px auto 0;color:var(--muted)}
  .reply .btn{margin-top:26px}

  .stand{margin-top:clamp(44px,6vw,64px);border-top:1px solid #3a322a;padding-top:clamp(38px,5vw,54px)}
  .stand h2{font-family:var(--display);font-weight:500;font-size:clamp(24px,3.6vw,34px);color:var(--warm-white)}
  .stand p{max-width:520px;margin:16px auto 0;color:var(--muted)}
  .stones{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:480px;margin:30px auto 0}
  .stone{display:block;border:1px solid #4a4133;background:var(--basalt-2);border-radius:3px;
    padding:18px 10px;text-decoration:none;transition:border-color .25s,transform .25s}
  .stone:hover{border-color:var(--gold);transform:translateY(-3px)}
  .stone .amt{display:block;font-family:var(--display);font-size:26px;line-height:1.2;color:var(--warm-white)}
  .stone .nm{display:block;font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);font-weight:700;margin-top:5px}
  .anyamt{margin-top:22px;font-size:14.5px;color:var(--muted)}
  .anyamt a{color:var(--gold);text-decoration:none;font-weight:700}
  .anyamt a:hover{text-decoration:underline}

  footer{border-top:1px solid #3a322a;color:var(--parchment-dim);text-align:center;padding:52px 24px 46px}
  footer .word{font-family:var(--display);font-style:italic;font-size:clamp(20px,3vw,26px);color:var(--warm-white);line-height:1.6}
  footer .rule{width:90px;height:2px;background:var(--gold);margin:24px auto}
  footer .sig{font-size:12px;letter-spacing:.16em;color:var(--muted);line-height:2.1}
  footer a{color:var(--gold);text-decoration:none}

  @media(max-width:480px){
    .btn{display:block;width:100%;text-align:center}
    .stones{grid-template-columns:1fr;max-width:280px}
  }
  @media (prefers-reduced-motion: reduce){
    *{animation:none!important;transition:none!important}
  }
</style>
</head>
<body>

<nav>
  <a class="brand" href="/">Pray the <span>Land</span></a>
  <a class="back" href="/films.html">All the films &rarr;</a>
</nav>

<main>
  <div class="eyebrow">Pray the Land &middot; Film ${esc(f.num)} &middot; ${esc(f.place)}</div>
  <h1>${esc(f.title)}</h1>
  <div class="place">A film from the Land, filmed where it happened</div>

  <div class="frame">
    <iframe src="https://www.youtube-nocookie.com/embed/${esc(f.youtube_id)}" title="Film ${esc(f.num)} · ${esc(f.title)}"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
  </div>

  <p class="desc">${descHtml}</p>
  <a class="allfilms" href="/films.html">Watch all the films &rarr;</a>

  <div class="reply">
    <h2>Send me your film from your side of the wall</h2>
    <p>One minute on your phone is enough.<br>Where you pray from, what you see, one verse if you like.<br>I watch every one of them personally.</p>
    <a class="btn btn-gold" href="${WHATSAPP}">Reply with your film on WhatsApp</a>
  </div>

  <div class="stand">
    <h2>Stand with the Land</h2>
    <p>The films are free and they stay free.<br>If your heart moves you to stand with the Land and this work, lay a stone.</p>
    <div class="stones">
      <a class="stone" href="https://paypal.me/amitaielon/18"><span class="amt">$18</span><span class="nm">Chai</span></a>
      <a class="stone" href="https://paypal.me/amitaielon/50"><span class="amt">$50</span><span class="nm">Stone</span></a>
      <a class="stone" href="https://paypal.me/amitaielon/120"><span class="amt">$120</span><span class="nm">Film</span></a>
    </div>
    <p class="anyamt">Or give any amount at <a href="https://paypal.me/amitaielon">paypal.me/amitaielon</a></p>
  </div>
</main>

<footer>
  <div class="word">The covenant holds.<br>The gates shall not prevail.</div>
  <div class="rule"></div>
  <div class="sig">
    WITH LOVE, AND WITH FAITH<br><br>
    AMITAI (TAI) ELON &middot; NATUR FARM<br>GOLAN HEIGHTS, ISRAEL<br>
    <a href="https://wa.me/972544442054">WhatsApp +972&middot;54&middot;444&middot;2054</a> &middot; <a href="mailto:amitai.elon@gmail.com">amitai.elon@gmail.com</a>
  </div>
</footer>

</body>
</html>
`;
}

const outDir = path.join(ROOT, 'f');
fs.mkdirSync(outDir, { recursive: true });
for (const f of films) {
  fs.writeFileSync(path.join(outDir, f.slug + '.html'), sharePageHtml(f));
  console.log(`f/${f.slug}.html: written`);
}

/* remove share pages for films no longer in films.json */
for (const existing of fs.readdirSync(outDir)) {
  if (existing.endsWith('.html') && !seenSlugs.has(existing.replace(/\.html$/, ''))) {
    fs.unlinkSync(path.join(outDir, existing));
    console.log(`f/${existing}: removed (no longer in films.json)`);
  }
}

console.log('build:films OK');
