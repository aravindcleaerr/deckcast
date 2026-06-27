from deckcast import pipeline


def test_fmt_out_default_suffix(tmp_path):
    cfg = {"output": "out/show.mp4"}
    assert pipeline._fmt_out(cfg, tmp_path, "pdf") == tmp_path / "out" / "show.pdf"


def test_fmt_out_explicit_relative(tmp_path):
    cfg = {"output": "out/show.mp4", "html": "web/deck.html"}
    assert pipeline._fmt_out(cfg, tmp_path, "html") == tmp_path / "web" / "deck.html"


def test_fmt_out_explicit_absolute(tmp_path):
    target = tmp_path / "abs.pptx"
    cfg = {"output": "out/show.mp4", "pptx": str(target)}
    assert pipeline._fmt_out(cfg, tmp_path, "pptx") == target


def test_fresh(tmp_path):
    missing = tmp_path / "missing"
    assert not pipeline._fresh(missing)
    empty = tmp_path / "empty"; empty.write_bytes(b"")
    assert not pipeline._fresh(empty)
    real = tmp_path / "real"; real.write_bytes(b"x")
    assert pipeline._fresh(real)
