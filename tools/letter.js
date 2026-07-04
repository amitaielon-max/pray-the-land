#!/usr/bin/env node
/*
  Broadcast letter generator.

      npm run letter -- <slug>

  Reads the film with that slug from data/films.json and writes
      letters-out/<slug>.letter.txt
      letters-out/<slug>.letter.html
  as a paste-ready email pair. The generator scaffolds; Tai's heart
  writes the opening lines at the TODO markers.

  letters-out/ is gitignored: letters are personal mail, not site pages.

  Optional per-film fields in films.json used here if present:
      "verse":     "Behold, He who keeps Israel will neither slumber nor sleep."
      "verse_ref": "Tehillim (Psalms) 121:4"
      "verse_heb": "..."
*/

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SITE = 'https://pray-the-land-golan.netlify.app';
const WHATSAPP = 'https://wa.me/972544442054?text=Tai%2C%20I%20am%20sending%20you%20my%20film%20from%20my%20side%20of%20the%20wall';
const STAND = SITE + '/stand.html';
const ARCHIVE_DOC = 'https://docs.google.com/document/d/1_7eyKES7ao1WXBRgl3D6r_cZxqASAzdQooTard0ws9M/edit';
const KEEPSAKE_PDF = 'https://drive.google.com/file/d/1mo7jSzcwB6b19mz0s7tDS9RsDkFIRQpO/view';

function fail(msg) {
  console.error('letter FAILED: ' + msg);
  process.exit(1);
}

const slug = (process.argv[2] || '').trim();
if (!slug) fail('usage: npm run letter -- <slug>   (slugs live in data/films.json)');

let films;
try {
  films = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'films.json'), 'utf8'));
} catch (e) {
  fail('cannot read data/films.json: ' + e.message);
}
const film = films.find((f) => f.slug === slug);
if (!film) fail(`no film with slug "${slug}". Known slugs: ${films.map((f) => f.slug).join(', ')}`);

const shareUrl = `${SITE}/f/${film.slug}.html`;
const descLines = String(film.desc).split('\n');

const TODO_OPENING = [
  '[TODO: your opening. Six short lines from your week and your heart.]',
  '[TODO: line two]',
  '[TODO: line three]',
  '[TODO: line four]',
  '[TODO: line five]',
  '[TODO: line six]',
];

/* ---------- plain text ---------- */

const txtVerse = film.verse
  ? [`"${film.verse}"`, film.verse_ref || '', film.verse_heb || ''].filter(Boolean)
  : ['[TODO: one verse for this film, with its Hebrew book name, or delete these two lines]', '[TODO: verse reference]'];

const txt = [
  'Pray the Land · from the Golan',
  `Film ${film.num} · ${film.title}`,
  '',
  ...TODO_OPENING,
  '',
  'There is a new film from the Land.',
  `Film ${film.num}. ${film.title}. Filmed in ${film.place}, where it happened.`,
  '',
  ...descLines,
  '',
  'Watch it here, in your own time:',
  shareUrl,
  '',
  'The films are free.',
  'They stay free.',
  '',
  ...txtVerse,
  '',
  'When you have watched, answer from your side of the wall.',
  'One minute on your phone is enough.',
  'Send me your film here:',
  WHATSAPP,
  '',
  'I watch every one personally.',
  '',
  `If your heart moves you to stand with the Land, you can lay a stone here: ${STAND}`,
  '',
  'Amitai (Tai) Elon',
  'Natur Farm, Golan Heights',
  'WhatsApp +972-54-444-2054',
  '',
  `The site: ${SITE}`,
  `The book of the letters: ${ARCHIVE_DOC}`,
  `The keepsake: ${KEEPSAKE_PDF}`,
  '',
].join('\n');

/* ---------- html (table based, email client safe, max width 600) ---------- */

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const NAVY = '#14213d';
const GOLD = '#C9A227';
const GOLD_DEEP = '#8a6a16';
const CREAM = '#fdfcf8';
const PANEL = '#EFE7CC';
const PANEL_INK = '#2b2410';
const INK = '#2b2a26';

function p(text, extra) {
  return `<p style="margin:0 0 14px;font-family:Georgia,serif;font-size:16px;line-height:1.8;color:${INK};${extra || ''}">${text}</p>`;
}

