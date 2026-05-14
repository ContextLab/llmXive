"""parse_action tests (T016, US1, FR-006).

Pure-Python. Drives :func:`personality.parse_action` against the canned
action fixtures and bad inputs, asserting the JSON-schema and per-action
required-fields rules are enforced (data-model.md E4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


class TestParseActionFixtures:
    def test_comment_fixture(self) -> None:
        raw = (FIXTURES / "action_comment.json").read_text(encoding="utf-8")
        a = p.parse_action(raw)
        assert a.action == "comment"
        assert a.target_project_id == "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
        assert a.target_artifact_kind == "spec"
        assert a.target_artifact_path.endswith("spec.md")
        assert "System 1" in a.content
        assert a.arxiv_url is None

    def test_contribute_fixture(self) -> None:
        raw = (FIXTURES / "action_contribute.json").read_text(encoding="utf-8")
        a = p.parse_action(raw)
        assert a.action == "contribute"
        assert a.target_artifact_kind == "tasks"
        assert "Proposed edit" in a.content

    def test_propose_arxiv_fixture(self) -> None:
        raw = (FIXTURES / "action_propose_arxiv.json").read_text(encoding="utf-8")
        a = p.parse_action(raw)
        assert a.action == "propose_arxiv"
        assert a.arxiv_url == "https://arxiv.org/abs/2401.00001"
        assert "motif disruption" in a.arxiv_search_terms

    def test_abstain_fixture(self) -> None:
        raw = (FIXTURES / "action_abstain.json").read_text(encoding="utf-8")
        a = p.parse_action(raw)
        assert a.action == "abstain"
        assert a.target_project_id is None
        assert a.content is None
        assert a.arxiv_url is None


class TestParseActionRejections:
    def test_bad_json_raises(self) -> None:
        with pytest.raises(p.ParseError) as exc:
            p.parse_action("not json at all")
        assert "no JSON" in str(exc.value) or "parse error" in str(exc.value)

    def test_missing_action_field(self) -> None:
        with pytest.raises(p.ParseError):
            p.parse_action(json.dumps({"reason": "no action"}))

    def test_unknown_action_value(self) -> None:
        with pytest.raises(p.ParseError) as exc:
            p.parse_action(json.dumps({"action": "lurk", "reason": "..."}))
        assert "lurk" in str(exc.value)

    def test_comment_missing_target(self) -> None:
        with pytest.raises(p.ParseError) as exc:
            p.parse_action(json.dumps({
                "action": "comment", "reason": "...", "content": "ok",
            }))
        assert "target." in str(exc.value)

    def test_comment_missing_content(self) -> None:
        with pytest.raises(p.ParseError):
            p.parse_action(json.dumps({
                "action": "comment", "reason": "...",
                "target": {"project_id": "PROJ-1", "artifact_kind": "spec",
                           "artifact_path": "p/spec.md"},
            }))

    def test_propose_arxiv_bad_url(self) -> None:
        with pytest.raises(p.ParseError) as exc:
            p.parse_action(json.dumps({
                "action": "propose_arxiv", "reason": "...",
                "content": "rationale",
                "arxiv": {"url": "https://example.com/paper", "search_terms": []},
            }))
        assert "arxiv.url" in str(exc.value)

    def test_propose_arxiv_no_rationale(self) -> None:
        with pytest.raises(p.ParseError):
            p.parse_action(json.dumps({
                "action": "propose_arxiv", "reason": "...",
                "arxiv": {"url": "https://arxiv.org/abs/2401.00001", "search_terms": []},
            }))

    def test_over_size_content_rejected(self) -> None:
        big = " ".join("word" + str(i) for i in range(3000))  # > 2000 words
        with pytest.raises(p.ParseError) as exc:
            p.parse_action(json.dumps({
                "action": "comment", "reason": "...",
                "target": {"project_id": "PROJ-1", "artifact_kind": "spec",
                           "artifact_path": "p/spec.md"},
                "content": big,
            }))
        assert "2000-word" in str(exc.value)

    def test_root_not_object(self) -> None:
        with pytest.raises(p.ParseError):
            p.parse_action(json.dumps([1, 2, 3]))


class TestParseActionResilience:
    def test_extracts_json_from_surrounding_prose(self) -> None:
        # LLMs sometimes wrap JSON in stray prose. Parser should tolerate it.
        raw = (
            "Here is my response:\n"
            '{"action": "abstain", "reason": "Nothing here interests me this tick."}\n'
            "Thank you!\n"
        )
        a = p.parse_action(raw)
        assert a.action == "abstain"
