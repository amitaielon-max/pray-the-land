#!/usr/bin/env python3
"""Render a finished Films from the Land master from an edit decision list.

    npm run render:film -- <edl.json>

The EDL is the editor's one confirmed plan (see example-edl.json):

    {
      "slug": "still-waters",              required
      "num": "II",                         required, Roman numeral
      "place": "Beit She'an",              required
      "region": "The Decapolis",           optional, for the lower third
      "title": "Still Waters",             required
      "clipsDir": "raw-films",             optional, default from config
      "base": [                            the spine: audio + default video
        {"clip": "a.mov", "in": 12.0, "out": 25.5, "role": "hook", "pushIn": true},
        {"clip": "b.mov", "in": 3.0, "out": 11.0, "role": "arrival"},
        {"clip": "a.mov", "in": 40.0, "out": 95.0, "role": "walk"}
      ],
      "broll": [                           optional, video only, over the spine
        {"clip": "c.mov", "in": 2.0, "at": 48.0, "duration": 5.0}
      ],
      "lowerThirdAt": 16.2,                optional, default: arrival start
      "captions": "path/to/captions.srt",  optional, timed to the FINAL cut
      "turn": [120.0, 150.0],              optional, Scripture moment (master time)
      "music": {"file": "assets/music/x.mp3"}   optional
    }

Structure produced: hook, 0.5s crossfade into the 3.5s title card, 0.5s
crossfade out into the rest of the spine (straight cuts), then the 8s
closing card. B-roll overlays cover the spine video while Tai's voice
continues. Speech normalized to -16 LUFS; music, if any, sits at about
-26 LUFS, ducks under speech, and stays out of the Scripture turn.

Writes to output/<slug>/:
    <slug>_master.mp4, title-card.png, films-entry.json, shotlog.md (copied)
and moves used clips to <clipsDir>/used/<slug>/. Then runs the Phase 3
letter generator if the slug is already in data/films.json.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cards
from common import ROOT, fail, ffprobe_json, load_config, roman_or_fail, run

cfg = load_config()
V = cfg["video"]
W, H, FPS = V["width"], V["height"], V["fps"]
GRADE = cfg["grade"]["filter"]
FONTS = os.path.join(ROOT, cfg["fontsDir"])


def duration_of(path):
    return float(ffprobe_json(path)["format"]["duration"])


def norm_filter(push_in, seg_dur):
    """Scale/pad to 1920x1080@30, grade, optional gentle push-in to 110%."""
    f = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},setsar=1," + GRADE
    )
    if push_in:
        frames = max(int(seg_dur * FPS), 1)
        step = (V["maxPushIn"] - 1.0) / frames
        f += (
            f",scale={W * 2}:{H * 2},"
            f"zoompan=z='min(1+{step:.6f}*on,{V['maxPushIn']})'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}"
        )
    return f


def cut_segment(src, t_in, t_out, dst, push_in=False, video_only=False):
    dur = t_out - t_in
    cmd = ["ffmpeg", "-y", "-ss", str(t_in), "-t", str(dur), "-i", src,
           "-vf", norm_filter(push_in, dur),
           "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
           "-pix_fmt", "yuv420p"]
    if video_only:
        cmd += ["-an"]
    else:
        cmd += ["-af", "aresample=48000", "-ac", "2", "-c:a", "aac", "-b:a", "256k"]
    run(cmd + [dst])


def card_clip(png, seconds, dst):
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(seconds), "-i", png,
         "-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=stereo",
         "-vf", f"scale={W}:{H},fps={FPS},setsar=1",
         "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", dst])


def xfade_pair(a, b, dst, fade):
    off = duration_of(a) - fade
    run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex",
         f"[0:v][1:v]xfade=transition=fade:duration={fade}:offset={off:.3f}[v];"
         f"[0:a][1:a]acrossfade=d={fade}[a]",
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", dst])


def concat_files(files, dst):
    if len(files) == 1:
        shutil.copyfile(files[0], dst)
        return
    lst = dst + ".txt"
    with open(lst, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst])


def make_lower_third(text, dst):
    lt_cfg = cfg["lowerThird"]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Medium.ttf"), lt_cfg["fontSize"])
    x = lt_cfg["marginLeft"]
    y = H - lt_cfg["marginBottom"] - lt_cfg["fontSize"]
    d.text((x + 2, y + 2), text, font=f, fill=(10, 8, 5, 160))  # soft shadow
    d.text((x, y), text, font=f, fill=cfg["cards"]["cream"])
    tw = d.textlength(text, font=f)
    d.rectangle([x, y + lt_cfg["fontSize"] + 16, x + tw, y + lt_cfg["fontSize"] + 18],
                fill=cfg["cards"]["gold"])
    im.save(dst)


# ---------------- load EDL ----------------

if len(sys.argv) != 2:
    fail("usage: render_film.py <edl.json>")
with open(sys.argv[1]) as f:
    edl = json.load(f)
for k in ("slug", "num", "place", "title", "base"):
    if k not in edl:
        fail(f'EDL is missing "{k}"')
roman_or_fail(edl["num"])
if not edl["base"]:
    fail("EDL base is empty")

clips_dir = os.path.join(ROOT, edl.get("clipsDir", cfg["rawDir"]))
out_dir = os.path.join(ROOT, cfg["outputDir"], edl["slug"])
os.makedirs(out_dir, exist_ok=True)


def clip_path(name):
    p = os.path.join(clips_dir, name)
    if not os.path.exists(p):
        fail(f"clip not found: {p}")
    return p


tmp = tempfile.mkdtemp(prefix="ftl-")
print(f"editing room: {edl['slug']} (work dir {tmp})")

# 1. spine segments
seg_files = []
for i, seg in enumerate(edl["base"]):
    dst = os.path.join(tmp, f"seg{i:02}.mp4")
    print(f"  segment {i} [{seg.get('role', 'walk')}] {seg['clip']} {seg['in']}..{seg['out']}")
    cut_segment(clip_path(seg["clip"]), seg["in"], seg["out"], dst, seg.get("pushIn", False))
    seg_files.append(dst)

# 2. title card after the hook (never before), 0.5s crossfades
print("  title card")
title_png = cards.build_title(edl["slug"], edl["num"], edl["place"], edl["title"])
title_clip = os.path.join(tmp, "title.mp4")
card_clip(title_png, cfg["cards"]["titleCardSeconds"], title_clip)

fade = cfg["cards"]["titleCrossfadeSeconds"]
hook_card = os.path.join(tmp, "hook_card.mp4")
xfade_pair(seg_files[0], title_clip, hook_card, fade)
spine = os.path.join(tmp, "spine.mp4")
if len(seg_files) > 1:
    rest = os.path.join(tmp, "rest.mp4")
    concat_files(seg_files[1:], rest)
    xfade_pair(hook_card, rest, spine, fade)
else:
    shutil.copyfile(hook_card, spine)

# 3. b-roll overlays + lower third over the spine
spine_dur = duration_of(spine)
inputs = ["-i", spine]
fc, last = [], "0:v"
idx = 1

for j, b in enumerate(edl.get("broll", [])):
    bf = os.path.join(tmp, f"broll{j:02}.mp4")
    print(f"  broll {j} {b['clip']} at {b['at']}s for {b['duration']}s")
    cut_segment(clip_path(b["clip"]), b["in"], b["in"] + b["duration"], bf, video_only=True)
    inputs += ["-i", bf]
    fc.append(f"[{idx}:v]setpts=PTS-STARTPTS+{b['at']}/TB[b{j}]")
    fc.append(f"[{last}][b{j}]overlay=eof_action=pass:enable='between(t,{b['at']},{b['at'] + b['duration']})'[v{j}]")
    last = f"v{j}"
    idx += 1

lt_text = edl["place"] + (" · " + edl["region"] if edl.get("region") else "")
lt_png = os.path.join(tmp, "lowerthird.png")
make_lower_third(lt_text, lt_png)
hook_dur = duration_of(seg_files[0])
lt_at = float(edl.get("lowerThirdAt", hook_dur + cfg["cards"]["titleCardSeconds"] - 2 * fade + 0.6))
lt_dur = cfg["lowerThird"]["seconds"]
inputs += ["-loop", "1", "-t", str(lt_dur), "-i", lt_png]
fc.append(f"[{idx}:v]format=rgba,fade=in:st=0:d=0.4:alpha=1,fade=out:st={lt_dur - 0.4}:d=0.4:alpha=1,setpts=PTS-STARTPTS+{lt_at}/TB[lt]")
fc.append(f"[{last}][lt]overlay=eof_action=pass[vlt]")
last = "vlt"

overlaid = os.path.join(tmp, "overlaid.mp4")
run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
     "-map", f"[{last}]", "-map", "0:a",
     "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
     "-pix_fmt", "yuv420p", "-c:a", "copy", overlaid])

# 4. closing card, 8s, straight cut after Tai's last line
print("  closing card")
closing_png = os.path.join(ROOT, cfg["cardsDir"], "closing-card.png")
if not os.path.exists(closing_png):
    cards.build_templates()
closing = os.path.join(tmp, "closing.mp4")
card_clip(closing_png, cfg["cards"]["closingCardSeconds"], closing)
run(["ffmpeg", "-y", "-i", closing, "-vf", "fade=in:st=0:d=0.3",
     "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
     "-pix_fmt", "yuv420p", "-c:a", "copy", os.path.join(tmp, "closing_f.mp4")])
assembled = os.path.join(tmp, "assembled.mp4")
concat_files([overlaid, os.path.join(tmp, "closing_f.mp4")], assembled)

# 5. captions burned in (timed to the final cut)
with_caps = assembled
if edl.get("captions"):
    print("  captions")
    srt = os.path.join(ROOT, edl["captions"]) if not os.path.isabs(edl["captions"]) else edl["captions"]
    if not os.path.exists(srt):
        fail("captions file not found: " + srt)
    with_caps = os.path.join(tmp, "captioned.mp4")
    style = cfg["captions"]["forceStyle"].replace(",", "\\,").replace("&", "\\&")
    sub = f"subtitles={srt}:fontsdir={FONTS}:force_style='{cfg['captions']['forceStyle']}'"
    run(["ffmpeg", "-y", "-i", assembled, "-vf", sub,
         "-c:v", "libx264", "-crf", str(V["mezzanineCrf"]), "-preset", "fast",
         "-pix_fmt", "yuv420p", "-c:a", "copy", with_caps])

# 6. audio: speech to -16 LUFS; optional music bed, ducked, silent over the turn
print("  audio")
A = cfg["audio"]
total = duration_of(with_caps)
loudnorm = f"loudnorm=I={A['speechLufs']}:TP={A['truePeak']}:LRA={A['lra']}"
master = os.path.join(out_dir, f"{edl['slug']}_master.mp4")
vcodec = ["-c:v", "libx264", "-crf", str(V["masterCrf"]), "-preset", V["masterPreset"],
          "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]

music = edl.get("music")
if music:
    mfile = os.path.join(ROOT, music["file"]) if not os.path.isabs(music["file"]) else music["file"]
    if not os.path.exists(mfile):
        fail("music file not found: " + mfile)
    mute = ""
    if edl.get("turn"):
        t0, t1 = edl["turn"]
        mute = f",volume=0:enable='between(t,{t0},{t1})'"
    fcx = (
        f"[0:a]{loudnorm}[speech];"
        f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},loudnorm=I=-26:TP=-2:LRA=11{mute}[bed];"
        f"[speech]asplit=2[s1][s2];"
        f"[bed][s2]{A['ducking']}[ducked];"
        f"[s1][ducked]amix=inputs=2:duration=first:normalize=0[mix]"
    )
    run(["ffmpeg", "-y", "-i", with_caps, "-i", mfile, "-filter_complex", fcx,
         "-map", "0:v", "-map", "[mix]", *vcodec, "-c:a", "aac", "-b:a", "192k", master])
else:
    run(["ffmpeg", "-y", "-i", with_caps, "-af", loudnorm,
         "-map", "0:v", "-map", "0:a", *vcodec, "-c:a", "aac", "-b:a", "192k", master])
    mdir = os.path.join(ROOT, cfg["musicDir"])
    tracks = [f for f in os.listdir(mdir) if os.path.splitext(f)[1].lower() in
              (".mp3", ".wav", ".m4a", ".flac", ".ogg")] if os.path.isdir(mdir) else []
    if not tracks:
        print("  note: no music rendered. assets/music/ is empty. Suggest quiet")
        print("  acoustic or strings Tai owns or licenses, no percussion-heavy beds.")

print(f"master OK: {master} ({duration_of(master):.1f}s)")

# 7. paperwork: shotlog copy, films.json draft, used clips, letter
src_log = os.path.join(clips_dir, "shotlog.md")
if os.path.exists(src_log):
    shutil.copyfile(src_log, os.path.join(out_dir, "shotlog.md"))

films_path = os.path.join(ROOT, "data", "films.json")
films = json.load(open(films_path)) if os.path.exists(films_path) else []
in_films = any(f.get("slug") == edl["slug"] for f in films)
if not in_films:
    draft = {
        "num": edl["num"], "slug": edl["slug"], "title": edl["title"],
        "place": edl["place"], "youtube_id": "PASTE_AFTER_UPLOAD",
        "desc": "Description line one.\nDescription line two.",
        "date": "",
    }
    with open(os.path.join(out_dir, "films-entry.json"), "w") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    print("drafted films.json entry: " + os.path.join(out_dir, "films-entry.json"))
    print("  (Tai uploads to YouTube, then the entry goes into data/films.json with the real id)")

used_dir = os.path.join(clips_dir, cfg["usedDirName"], edl["slug"])
os.makedirs(used_dir, exist_ok=True)
used = {s["clip"] for s in edl["base"]} | {b["clip"] for b in edl.get("broll", [])}
for name in used:
    p = os.path.join(clips_dir, name)
    if os.path.exists(p):
        shutil.move(p, os.path.join(used_dir, name))
print(f"moved {len(used)} used clip(s) to {used_dir}")

if in_films:
    print("running the letter generator")
    run(["node", os.path.join(ROOT, "tools", "letter.js"), edl["slug"]], quiet=False)
else:
    print("letter: run after the film is added to data/films.json:")
    print(f"  npm run letter -- {edl['slug']}")

shutil.rmtree(tmp, ignore_errors=True)
print("editing room DONE. Walk the QC checklist in tools/editing/README.md before declaring done.")
