"""Shared helpers for the Films from the Land editing room."""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(ROOT, "tools", "editing.config.json")

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mts", ".avi", ".mkv", ".webm", ".3gp"}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fail(msg):
    print("editing room FAILED: " + msg, file=sys.stderr)
    sys.exit(1)


def run(cmd, quiet=True, **kw):
    """Run a command, failing loudly with its stderr if it errors."""
    res = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw
    )
    if res.returncode != 0:
        tail = "\n".join(res.stderr.splitlines()[-14:])
        fail(f"command failed: {' '.join(str(c) for c in cmd[:6])} ...\n{tail}")
    if not quiet and res.stdout:
        print(res.stdout)
    return res


def ffprobe_json(path):
    res = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path,
    ])
    return json.loads(res.stdout)


def probe_summary(path):
    """duration, resolution, fps, orientation, creation time, audio presence."""
    data = ffprobe_json(path)
    fmt = data.get("format", {})
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if v is None:
        return None
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    rotate = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotate = int(abs(sd["rotation"]))
    if rotate in (90, 270):
        w, h = h, w
    fps = v.get("avg_frame_rate", "0/1")
    try:
        num, den = fps.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else 0
    except ValueError:
        fps = 0
    return {
        "file": os.path.basename(path),
        "duration": round(float(fmt.get("duration", 0)), 2),
        "width": w,
        "height": h,
        "orientation": "vertical" if h > w else "horizontal",
        "fps": fps,
        "has_audio": a is not None,
        "created": (fmt.get("tags", {}) or {}).get("creation_time", ""),
    }


def mean_volume_db(path):
    """Mean loudness of a clip's audio via volumedetect (fast, mono, 16k)."""
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
         "-af", "volumedetect", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    for line in res.stderr.splitlines():
        if "mean_volume:" in line:
            return line.split("mean_volume:")[1].strip()
    return "n/a"


def roman_or_fail(s):
    if not s or any(c not in "IVXLCDM" for c in s):
        fail(f'"{s}" is not a Roman numeral (use I, II, III ...)')
    return s
