# Changelog

All notable changes to deckcast are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **PPTX and HTML export.** `--formats mp4,pptx,html` (or `formats:` in config) emits a
  PowerPoint (full-bleed slides, narration as speaker notes) and/or a self-contained,
  keyboard-navigable HTML deck from the same rendered frames. `tts`/`video` stages are
  skipped automatically when no `mp4` is requested. PPTX needs the `[export]` extra
  (`pip install "deckcast[export]"`); HTML is stdlib-only.

### Fixed
- **Windows support.** Detect Chrome/Edge from their standard install paths (previously
  only Linux binary names were searched), and build `file://` URLs with `Path.as_uri()`
  so Chrome actually loads slide background images (backslash paths silently failed,
  producing image-less frames).

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

[0.1.0]: https://example.com/deckcast/releases/0.1.0
