"""Voiceover via edge-tts (free Microsoft neural voices, no API key).

Browse voices:  edge-tts --list-voices
Nice picks: en-IN-NeerjaNeural (f), en-IN-PrabhatNeural (m), en-US-AriaNeural, en-GB-SoniaNeural
"""
import asyncio
from pathlib import Path


def synth(text, dest, voice):
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

    asyncio.run(_run())
    return Path(dest)
