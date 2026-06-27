import pytest
from deckcast import author


def test_extract_plain_array():
    assert author._extract_array('[{"a": 1}]') == [{"a": 1}]


def test_extract_json_fenced():
    text = "```json\n[{\"a\": 1}, {\"b\": 2}]\n```"
    assert len(author._extract_array(text)) == 2


def test_extract_with_surrounding_prose():
    text = "Sure, here it is:\n[{\"x\": 1}]\nHope that helps!"
    assert author._extract_array(text) == [{"x": 1}]


def test_extract_rejects_non_array():
    with pytest.raises(Exception):
        author._extract_array('{"a": 1}')


def test_parse_enforces_count():
    with pytest.raises(Exception):
        author._parse('[{"a": 1}]', 3)
