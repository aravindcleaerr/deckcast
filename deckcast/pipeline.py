"""Orchestrate the full pipeline: author -> images -> frames -> tts -> video.

Outputs are selected by `formats` (default ["mp4"]): mp4 (narrated video),
pptx, and/or html. pptx/html reuse the rendered frames, so tts/video stages
are skipped automatically when no mp4 is requested.
"""
from pathlib import Path
from . import author, images, frames, tts, video, export

STEPS = ["author", "images", "frames", "tts", "video"]
FORMATS = ["mp4", "pptx", "html"]


def _fmt_out(cfg, root, ext):
    explicit = cfg.get(ext)
    p = Path(explicit) if explicit else Path(cfg["output"]).with_suffix("." + ext)
    return p if p.is_absolute() else root / p


def run(cfg, steps=None, only=None, formats=None):
    steps = list(steps or STEPS)
    formats = [f.lower().lstrip(".") for f in (formats or cfg.get("formats") or ["mp4"])]
    # pptx/html only need frames; drop audio/video stages when no mp4 is wanted.
    if "mp4" not in formats:
        steps = [s for s in steps if s not in ("tts", "video")]
    root = Path(cfg["_dir"])
    build = root / "build_deckcast"
    fdir, idir, adir, sdir = build / "frames", build / "images", build / "audio", build / "segments"
    for d in (fdir, idir, adir, sdir):
        d.mkdir(parents=True, exist_ok=True)

    slides = cfg["slides"]
    theme, img, voice, fr, vid = cfg["theme"], cfg["image"], cfg["voice"], cfg["frames"], cfg["video"]

    # 0) autonomous mode — no slides, just a brief: let the LLM design the whole deck
    if not slides and cfg.get("brief"):
        print(f"authoring deck from brief ({cfg['llm']['model']})...", flush=True)
        slides = author.outline(cfg["brief"], theme, cfg["llm"])
        cfg["slides"] = slides
        print(f"  -> {len(slides)} slides drafted", flush=True)

    fsize = (fr["width"], fr["height"])
    idxs = [only - 1] if only else range(len(slides))

    # 1) LLM authoring (optional, in-place) — fills any missing prompt/narration
    if "author" in steps:
        slides = author.author(slides, theme, cfg["llm"])

    segs, total, built = [], 0.0, []
    for i in idxs:
        s = slides[i]
        tag = f"slide {i+1:02d}"

        # 2) image
        img_path = None
        if fr["mode"] == "builtin":
            if s.get("image"):                       # user-supplied path
                p = Path(s["image"])
                img_path = p if p.is_absolute() else root / p
            elif "images" in steps and s.get("image_prompt"):
                img_path = idir / f"img-{i+1:02d}.png"
                print(f"{tag}: generating image ({img['provider']})...", flush=True)
                if not images.generate(s["image_prompt"], img_path, img, img.get("style", "")):
                    print(f"{tag}: image generation failed — frame will use solid background")
                    img_path = None

        # 3) frame
        frame = fdir / f"frame-{i+1:02d}.png"
        if "frames" in steps:
            print(f"{tag}: rendering frame...", flush=True)
            if fr["mode"] == "deck":
                frames.deck_frame(fr["deck_path"], i, frame, fsize)
            else:
                frames.builtin_frame(s, i, len(slides), theme, img_path, frame, fsize)
        built.append({"frame": frame, "narration": s.get("narration"), "title": s.get("title")})

        # 4) voiceover
        audio = adir / f"audio-{i+1:02d}.mp3"
        if "tts" in steps:
            text = s.get("narration") or s.get("title") or ""
            print(f"{tag}: voiceover ({voice['name']})...", flush=True)
            tts.synth(text, audio, voice)

        # 5) segment
        if "video" in steps:
            seg = sdir / f"seg-{i+1:02d}.mp4"
            dur = video.segment(frame, audio, seg, fsize, vid["fps"], vid["tail_seconds"],
                                vid["audio_bitrate"])
            segs.append(seg); total += dur
            print(f"{tag}: segment {dur:.1f}s", flush=True)

    if only:                       # single-slide test run — don't emit whole decks
        return None

    outputs = []
    project = cfg.get("project", "Deck")

    if "mp4" in formats and "video" in steps and segs:
        out = _fmt_out(cfg, root, "mp4")
        print("concatenating final video...", flush=True)
        video.concat(segs, out, build)
        m, sec = divmod(int(total), 60)
        outputs.append((out, f"{m}m {sec}s, {len(segs)} slides"))

    if "pptx" in formats:
        dest = _fmt_out(cfg, root, "pptx")
        if export.to_pptx(built, dest, fsize, project):
            outputs.append((dest, f"pptx, {len(built)} slides"))

    if "html" in formats:
        dest = _fmt_out(cfg, root, "html")
        if export.to_html(built, dest, fsize, project):
            outputs.append((dest, f"html, {len(built)} slides"))

    for path, info in outputs:
        print(f"DONE -> {path}  ({info})")
    return [p for p, _ in outputs] or None
