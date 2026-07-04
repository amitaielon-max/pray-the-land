#!/usr/bin/env python3
"""List silences in a clip, to guide the cut.

    npm run silences -- <media file>

Prints every silence longer than the grammar threshold (0.7s). Cut the dead
air, but keep his breath and the pauses before important lines. Silences
longer than 1.5s must not survive into the master except intentional
Scripture pauses.
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fail, load_config

cfg = load_config()
thr = cfg["editingGrammar"]["cutSilenceOverSeconds"]

if len(sys.argv) != 2:
    fail("usage: silences.py <media file>")
media = sys.argv[1]
if not os.path.exists(media):
    fail("no such file: " + media)

res = subprocess.run(
    ["ffmpeg", "-hide_banner", "-i", media, "-vn",
     "-af", f"silencedetect=noise=-32dB:d={thr}", "-f", "null", "-"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
starts = re.findall(r"silence_start: ([\d.]+)", res.stderr)
ends = re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", res.stderr)

if not starts:
    print(f"no silences over {thr}s")
    sys.exit(0)
print(f"silences over {thr}s in {os.path.basename(media)}:")
for i, s in enumerate(starts):
    if i < len(ends):
        e, d = ends[i]
        flag = "  <-- must not survive (unless Scripture pause)" if float(d) > cfg["editingGrammar"]["maxSilenceSeconds"] else ""
        print(f"  {float(s):8.2f}s -> {float(e):8.2f}s  ({float(d):.2f}s){flag}")
    else:
        print(f"  {float(s):8.2f}s -> end of clip")
