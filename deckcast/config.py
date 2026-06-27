"""Load + normalize a deckcast config (YAML or JSON) over sensible defaults."""
import json
from pathlib import Path

DEFAULTS = {
    "project": "Untitled Deck",
    "output": "out/deckcast.mp4",
    "theme": {
        "brand": "Deckcast",
        "accent": "#1f6f63", "accent2": "#d98a3d",
        "bg": "#fbf8f2", "ink": "#1d2a27",
    },
    "image": {
        "provider": "hf",            # hf | pollinations | none
        "model": "schnell",
        "token_env": "HF_TOKEN",
        "style": ("candid documentary photograph, natural available light, realistic, "
                  "true-to-life colors, soft depth of field, sharp focus, high resolution"),
        "width": 1344, "height": 768,
    },
    "voice": {
        "provider": "edge",          # edge
        "name": "en-IN-NeerjaNeural",
        "rate": "-4%",
    },
    "frames": {
        "mode": "builtin",           # builtin | deck
        "deck_path": None,           # required if mode == deck (must support ?clean#N)
        "width": 1920, "height": 1080,
    },
    "llm": {
        "enabled": False,            # OpenAI-compatible — works with ANY provider
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
    },
    "video": {"fps": 30, "tail_seconds": 0.8, "audio_bitrate": "192k"},
    "formats": ["mp4"],              # any of: mp4 | pptx | html
    "pptx": None,                    # optional explicit path (else derived from `output`)
    "html": None,                    # optional explicit path (else derived from `output`)
    "slides": [],
}


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def read_raw(path):
    """Parse a YAML/JSON file to a plain dict — no defaults, no validation."""
    path = Path(path)
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise SystemExit("PyYAML not installed (`pip install pyyaml`) — or use a .json config.")
        return yaml.safe_load(text) or {}
    return json.loads(text)


def load(path):
    cfg = _merge(DEFAULTS, read_raw(path))
    cfg["_dir"] = str(Path(path).resolve().parent)
    if not cfg["slides"] and not cfg.get("brief"):
        raise SystemExit("Config has no 'slides' (and no 'brief' to generate them from).")
    return cfg
