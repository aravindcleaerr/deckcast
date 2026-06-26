"""Image generation — free providers, no paid key required.

  hf          : Hugging Face FLUX.1-schnell (free token in $HF_TOKEN) — higher quality
  pollinations: Pollinations Flux (no key at all) — quickest, lower ceiling
  none        : skip generation (you provide `image` paths in the config yourself)
"""
import os, time, urllib.parse
from pathlib import Path
from .util import http_get, http_post_json

HF_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-{m}"
POLLI = "https://image.pollinations.ai/prompt/"


def _hf(prompt, dest, img):
    token = os.environ.get(img.get("token_env", "HF_TOKEN"), "")
    if not token:
        raise SystemExit(f"image.provider=hf needs a token in ${img.get('token_env','HF_TOKEN')} "
                         f"(free: huggingface.co/settings/tokens)")
    model = "schnell" if img.get("model") != "dev" else "dev"
    url = HF_URL.format(m=model)
    params = {"width": img["width"], "height": img["height"]}
    if img.get("seed") is not None:
        params["seed"] = img["seed"]
    params["num_inference_steps"] = 4 if model == "schnell" else 30
    for attempt in range(1, 7):
        status, data, ctype = http_post_json(
            url, {"inputs": prompt, "parameters": params},
            headers={"Authorization": f"Bearer {token}", "x-wait-for-model": "true"},
            accept="image/png")
        if status == 200 and "image" in ctype and len(data) > 3000:
            Path(dest).write_bytes(data)
            return True
        if status == 503:
            time.sleep(20); continue
        if status in (401, 403, 402, 410):
            raise SystemExit(f"HF image error (HTTP {status}): {data.decode(errors='replace')[:200]}")
        time.sleep(6)
    return False


def _pollinations(prompt, dest, img):
    q = urllib.parse.urlencode({"width": img["width"], "height": img["height"],
                                "model": "flux", "nologo": "true",
                                **({"seed": img["seed"]} if img.get("seed") is not None else {})})
    url = POLLI + urllib.parse.quote(prompt, safe="") + "?" + q
    for attempt in range(1, 5):
        try:
            data, _ = http_get(url, timeout=180)
            if len(data) > 3000:
                Path(dest).write_bytes(data); return True
        except Exception:
            pass
        time.sleep(5)
    return False


def generate(prompt, dest, img, style=""):
    provider = img.get("provider", "hf")
    if provider == "none":
        return False
    full = f"{prompt}. {style}" if style else prompt
    if provider == "hf":
        return _hf(full, dest, img)
    if provider == "pollinations":
        return _pollinations(full, dest, img)
    raise SystemExit(f"Unknown image.provider: {provider}")
