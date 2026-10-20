"""Automated tests. They run offline and cost nothing.

Run them with:  python -m pytest
"""

import json

import pytest

from briefbuilder.agent import REQUIRED_KEYS, brief_to_markdown, generate_brief, parse_brief_json


def test_mock_brief_has_every_section():
    brief = generate_brief("content briefs", mock=True)
    for key in REQUIRED_KEYS:
        assert key in brief
    assert brief["research_source"].startswith("mock")


def test_empty_keyword_is_rejected():
    with pytest.raises(ValueError):
        generate_brief("   ", mock=True)


def test_citation_answer_is_quotable_length():
    words = len(generate_brief("seo", mock=True)["citation_ready_answer"].split())
    assert 40 <= words <= 60


def test_parse_handles_chatty_reply():
    raw = 'Sure, here it is:\n' + json.dumps({"search_intent": "x", "faqs": [{"question": "q", "answer": "a"}]}) + "\nHope that helps!"
    data = parse_brief_json(raw)
    assert data["search_intent"] == "x"
    assert data["outline"] == []  # missing key filled with a safe default


def test_parse_replaces_wrong_types():
    data = parse_brief_json(json.dumps({"outline": "not a list", "target_word_count": "lots"}))
    assert data["outline"] == [] and data["target_word_count"] == 1500


def test_parse_without_json_fails_clearly():
    with pytest.raises(ValueError):
        parse_brief_json("no braces here")


def test_markdown_contains_key_sections():
    md = brief_to_markdown(generate_brief("aeo", mock=True))
    for heading in ["## Outline", "## FAQs", "## Competitor gaps", "## Citation-ready answer", "## AEO checklist"]:
        assert heading in md
