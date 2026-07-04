# pray-the-land

The Pray the Land site. Deploys to https://pray-the-land-golan.netlify.app

## Adding a film

Edit `data/films.json` and add one entry:

```json
{
  "num": "II",
  "slug": "short-name-of-the-film",
  "title": "The Film Title",
  "place": "Where it was filmed",
  "youtube_id": "the id after watch?v= on YouTube",
  "desc": "Description line one.\nDescription line two.",
  "date": "2026-07-09"
}
```

Commit and push. Netlify runs `npm run build:films` on every deploy, which
regenerates the film cards on `films.html` (newest first) and writes a share
page at `/f/<slug>.html` for every film. No HTML is edited by hand.

To preview locally: `npm run build:films`, then open `films.html`.

## Writing the letter for a film

```
npm run letter -- <slug>
```

writes `letters-out/<slug>.letter.txt` and `letters-out/<slug>.letter.html`,
a paste-ready email pair for that film. Fill in the TODO opening lines
before sending; the generator scaffolds, Tai's heart writes the first six
lines. `letters-out/` is not committed and never deployed.

A film entry may optionally carry `"verse"`, `"verse_ref"` and
`"verse_heb"` fields; the letter then includes that Scripture in the gold
panel instead of a TODO placeholder.

Video is never hosted here. Films are unlisted YouTube embeds only.
