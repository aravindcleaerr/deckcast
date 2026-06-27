import pytest
from deckcast import export


def test_ts_format():
    assert export._ts(0) == "00:00:00,000"
    assert export._ts(3661.5) == "01:01:01,500"


def test_srt_times_and_skips_silent(tmp_path):
    dest = tmp_path / "o.srt"
    out = export.to_srt([("hello", 2.0), ("", 3.0), ("world", 1.5)], dest)
    assert out is not None
    txt = dest.read_text(encoding="utf-8")
    assert txt.count("-->") == 2                 # silent middle slide emits no cue
    assert "hello" in txt and "world" in txt
    # world starts after hello(2) + silent(3) = 5.0s
    assert "00:00:05,000 --> 00:00:06,500" in txt


def test_srt_all_silent_returns_none(tmp_path):
    assert export.to_srt([("", 2.0)], tmp_path / "x.srt") is None


def test_html_self_contained(frames, tmp_path):
    dest = tmp_path / "deck.html"
    export.to_html(frames, dest, (1920, 1080), "MyProject")
    html = dest.read_text(encoding="utf-8")
    assert html.count('class="slide"') == 3
    assert "MyProject" in html
    assert "data:image/png;base64," in html       # frames embedded


def test_html_skips_missing_frames(tmp_path):
    out = export.to_html([{"frame": tmp_path / "nope.png", "narration": "x"}],
                         tmp_path / "d.html", (1920, 1080))
    assert out is None


def test_pptx(frames, tmp_path):
    pytest.importorskip("pptx")
    dest = tmp_path / "deck.pptx"
    export.to_pptx(frames, dest, (1920, 1080))
    from pptx import Presentation
    assert len(Presentation(str(dest)).slides._sldIdLst) == 3


def test_pdf(frames, tmp_path):
    pytest.importorskip("PIL")
    dest = tmp_path / "deck.pdf"
    export.to_pdf(frames, dest, (1920, 1080))
    assert dest.exists() and dest.stat().st_size > 0
