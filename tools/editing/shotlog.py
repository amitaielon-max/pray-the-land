#!/usr/bin/env python3
"""Build the shot log for a folder of raw clips.

    npm run shotlog [-- <folder>]        (default: rawDir from editing.config.json)

Probes every clip (duration, resolution, orientation, audio level, creation
time) and writes, next to the clips:
    shots.json    machine readable
    shotlog.md    the human log: clip table plus empty STORY and PROPOSED ORDER
                  sections that the editor fills in and shows Tai BEFORE
                  rendering. One confirmation, then execute fully.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, VIDEO_EXTS, fail, load_config, mean_volume_db, probe_summary

cfg = load_config()
folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, cfg["rawDir"])
if not os.path.isdir(folder):
    fail(f"no such folder: {folder}\nPut the raw clips there (or pass the folder as an argument).")

clips = sorted(
    f for f in os.listdir(folder)
    if os.path.splitext(f)[1].lower() in VIDEO_EXTS and not f.startswith(".")
)
if not clips:
    fail(f"no video clips found in {folder}")

shots = []
for name in clips:
    path = os.path.join(folder, name)
    info = probe_summary(path)
    if info is None:
        print(f"  skipping (no video stream): {name}")
        continue
    info["mean_volume"] = mean_volume_db(path) if info["has_audio"] else "no audio"
    shots.append(info)
    print(f"  {name}: {info['duration']}s {info['width']}x{info['height']} {info['orientation']} audio {info['mean_volume']}")

shots.sort(key=lambda s: (s["created"] or "9999", s["file"]))

with open(os.path.join(folder, "shots.json"), "w") as f:
    json.dump(shots, f, indent=2)

lines = [
    "# Shot log",
    "",
    "| # | clip | duration | size | orientation | audio | created |",
    "|---|------|----------|------|-------------|-------|---------|",
]
for i, s in enumerate(shots, 1):
    lines.append(
        f"| {i} | {s['file']} | {s['duration']}s | {s['width']}x{s['height']} "
        f"| {s['orientation']} | {s['mean_volume']} | {s['created'] or '?'} |"
    )
lines += [
    "",
    "## THE STORY FOUND IN THE FOOTAGE",
    "",
    "[One paragraph. What the footage wants to say. Show this to Tai before rendering.]",
    "",
    "## PROPOSED ORDER",
    "",
    "[Hook: which line, from which clip, at what time.]",
    "[Arrival wide + lower third text.]",
    "[The walk: talking segments and the detail shots that cover them.]",
    "[The turn: the Scripture moment, what the camera holds on.]",
    "[The close: his last line.]",
    "",
    "## WHAT WAS CUT AND WHY",
    "",
    "[Fill during the edit. Becomes part of output/<slug>/shotlog.md.]",
    "",
]
with open(os.path.join(folder, "shotlog.md"), "w") as f:
    f.write("\n".join(lines))

print(f"\nshotlog OK: {len(shots)} clips")
print(f"  {os.path.join(folder, 'shotlog.md')}")
print(f"  {os.path.join(folder, 'shots.json')}")
print("Fill in THE STORY and PROPOSED ORDER, show Tai, get one confirmation, then render.")
