"""Voiceover via edge-tts (free Microsoft neural voices, no API key).

Browse voices:  edge-tts --list-voices
Nice picks: en-IN-NeerjaNeural (f), en-IN-PrabhatNeural (m), en-US-AriaNeural, en-GB-SoniaNeural
"""
import asyncio, time
from pathlib import Path


def synth(text, dest, voice, retries=3):
    try:
        import edge_tts
    except ImportError:
        raise SystemExit("edge-tts not installed — run `pip install edge-tts`.")
    if voice.get("provider", "edge") != "edge":
        raise SystemExit(f"Unknown voice.provider: {voice.get('provider')}")

    async def _run():
        comm = edge_tts.Communicate(text, voice.get("name", "en-US-AriaNeural"),
                                    rate=voice.get("rate", "+0%"))
        await comm.save(str(dest))

    last = None
    for attempt in range(1, retries + 1):
        try:
            asyncio.run(_run())
            if Path(dest).exists() and Path(dest).stat().st_size > 0:
                return Path(dest)
            raise RuntimeError("edge-tts returned no audio")
        except Exception as e:                       # network blips, empty responses
            last = e
            if attempt < retries:
                time.sleep(3 * attempt)
    raise SystemExit(f"TTS failed after {retries} attempts: {last}")
