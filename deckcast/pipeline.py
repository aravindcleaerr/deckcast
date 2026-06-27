"""Orchestrate the full pipeline: author -> images -> frames -> tts -> video.

Outputs are selected by `formats` (default ["mp4"]): mp4 (narrated video),
pptx, and/or html. pptx/html reuse the rendered frames, so tts/video stages
are skipped automatically when no mp4 is requested.
"""
from pathlib import Path
from . import author, images, frames, tts, video, export
from .util import ffprobe_duration

STEPS = ["author", "images", "frames", "tts", "video"]
FORMATS = ["mp4", "pptx", "pdf", "html"]


def _fmt_out(cfg, root, ext):
    explicit = cfg.get(ext)
    p = Path(explicit) if explicit else Path(cfg["output"]).with_suffix("." + ext)
    return p if p.is_absolute() else root / p


def _fresh(path):
    p = Path(path)
    return p.exists() and p.stat().st_size > 0


def run(cfg, steps=None, only=None, formats=None, resume=False):
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

    segs, total, built, caption_rows = [], 0.0, [], []
    for i in idxs:
        s = slides[i]
        tag = f"slide {i+1:02d}"

        # 2) image
        img_path, img_made = None, False
        if fr["mode"] == "builtin":
            if s.get("image"):                       # user-supplied path
                p = Path(s["image"])
                img_path = p if p.is_absolute() else root / p
            elif "images" in steps and s.get("image_prompt"):
                img_path = idir / f"img-{i+1:02d}.png"
                if resume and _fresh(img_path):
                    print(f"{tag}: image cached", flush=True)
                else:
                    print(f"{tag}: generating image ({img['provider']})...", flush=True)
                    if images.generate(s["image_prompt"], img_path, img, img.get("style", "")):
                        img_made = True
                    else:
                        print(f"{tag}: image generation failed — frame will use solid background")
                        img_path = None

        # 3) frame
        frame = fdir / f"frame-{i+1:02d}.png"
        if "frames" in steps:
            if resume and _fresh(frame) and not img_made:
                print(f"{tag}: frame cached", flush=True)
            else:
                print(f"{tag}: rendering frame...", flush=True)
                if fr["mode"] == "deck":
                    frames.deck_frame(fr["deck_path"], i, frame, fsize)
                else:
                    frames.builtin_frame(s, i, len(slides), theme, img_path, frame, fsize)
        built.append({"frame": frame, "narration": s.get("narration"), "title": s.get("title")})

        # 4) voiceover
        audio = adir / f"audio-{i+1:02d}.mp3"
        text = (s.get("narration") or "").strip()
        audio_made = False
        if "tts" in steps:
            if resume and _fresh(audio):
                print(f"{tag}: voiceover cached", flush=True)
            elif text:
                print(f"{tag}: voiceover ({voice['name']})...", flush=True)
                tts.synth(text, audio, voice)
                audio_made = True
            else:
                Path(audio).unlink(missing_ok=True)   # no narration -> silent slide
                print(f"{tag}: no narration — silent slide", flush=True)

        # 5) segment
        if "video" in steps:
            seg = sdir / f"seg-{i+1:02d}.mp4"
            if resume and _fresh(seg) and not (img_made or audio_made):
                dur = ffprobe_duration(seg)
                print(f"{tag}: segment cached {dur:.1f}s", flush=True)
            else:
                has_audio = _fresh(audio)
                base = (ffprobe_duration(audio) + vid["tail_seconds"]) if has_audio \
                    else vid.get("still_seconds", 3.0)
                dur = max(base, vid.get("min_seconds", 0) or 0, float(s.get("duration") or 0))
                video.segment(frame, audio if has_audio else None, seg, fsize, vid["fps"],
                              dur, vid["audio_bitrate"])
                print(f"{tag}: segment {dur:.1f}s", flush=True)
            segs.append(seg); total += dur
            caption_rows.append((text, dur))

    if only:                       # single-slide test run — don't emit whole decks
        return None

    outputs = []
    project = cfg.get("project", "Deck")

    if "mp4" in formats and "video" in steps and segs:
        out = _fmt_out(cfg, root, "mp4")
        tdur = float(vid.get("transition") or 0)
        if tdur > 0 and len(segs) > 1:
            print(f"concatenating with {tdur:g}s crossfades...", flush=True)
            video.concat_xfade(segs, out, tdur, vid["fps"], vid["audio_bitrate"], build)
            total -= tdur * (len(segs) - 1)
        else:
            print("concatenating final video...", flush=True)
            video.concat(segs, out, build)
        music = vid.get("music")
        if music:
            mp = Path(music)
            mp = mp if mp.is_absolute() else root / mp
            if mp.exists():
                print("mixing background music...", flush=True)
                video.add_music(out, mp, vid.get("music_volume", 0.12))
            else:
                print(f"music not found ({mp}) — skipping", flush=True)
        m, sec = divmod(int(total), 60)
        outputs.append((out, f"{m}m {sec}s, {len(segs)} slides"))
        if vid.get("captions", True):
            srt = export.to_srt(caption_rows, out.with_suffix(".srt"))
            if srt:
                outputs.append((srt, f"captions, {len(segs)} slides"))

    if "pptx" in formats:
        dest = _fmt_out(cfg, root, "pptx")
        if export.to_pptx(built, dest, fsize, project):
            outputs.append((dest, f"pptx, {len(built)} slides"))

    if "pdf" in formats:
        dest = _fmt_out(cfg, root, "pdf")
        if export.to_pdf(built, dest, fsize, project):
            outputs.append((dest, f"pdf, {len(built)} slides"))

    if "html" in formats:
        dest = _fmt_out(cfg, root, "html")
        if export.to_html(built, dest, fsize, project):
            outputs.append((dest, f"html, {len(built)} slides"))

    for path, info in outputs:
        print(f"DONE -> {path}  ({info})")
    return [p for p, _ in outputs] or None
