# The Editing Room

Turns Tai's raw phone footage into finished Films from the Land episodes,
consistent as one series, with near-zero effort from Tai. Claude Code owns
all editing. Rendering ends the job: Tai uploads to YouTube. Nothing is
ever uploaded from here.

## The flow

1. **Ingest.** Tai drops raw clips in the Google Drive folder "Raw Films"
   (id in `tools/editing.config.json`). In a session they are fetched into
   `raw-films/` (gitignored). On a local machine, point `rawDir` at the
   Google Drive for Desktop synced folder instead.
2. **Shot log.** `npm run shotlog` probes every clip and writes
   `shotlog.md`. `npm run silences -- <clip>` lists dead air.
   `npm run transcribe -- <clip>` writes an SRT of what Tai says.
3. **The story.** The editor watches the footage, fills in THE STORY and
   PROPOSED ORDER in shotlog.md, and shows Tai the one-paragraph story and
   order BEFORE rendering. One confirmation, then execute fully.
4. **Render.** Write the EDL (see `example-edl.json`), then
   `npm run render:film -- <edl.json>`. Output lands in `output/<slug>/`.
5. **Thumbnail.** `npm run thumbnail -- <slug> <video> <seconds> "<Title>"`
   picks the best land frame.
6. **Paperwork.** The render drafts the films.json entry and, once the slug
   is in `data/films.json`, runs the letter generator automatically.
7. Used clips move to `raw-films/used/<slug>/` after a successful render.

## The editing grammar (Tai's style, treat as law)

Open-loop ladder, in this order:

1. **HOOK** (first 8 to 15 seconds): the single most curiosity-pulling line
   Tai says anywhere in the footage, pulled forward, over the strongest
   wide shot. It opens a question, never answers one. Never start with
   "Hi" or context.
2. **ARRIVAL**: one wide shot, place named with a simple lower third
   (place + region, e.g. "Beit She'an · The Decapolis").
3. **THE WALK**: Tai talking to camera, intercut with his detail shots as
   B-roll over his own voice. Cut silences over 0.7s and false starts, but
   KEEP his breath, his pauses before important lines, his imperfections.
   The stumbles are the voice. Do not over-tighten. Unhurried.
4. **THE TURN**: the Scripture moment. Slow down. Hold shots longer. If he
   reads a verse, show the land while he reads, not his face.
5. **THE CLOSE**: his last heartfelt line, then cut to the closing card.

Length 3 to 8 minutes. Never pad: if the footage gives 3 good minutes, the
film is 3 minutes. Gentle push-ins (max 110%) on key sentences only. No
whip cuts, no beat-synced editing, no meme style. One gentle warm grade,
identical on every film (saved in `editing.config.json`).

## Series packaging (identical every episode)

- Opening title card, 3.5s, AFTER the hook, never before. Navy #14213d,
  thin gold #C9A227 rule, serif. 0.5s crossfades in and out.
- Lower thirds: cream text, thin gold underline, bottom left, 4s.
- Captions: burned in, bottom center, cream on 55% navy strip, serif,
  max 2 lines. No word-by-word pop (that is shorts grammar). Keep the
  spoken language: Hebrew stays Hebrew. A quoted Hebrew verse gets Hebrew
  on the first line, English in parentheses on the second.
- Closing card, 8s: templates in `assets/cards/`, built by
  `npm run cards -- templates`.
- Audio: speech -16 LUFS. Music only from `assets/music/`, at about
  -26 LUFS, ducked under speech, silent during the turn unless Tai asks.

## Outputs per film (`output/<slug>/`)

1. `<slug>_master.mp4` — 1920x1080, H.264 high, CRF 18, AAC 192k
2. `<slug>_teaser_9x16.mp4` — optional, only if a clean 45 to 60s vertical
   crop of the hook plus one strong moment exists (word-by-word captions
   allowed there; that is shorts grammar and it is welcome on WhatsApp
   Status). Recipe: crop=608:1080 around the subject, scale=1080:1920.
3. `<slug>_thumbnail.jpg` — 1280x720, best land frame, title in serif over
   a navy gradient, thin gold rule
4. `shotlog.md` — what was used, what was cut and why
5. The Phase 3 letter, once the film is in `data/films.json`

## QC checklist (verify before declaring done)

- [ ] Hook opens a question in the first 15 seconds
- [ ] No silence over 1.5s except intentional Scripture pauses
- [ ] Captions match speech, Hebrew kept as Hebrew
- [ ] Title and closing cards match the brand spec exactly
- [ ] Speech -16 LUFS, no clipping, music never fights the voice
- [ ] Length 3 to 8 minutes, ends on Tai's line, not on B-roll
- [ ] Thumbnail readable at phone size
- [ ] films.json entry drafted (Tai adds youtube_id after upload)

## What never happens in the editing room

No stock footage. No AI-generated visuals. No footage Tai did not film.
No captions that clean up his English into corporate English. No jump-cut
machine-gun pacing. No emojis on screen. No subscribe buttons. Never
upload anywhere: rendering ends the job.

## Environment notes

- ffmpeg: `apt-get update && apt-get install -y ffmpeg` if missing.
- Captions: `pip install faster-whisper` (preferred) or
  `pip install openai-whisper`. Model download needs huggingface.co or
  openaipublic.azureedge.net reachable; in Claude Code web sessions add
  those domains to the environment's allowed network list.
- Fonts live in `tools/editing/fonts/` (EB Garamond for cards and lower
  thirds, Frank Ruhl Libre for captions, which needs Hebrew glyphs).
