# Changelog

All notable changes to deckcast are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **PPTX / PDF / HTML export.** `--formats mp4,pptx,pdf,html` (or `formats:` in config)
  emits a PowerPoint (full-bleed slides, narration as speaker notes), a PDF (one frame per
  page), and/or a self-contained, keyboard-navigable HTML deck — all from the same rendered
  frames. `tts`/`video` stages are skipped automatically when no `mp4` is requested. PPTX/PDF
  need the `[export]` extra (`pip install "deckcast[export]"`); HTML is stdlib-only.
- **`--resume`** reuses cached images/frames/audio/segments, so a failed or partial run
  continues in seconds instead of regenerating everything.
- **SRT captions.** Building `mp4` also writes a matching `.srt` sidecar timed to each
  slide (toggle with `video.captions`).
- **Crossfade transitions** (`video.transition`) and a **background-music bed**
  (`video.music`, `video.music_volume`) mixed under the narration.
- **Silent slides & timing control.** Slides with no narration render as silent holds of
  `video.still_seconds`; `video.min_seconds` floors narrated slides; per-slide `duration`
  extends on-screen time.
- **`theme.logo`** — a brand logo image in the corner (replaces the auto letter badge).
- **Retries** on TTS (edge-tts) and the LLM call so a transient network blip no longer
  aborts a long run.
- **Tests** (`tests/`, pytest) and CI now runs them plus a pptx/pdf/html export smoke.

### Changed
- `doctor` reports which output each prerequisite is needed for, checks for python-pptx,
  and falls back to the `imageio-ffmpeg` bundled ffmpeg binary when ffmpeg is not on PATH.

### Fixed
- **Windows support.** Detect Chrome/Edge from their standard install paths (previously
  only Linux binary names were searched), and build `file://` URLs with `Path.as_uri()`
  so Chrome actually loads slide background images (backslash paths silently failed,
  producing image-less frames).

[Unreleased]: https://github.com/aravindcleaerr/deckcast/compare/v0.1.0...HEAD

## [0.1.0] — 2026-06-26

Initial release.

### Added
- **Five-stage pipeline**: author → images → frames → tts → video.
- **`deckcast run <config>`** — build a narrated MP4 from a YAML/JSON config; `--steps`
  to run a subset, `--only N` to process a single slide.
- **`deckcast create "<topic>"`** — autonomous mode: an LLM designs the whole deck
  (titles, bullets, image prompts, narration) and writes a reviewable config; `--build`
  to render immediately. Also supported via a `brief:`-only config in `run`.
- **`deckcast doctor`** — prerequisite check (Chrome, ffmpeg, edge-tts).
- **LLM-agnostic** authoring via any OpenAI-compatible endpoint (OpenAI, Groq, Together,
  OpenRouter, or local Ollama / LM Studio) — or no LLM at all.
- **Free image backends**: Hugging Face FLUX.1-schnell (free token) and Pollinations
  (no key); plus `none` to use your own image files.
- **Free voice**: Microsoft `edge-tts` neural voices (no key).
- **Two frame modes**: a built-in branded slide renderer, or `deck` mode that screenshots
  your own HTML deck via the `?clean#N` contract.
- Docs: [README.md](README.md), full [GUIDE.md](GUIDE.md), and `examples/`
  (`quickstart.yaml`, `autonomous.yaml`).

[0.1.0]: https://github.com/aravindcleaerr/deckcast/releases/tag/v0.1.0
