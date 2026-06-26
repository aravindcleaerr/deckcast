"""Optional LLM step: turn each slide's topic/title into an image prompt + narration.

Only runs for slides missing `image_prompt` or `narration`, and only if llm.enabled.
Provider-agnostic (see llm.py). With llm.enabled = false, you simply supply those
fields yourself in the config and this step is skipped entirely.
"""
import json, re
from . import llm

SYSTEM = (
    "You script short narrated slide videos. For each slide you are given a title, "
    "optional subtitle, and optional topic/notes. Return STRICT JSON: an array with one "
    "object per slide, in order, each {\"image_prompt\": str, \"narration\": str}. "
    "image_prompt: a vivid, concrete visual scene (people/objects/lighting) suitable for a "
    "text-to-image model; no text or UI in the image. narration: 2-3 natural spoken "
    "sentences a presenter would say over that slide. Do not include slide numbers. "
    "Return ONLY the JSON array."
)


def _extract_array(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\[.*\]", text, flags=re.S)
    arr = json.loads(m.group(0) if m else text)
    if not isinstance(arr, list):
        raise ValueError("LLM did not return a JSON array")
    return arr


def _parse(text, n):
    arr = _extract_array(text)
    if len(arr) < n:
        raise ValueError(f"LLM returned {len(arr)} items, expected {n}")
    return arr


OUTLINE_SYSTEM = (
    "You are a presentation designer + scriptwriter. Given a brief, design a complete, "
    "coherent slide deck with a clear narrative arc (hook, problem, solution, a few "
    "supporting points, and a memorable close). Return STRICT JSON: an array of slide "
    "objects, in order. Each slide has: "
    "\"eyebrow\" (2-4 word kicker), \"title\" (punchy headline), then EITHER \"subtitle\" "
    "(one supporting line) OR \"bullets\" (3-5 short phrases) — pick whichever fits, "
    "\"image_prompt\" (a vivid concrete visual scene for a text-to-image model; no text, no "
    "UI, no charts), and \"narration\" (2-3 natural spoken sentences for that slide). "
    "Optionally set \"dark\": true on ONE pivotal slide for emphasis. The first slide is a "
    "cover; the last is a closing call-to-action. Return ONLY the JSON array."
)


def outline(brief, theme, llm_cfg, count=None):
    """Autonomous mode: turn a one-line brief into a full slide list via the LLM."""
    if not llm_cfg.get("enabled"):
        raise SystemExit("Autonomous mode needs llm.enabled=true (set base_url / model / key).")
    howmany = f"exactly {count} slides" if count else "between 8 and 12 slides"
    user = (f"Brand: {theme.get('brand')}. Tone: warm, clear, confident.\n"
            f"Create {howmany} for this brief:\n{brief}")
    out = llm.chat([{"role": "system", "content": OUTLINE_SYSTEM},
                    {"role": "user", "content": user}], llm_cfg)
    keep = ("eyebrow", "title", "subtitle", "bullets", "image_prompt", "narration", "dark")
    slides = []
    for o in _extract_array(out):
        slides.append({k: o[k] for k in keep if o.get(k) not in (None, "")})
    if not slides:
        raise SystemExit("LLM returned an empty deck.")
    return slides


def author(slides, theme, llm_cfg):
    if not llm_cfg.get("enabled"):
        return slides
    missing = [i for i, s in enumerate(slides)
               if not s.get("image_prompt") or not s.get("narration")]
    if not missing:
        return slides
    brief = [{"i": i, "title": s.get("title", ""), "subtitle": s.get("subtitle", ""),
              "topic": s.get("topic", "")} for i, s in enumerate(slides)]
    user = (f"Brand/voice: {theme.get('brand')}. Tone: warm, clear, confident.\n"
            f"Slides:\n{json.dumps(brief, ensure_ascii=False)}")
    out = llm.chat([{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user}], llm_cfg)
    arr = _parse(out, len(slides))
    for i, s in enumerate(slides):
        if not s.get("image_prompt"):
            s["image_prompt"] = arr[i].get("image_prompt", "")
        if not s.get("narration"):
            s["narration"] = arr[i].get("narration", "")
    return slides