function goldPanel(innerHtml) {
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0">
  <tr><td style="background:${PANEL};border:2px solid ${GOLD};padding:22px 26px;text-align:center">
    ${innerHtml}
  </td></tr>
</table>`;
}

function button(href, label) {
  return `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px auto">
  <tr><td style="background:${GOLD};border-radius:2px">
    <a href="${esc(href)}" style="display:inline-block;padding:14px 30px;font-family:Georgia,serif;font-size:15px;font-weight:bold;color:${NAVY};text-decoration:none">${label}</a>
  </td></tr>
</table>`;
}

const htmlVerse = film.verse
  ? goldPanel(
      `<p style="margin:0;font-family:Georgia,serif;font-style:italic;font-size:18px;line-height:1.7;color:${PANEL_INK}">&ldquo;${esc(film.verse)}&rdquo;</p>` +
      (film.verse_ref ? `<p style="margin:12px 0 0;font-family:Georgia,serif;font-size:12px;letter-spacing:2px;color:${GOLD_DEEP};text-transform:uppercase">${esc(film.verse_ref)}</p>` : '') +
      (film.verse_heb ? `<p dir="rtl" style="margin:8px 0 0;font-family:Georgia,serif;font-style:italic;font-size:17px;color:${PANEL_INK}">${esc(film.verse_heb)}</p>` : '')
    )
  : goldPanel(
      `<p style="margin:0;font-family:Georgia,serif;font-style:italic;font-size:16px;line-height:1.7;color:${PANEL_INK}">[TODO: one verse for this film, with its Hebrew book name, or delete this panel]</p>`
    );

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Film ${esc(film.num)} · ${esc(film.title)} · Pray the Land</title>
</head>
<body style="margin:0;padding:0;background:${CREAM}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${CREAM}">
<tr><td align="center" style="padding:26px 12px">

<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">

  <tr><td style="background:${NAVY};padding:30px 34px;text-align:center">
    <p style="margin:0;font-family:Georgia,serif;font-size:12px;letter-spacing:4px;color:${GOLD};text-transform:uppercase">Pray the Land &middot; from the Golan</p>
    <p style="margin:14px 0 0;font-family:Georgia,serif;font-size:30px;line-height:1.2;color:${CREAM}">${esc(film.title)}</p>
    <p style="margin:10px 0 0;font-family:Georgia,serif;font-style:italic;font-size:15px;color:#cfc4a6">Film ${esc(film.num)} &middot; ${esc(film.place)}</p>
  </td></tr>

  <tr><td style="height:3px;background:${GOLD};font-size:0;line-height:0">&nbsp;</td></tr>

  <tr><td style="padding:34px 34px 10px">
    ${TODO_OPENING.map((l) => p(esc(l), `background:#fdf6da;`)).join('\n    ')}
  </td></tr>

  <tr><td style="padding:6px 34px 0">
    ${p('There is a new film from the Land.')}
    ${p(`Film ${esc(film.num)}. ${esc(film.title)}. Filmed in ${esc(film.place)}, where it happened.`)}
    ${descLines.map((l) => p(esc(l))).join('\n    ')}
    ${p('Watch it in your own time. The films are free. They stay free.')}
    ${button(shareUrl, 'Watch the film')}
    ${p(`Or open this link: <a href="${esc(shareUrl)}" style="color:${GOLD_DEEP}">${esc(shareUrl)}</a>`, 'font-size:14px;text-align:center;')}
  </td></tr>

  <tr><td style="padding:0 34px">
    ${htmlVerse}
  </td></tr>

  <tr><td style="padding:0 34px">
    ${p('When you have watched, answer from your side of the wall.')}
    ${p('One minute on your phone is enough. Where you pray from, what you see, one verse if you like.')}
    ${p('I watch every one personally.')}
    ${button(WHATSAPP, 'Reply with your film on WhatsApp')}
  </td></tr>

  <tr><td style="padding:6px 34px 8px">
    ${p(`If your heart moves you to stand with the Land, you can lay a stone here: <a href="${esc(STAND)}" style="color:${GOLD_DEEP}">Stand with the Land</a>`, 'font-size:15px;')}
  </td></tr>

  <tr><td style="padding:18px 34px 0">
    ${p('Amitai (Tai) Elon<br>Natur Farm, Golan Heights<br>WhatsApp +972-54-444-2054', 'margin:0;')}
  </td></tr>

  <tr><td style="padding:28px 34px 34px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="border-top:1px solid ${GOLD};padding-top:18px;text-align:center">
        <p style="margin:0;font-family:Georgia,serif;font-size:13px;line-height:2;color:#6b6455">
          <a href="${SITE}" style="color:${GOLD_DEEP}">The site</a>
          &nbsp;&middot;&nbsp;
          <a href="${ARCHIVE_DOC}" style="color:${GOLD_DEEP}">The book of the letters</a>
          &nbsp;&middot;&nbsp;
          <a href="${KEEPSAKE_PDF}" style="color:${GOLD_DEEP}">The keepsake</a>
        </p>
      </td></tr>
    </table>
  </td></tr>

</table>

</td></tr>
</table>
</body>
</html>
`;

/* ---------- write ---------- */

const outDir = path.join(ROOT, 'letters-out');
fs.mkdirSync(outDir, { recursive: true });
const txtPath = path.join(outDir, `${film.slug}.letter.txt`);
const htmlPath = path.join(outDir, `${film.slug}.letter.html`);
fs.writeFileSync(txtPath, txt);
fs.writeFileSync(htmlPath, html);
console.log('letter OK');
console.log('  ' + path.relative(ROOT, txtPath));
console.log('  ' + path.relative(ROOT, htmlPath));
console.log('Fill in the TODO lines before sending. Tai\'s heart writes the opening.');
