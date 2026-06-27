import json
import pytest
from deckcast import config


def test_merge_is_deep_and_pure():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    out = config._merge(base, {"a": {"y": 9}, "c": 4})
    assert out == {"a": {"x": 1, "y": 9}, "b": 3, "c": 4}
    assert base["a"]["y"] == 2          # original not mutated


def test_load_applies_defaults_and_dir(tmp_path):
    p = tmp_path / "deck.json"
    p.write_text(json.dumps({"slides": [{"title": "x"}]}))
    cfg = config.load(str(p))
    assert cfg["_dir"] == str(tmp_path)
    assert cfg["formats"] == ["mp4"]
    assert cfg["output"].endswith("deckcast.mp4")
    # newer defaults are present
    assert "still_seconds" in cfg["video"] and "captions" in cfg["video"]
    assert "logo" in cfg["theme"]


def test_load_requires_slides_or_brief(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({}))
    with pytest.raises(SystemExit):
        config.load(str(p))
