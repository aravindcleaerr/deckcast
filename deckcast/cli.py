"""deckcast CLI — build a narrated MP4 from a config, in any project, with any LLM."""
import argparse, sys
from pathlib import Path
from . import config, pipeline, author
from .util import CHROME, FFMPEG, FFPROBE


def doctor():
    ok = True
    for name, val in [("chrome/chromium", CHROME), ("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)]:
        print(f"  {'OK ' if val else 'MISSING'}  {name}: {val or '-'}")
        ok = ok and bool(val)
    try:
        import edge_tts  # noqa
        print("  OK   edge-tts (python)")
    except ImportError:
        print("  MISSING  edge-tts (pip install edge-tts)"); ok = False
    print("All prerequisites present." if ok else "Install the MISSING items above.")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(prog="deckcast",
                                 description="Config-driven narrated-video builder (LLM-agnostic).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="build the video from a config file")
    r.add_argument("config", help="path to .yaml or .json config")
    r.add_argument("--steps", help="comma list subset of: " + ",".join(pipeline.STEPS))
    r.add_argument("--only", type=int, help="process a single slide number (test)")

    c = sub.add_parser("create", help="autonomous: design a whole deck from one topic (LLM)")
    c.add_argument("topic", help="the brief, e.g. \"investor pitch for a senior-care app\"")
    c.add_argument("--out", default="deck.yaml", help="where to write the generated config")
    c.add_argument("--base", help="config supplying theme/image/voice/llm (slides ignored)")
    c.add_argument("--slides", type=int, help="target slide count (LLM decides if omitted)")
    c.add_argument("--brand", help="brand name override")
    c.add_argument("--base-url", help="LLM endpoint (OpenAI-compatible)")
    c.add_argument("--model", help="LLM model id")
    c.add_argument("--api-key-env", help="env var holding the LLM key ('' for local)")
    c.add_argument("--image-provider", choices=["hf", "pollinations", "none"])
    c.add_argument("--voice", help="edge-tts voice name")
    c.add_argument("--build", action="store_true", help="build the video after writing the config")

    sub.add_parser("doctor", help="check prerequisites (chrome, ffmpeg, edge-tts)")

    args = ap.parse_args(argv)
    if args.cmd == "doctor":
        sys.exit(0 if doctor() else 1)
    if args.cmd == "create":
        return create(args)

    cfg = config.load(args.config)
    steps = args.steps.split(",") if args.steps else None
    pipeline.run(cfg, steps=steps, only=args.only)


def create(args):
    import yaml
    raw = config.read_raw(args.base) if args.base else {}
    cfg = config._merge(config.DEFAULTS, raw)
    cfg["llm"]["enabled"] = True
    for flag, path in [(args.base_url, ("llm", "base_url")), (args.model, ("llm", "model")),
                       (args.brand, ("theme", "brand")), (args.voice, ("voice", "name")),
                       (args.image_provider, ("image", "provider"))]:
        if flag:
            cfg[path[0]][path[1]] = flag
    if args.api_key_env is not None:
        cfg["llm"]["api_key_env"] = args.api_key_env

    print(f"designing deck from topic ({cfg['llm']['model']})...", flush=True)
    slides = author.outline(args.topic, cfg["theme"], cfg["llm"], args.slides)

    cfg["project"] = args.topic[:70]
    cfg["brief"] = args.topic
    cfg["slides"] = slides
    dump = {k: v for k, v in cfg.items() if not k.startswith("_")}
    out = Path(args.out)
    out.write_text(yaml.safe_dump(dump, sort_keys=False, allow_unicode=True, width=100))
    print(f"wrote {len(slides)}-slide deck -> {out}  (review/edit, then `deckcast run {out}`)")

    if args.build:
        pipeline.run(config.load(out))


if __name__ == "__main__":
    main()
