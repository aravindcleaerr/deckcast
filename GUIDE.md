# deckcast — How-To Guide

Turn a list of slides (or just a topic) into a **narrated MP4**. Reusable in any project,
free image + voice backends, and works with **any LLM or none**.

This guide is the practical, end-to-end manual. For a 30-second overview see
[README.md](README.md).

---

## Contents

1. [What it does](#1-what-it-does)
2. [Install & prerequisites](#2-install--prerequisites)
3. [Three ways to use it](#3-three-ways-to-use-it)
4. [Quickstart](#4-quickstart)
5. [Commands](#5-commands)
6. [Config reference](#6-config-reference)
7. [Slide fields](#7-slide-fields)
8. [Image providers](#8-image-providers)
9. [Voice / narration](#9-voice--narration)
10. [LLM providers (any of them)](#10-llm-providers-any-of-them)
11. [Using your own HTML deck](#11-using-your-own-html-deck)
12. [Iterating fast](#12-iterating-fast)
13. [Output & build files](#13-output--build-files)
14. [Troubleshooting](#14-troubleshooting)
15. [Recipes](#15-recipes)

---

## 1. What it does

deckcast runs a five-stage pipeline. Each stage is optional and composable:

```
author  →  images  →  frames   →  tts      →  video
(LLM,      (free      (headless    (free       (ffmpeg
 optional)  FLUX)      Chrome)      edge-tts)    assembly)
```

- **author** *(optional, any LLM)* — writes image prompts + narration (or designs the whole deck).
- **images** — generates one image per slide from its `image_prompt` (free).
- **frames** — renders each slide to a 1920×1080 PNG: either a **built-in branded slide**, or a screenshot of **your own HTML deck**.
- **tts** — neural voiceover per slide (free, no key).
- **video** — each slide is held for the length of its narration, then concatenated to one MP4.

---

## 2. Install & prerequisites

**System tools** (must be on `PATH`):

| Tool | Why | Install |
|------|-----|---------|
| `ffmpeg` (+`ffprobe`) | assemble video | `apt install ffmpeg` / `brew install ffmpeg` |
| Google Chrome or Chromium | render slide frames | system package |

**Python** (3.9+):

```bash
cd deckcast
pip install -e .          # installs the `deckcast` command + deps (edge-tts, pyyaml)
# or, without installing:  pip install -r requirements.txt  &&  python -m deckcast ...
```

**Verify everything:**

```bash
deckcast doctor
```

```
  OK   chrome/chromium: /usr/bin/google-chrome
  OK   ffmpeg: /usr/bin/ffmpeg
  OK   ffprobe: /usr/bin/ffprobe
  OK   edge-tts (python)
All prerequisites present.
```

---

## 3. Three ways to use it

| Mode | You provide | LLM needed? | Best for |
|------|-------------|-------------|----------|
| **Manual** | Every slide's `title`, `image_prompt`, `narration` | No | Full control, exact wording |
| **LLM-assisted** | `title`/`topic` per slide; LLM fills `image_prompt` + `narration` | Yes | You set structure, AI writes copy |
| **Autonomous** | One `brief:` (no slides) | Yes | "Topic in, video out" |

You can mix them: any slide that already has `image_prompt`/`narration` is left untouched
by the LLM, so hand-write the ones you care about and let the LLM fill the rest.

---

## 4. Quickstart

```bash
export HF_TOKEN=hf_xxx                 # free image token (see §8) — or use pollinations / none
deckcast run examples/quickstart.yaml  # -> out/quickstart.mp4
```

Autonomous (one command, topic → video):

```bash
export HF_TOKEN=hf_xxx
export OPENAI_API_KEY=sk-...           # or any provider in §10
deckcast create "a 6-slide intro to our product for investors" --slides 6 --build
```

---

## 5. Commands

### `deckcast run <config> [--steps ...] [--only N]`
Build the video from a config file.
- `--steps author,images,frames,tts,video` — run only a subset (comma-separated).
- `--only N` — process a single slide number (great for testing one slide).

```bash
deckcast run deck.yaml
deckcast run deck.yaml --only 3                 # just slide 3
deckcast run deck.yaml --steps frames,tts,video # skip image regeneration
```

### `deckcast create "<topic>" [options]`
Autonomous: the LLM designs a whole deck and writes a **reviewable** config.

| Option | Meaning |
|--------|---------|
| `--out PATH` | where to write the config (default `deck.yaml`) |
| `--slides N` | target slide count (LLM decides if omitted) |
| `--base PATH` | a config supplying `theme`/`image`/`voice`/`llm` (its `slides` are ignored) |
| `--brand NAME` | brand override |
| `--base-url`, `--model`, `--api-key-env` | LLM endpoint (see §10) |
| `--image-provider hf\|pollinations\|none` | image backend |
| `--voice NAME` | edge-tts voice |
| `--build` | render the video immediately after writing the config |

```bash
deckcast create "pitch for a senior-care trust platform, India-first" \
  --slides 9 --brand KuboHomes --model gpt-4o-mini --out kubo.yaml --build
```

### `deckcast doctor`
Check that Chrome, ffmpeg, and edge-tts are available.

---

## 6. Config reference

A deck is a YAML (or JSON) file. Fully-annotated:

```yaml
project: "My Deck"             # label only
output: "out/my-deck.mp4"      # output path (relative to the config file)
brief: "..."                   # OPTIONAL — autonomous mode: LLM designs slides from this

theme:
  brand:   "KuboHomes"         # shown as a chip + footer on built-in slides
  accent:  "#1f6f63"           # primary (eyebrow, brand chip)
  accent2: "#d98a3d"           # secondary (bullet markers, accents)
  bg:      "#fbf8f2"           # slide background when there is no image
  ink:     "#1d2a27"           # body text color (light slides)

image:
  provider: hf                 # hf | pollinations | none
  model:    schnell            # schnell (free) | dev (NOT free on HF, see §8)
  token_env: HF_TOKEN          # env var holding the HF token
  style:    "candid documentary photograph, soft natural light, realistic, sharp"  # appended to every image_prompt
  width:    1344
  height:   768
  seed:     null               # optional int — fixes/var­ies composition (see §12)

voice:
  provider: edge               # edge (edge-tts)
  name:     "en-IN-NeerjaNeural"
  rate:     "-4%"              # speed, e.g. "+0%", "-10%"

frames:
  mode:      builtin           # builtin | deck
  deck_path: null              # required when mode=deck (your HTML deck)
  width:     1920
  height:    1080

llm:                           # OPTIONAL — used by author/create. OpenAI-compatible.
  enabled:     false
  base_url:    "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"   # "" for local providers with no key
  model:       "gpt-4o-mini"
  temperature: 0.7

video:
  fps:           30
  tail_seconds:  0.8           # silence held after each narration
  audio_bitrate: "192k"

slides:                        # omit entirely when using `brief:`
  - eyebrow: "Welcome"
    title:   "..."
    subtitle: "..."            # use subtitle OR bullets
    bullets: ["...", "..."]
    image_prompt: "..."        # or `image: path/to.png` to use your own file
    narration: "..."
    dark: false                # true = dark overlay for white text
```

---

## 7. Slide fields

| Field | Used by | Notes |
|-------|---------|-------|
| `eyebrow` | built-in frame | small uppercase kicker |
| `title` | built-in frame | headline (auto-sizes to length) |
| `subtitle` | built-in frame | one supporting line |
| `bullets` | built-in frame | list of 3–5 short phrases (use *instead of* subtitle) |
| `image` | image step | path to your own image (skips generation) |
| `image_prompt` | image step | text-to-image prompt; `style` is appended |
| `narration` | tts | the spoken line(s) for this slide |
| `topic` | author (LLM) | hint the LLM uses to write `image_prompt`+`narration` |
| `dark` | built-in frame | `true` → dark overlay + light text |

In `deck` frame mode, only `narration` (and `image_prompt` if generating) matter — the
visuals come from your HTML deck, not these fields.

---

## 8. Image providers

### `hf` — Hugging Face FLUX (recommended, free)
Higher quality, 1344×768 clean PNGs.

1. Create a free token: <https://huggingface.co/settings/tokens> (type **Read**).
2. `export HF_TOKEN=hf_xxx` (or set `image.token_env` to your own var name).

> **Model note:** `model: schnell` is free. `model: dev` (FLUX.1-dev) is **no longer free**
> on Hugging Face's serverless tier (returns HTTP 410) — it needs a paid provider. Stick
> with `schnell` unless you've wired a paid endpoint.

### `pollinations` — no key at all
Zero setup, but capped at ~1024px and lower fidelity. Good for a fast first pass.

```yaml
image: { provider: pollinations }
```

### `none` — bring your own images
Skip generation; set `image:` to a file path on each slide (or rely on `deck` mode).

```yaml
image: { provider: none }
slides:
  - title: "..." 
    image: "assets/cover.jpg"
```

---

## 9. Voice / narration

Voiceover uses **edge-tts** (Microsoft neural voices, free, no key).

```bash
edge-tts --list-voices | grep en-       # browse English voices
```

Good picks:

| Voice | Accent / gender |
|-------|-----------------|
| `en-IN-NeerjaNeural` | Indian, female (default) |
| `en-IN-PrabhatNeural` | Indian, male |
| `en-US-AriaNeural` | US, female |
| `en-GB-SoniaNeural` | UK, female |

```yaml
voice: { name: "en-IN-PrabhatNeural", rate: "-4%" }
```

---

## 10. LLM providers (any of them)

The author/create steps call a standard **OpenAI-compatible** `/chat/completions` endpoint.
Switch providers by changing three fields — nothing else.

| Provider | `base_url` | `api_key_env` | example `model` |
|----------|-----------|----------------|------------------|
| OpenAI | `https://api.openai.com/v1` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | `meta-llama/llama-3.1-70b-instruct` |
| Together | `https://api.together.xyz/v1` | `TOGETHER_API_KEY` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| **Ollama (local)** | `http://localhost:11434/v1` | `""` (none) | `llama3.1` |
| **LM Studio (local)** | `http://localhost:1234/v1` | `""` (none) | *(loaded model)* |

```yaml
llm:
  enabled: true
  base_url: "http://localhost:11434/v1"   # fully local, no key, no cost
  api_key_env: ""
  model: "llama3.1"
```

Then export the key (skip for local): `export OPENAI_API_KEY=sk-...`

---

## 11. Using your own HTML deck

Set `frames.mode: deck` to screenshot an existing deck instead of the built-in template:

```yaml
frames:
  mode: deck
  deck_path: "docs/MyDeck.html"
slides:
  - narration: "First slide narration..."
  - narration: "Second slide narration..."
  # one entry per slide, in order
```

Your deck must honor a tiny **contract** so deckcast can grab one clean frame per slide:

- **`#N`** in the URL shows slide *N* (1-based).
- **`?clean`** in the query hides nav chrome and freezes animations.

Minimal JS to add to any deck (this is exactly what the KuboHomes deck uses):

```html
<script>
  // ?clean -> hide chrome + freeze animations for capture
  if (location.search.indexOf('clean') !== -1) document.body.classList.add('clean');
  // #N -> jump to that slide
  const n = parseInt((location.hash || '').replace('#',''), 10) || 1;
  showSlide(n - 1);   // your function to display slide n
</script>
<style>
  body.clean .nav, body.clean .footer { display:none !important; }
  body.clean * { animation:none !important; transition:none !important; }
</style>
```

---

## 12. Iterating fast

- **One slide at a time:** `deckcast run deck.yaml --only 4`
- **Skip image regen** (text/voice tweaks): `--steps frames,tts,video`
- **Re-narrate only:** `--steps tts,video`
- **Vary an image:** the `hf` `schnell` model is *deterministic per seed*. To get a different
  composition, change `image.seed` (any int). To reproduce one you liked, keep that seed.
- **Cheaper drafts:** set `image.provider: pollinations` (no key) while drafting, switch to
  `hf` for the final render.

---

## 13. Output & build files

- **Final video:** `output:` path (default `out/<name>.mp4`) — 1920×1080, H.264 + AAC.
- **Intermediates:** `build_deckcast/` next to your config —
  `frames/`, `images/`, `audio/`, `segments/`, `segments.txt`.
  Safe to delete anytime; it's all regenerated. (Add it to `.gitignore`.)

---

## 14. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `doctor` shows MISSING chrome/ffmpeg | not installed / not on PATH | install them (§2) |
| `HF image error (HTTP 401/403)` | bad token or license not accepted | check `HF_TOKEN`; for `dev` accept the model license |
| `HF image error (HTTP 410)` | `model: dev` not free on HF serverless | use `model: schnell` or a paid provider |
| Image generation "failed", frame has plain background | provider hiccup / empty prompt | re-run (`--only N`); check `image_prompt` is set |
| Same image every re-run | `schnell` is deterministic per seed | set a different `image.seed` (§12) |
| `LLM call failed (HTTP 401)` | missing or wrong API key | export the key named in `api_key_env` |
| `Autonomous mode needs llm.enabled=true` | `create`/brief without LLM config | set `llm.enabled` + `base_url`/`model` |
| Fonts look like fallback serif | no network for Google Fonts during capture | ensure network, or accept the fallback |
| `PyYAML not installed` | missing dep | `pip install pyyaml` or use a `.json` config |
| Deck-mode frames blank/wrong slide | deck doesn't honor `?clean#N` | add the contract snippet (§11) |

---

## 15. Recipes

**A. Fully manual, your own images, no internet model:**
```yaml
image: { provider: none }
llm: { enabled: false }
slides:
  - { title: "Cover", image: "img/cover.jpg", narration: "Welcome." }
  - { title: "Next",  image: "img/next.jpg",  narration: "Here's the plan." }
```
```bash
deckcast run deck.yaml
```

**B. You write the outline, AI writes the copy:**
```yaml
llm: { enabled: true, base_url: "https://api.openai.com/v1", api_key_env: "OPENAI_API_KEY", model: "gpt-4o-mini" }
slides:
  - { topic: "cover: the problem with finding care homes" }
  - { topic: "our solution: a trust layer" }
  - { topic: "call to action" }
```
```bash
export OPENAI_API_KEY=sk-... HF_TOKEN=hf_xxx
deckcast run deck.yaml
```

**C. Topic → video, local model, no cost:**
```bash
# Ollama running locally with llama3.1 pulled
export HF_TOKEN=hf_xxx
deckcast create "a 7-slide overview of our open-source project" \
  --base-url http://localhost:11434/v1 --api-key-env "" --model llama3.1 --build
```

**D. Narrate an existing branded HTML deck:**
```yaml
frames: { mode: deck, deck_path: "docs/Deck.html" }
image:  { provider: none }
slides:
  - { narration: "..." }   # one per slide, in order
```
