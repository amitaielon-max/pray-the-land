#!/usr/bin/env python3
"""Transcribe a clip to SRT captions, keeping the spoken language.

    npm run transcribe -- <media file> [model]

Writes <media file>.srt next to the input. Never translates: Hebrew stays
Hebrew, English stays English (whisper task=transcribe). For a quoted
Hebrew verse, hand-edit the caption afterwards: Hebrew on the first line,
English in parentheses on the second.

Uses faster-whisper if installed, else openai-whisper. Model downloads
need huggingface.co (faster-whisper) or openaipublic.azureedge.net
(openai-whisper) reachable; if the session's network policy blocks them,
allow those domains in the Claude Code environment settings.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fail, load_config

cfg = load_config()

if len(sys.argv) < 2:
    fail("usage: transcribe.py <media file> [model]")
media = sys.argv[1]
model_name = sys.argv[2] if len(sys.argv) > 2 else cfg["whisper"]["model"]
if not os.path.exists(media):
    fail("no such file: " + media)
out = os.path.splitext(media)[0] + ".srt"


def ts(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(segments):
    n = 0
    lines = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        n += 1
        lines += [str(n), f"{ts(seg['start'])} --> {ts(seg['end'])}", text, ""]
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"transcribe OK: {out} ({n} captions)")
    print("Review before burning in: keep his words as he said them. No corporate cleanup.")


try:
    from faster_whisper import WhisperModel  # type: ignore

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(media, task="transcribe", vad_filter=True)
    print(f"faster-whisper {model_name}, detected language: {info.language}")
    write_srt({"start": s.start, "end": s.end, "text": s.text} for s in segments)
    sys.exit(0)
except ImportError:
    pass

try:
    import whisper  # type: ignore

    model = whisper.load_model(model_name)
    result = model.transcribe(media, task="transcribe")
    print(f"openai-whisper {model_name}, detected language: {result.get('language')}")
    write_srt(result["segments"])
    sys.exit(0)
except ImportError:
    fail(
        "no whisper installed. Run one of:\n"
        "  pip install faster-whisper   (lighter, preferred)\n"
        "  pip install openai-whisper\n"
        "and make sure the model host is reachable (see docstring)."
    )
