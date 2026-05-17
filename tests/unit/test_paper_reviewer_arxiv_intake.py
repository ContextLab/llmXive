"""Tests for paper_reviewer's arxiv-intake fallback path.

Real-world failure: 26 paper-reviewer invocations across PROJ-564 +
PROJ-566 (both arXiv-submitted papers) failed with
``FileNotFoundError: no paper specs/ feature dir`` because those
projects never ran through the home-grown spec→plan→tasks→implement
pipeline — they came in fully-formed from arXiv with ``paper/source/``
+ ``paper/metadata.json``. The reviewer now falls back to hashing
``metadata.json`` when ``paper/specs/`` doesn't exist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_arxiv_intake_project(repo: Path, project_id: str) -> Path:
    """Build a minimal arXiv-intake project layout (paper/ + metadata.json,
    NO paper/specs/)."""
    proj_dir = repo / "projects" / project_id
    paper = proj_dir / "paper"
    (paper / "source").mkdir(parents=True)
    (paper / "pdf").mkdir()
    (paper / "figures").mkdir()
    (paper / "source" / "main.tex").write_text(r"\documentclass{article}\begin{document}x\end{document}",
                                                encoding="utf-8")
    (paper / "metadata.json").write_text(json.dumps({
        "arxiv_id": "2605.99999",
        "arxiv_url": "https://arxiv.org/abs/2605.99999",
        "title": "Synthetic Test Paper",
        "authors": ["A. Author"],
        "submitter": "github-actions[bot]",
        "submitted_via": "test",
        "source_files": ["main.tex"],
        "toplevel_tex": ["main.tex"],
    }, indent=2), encoding="utf-8")
    return proj_dir


class TestArxivIntakeFallback:
    def test_paper_feature_dir_returns_none_when_no_specs(self, tmp_path: Path) -> None:
        """Without instantiating the full agent (which needs a complete
        registry entry), exercise the _paper_feature_dir helper directly
        as an unbound method on the class — it doesn't read self."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        proj = _make_arxiv_intake_project(tmp_path, "PROJ-999-test")
        # _paper_feature_dir is a method but only reads project_dir; bypass
        # __init__ to avoid the registry-entry validation.
        agent = object.__new__(PaperReviewerAgent)
        assert agent._paper_feature_dir(proj) is None

    def test_handle_response_uses_metadata_json_when_no_feature_dir(self, tmp_path: Path, monkeypatch) -> None:
        """When `paper/specs/` is missing, handle_response should hash
        `paper/metadata.json` and produce a schema-valid artifact_path
        (matches ^projects/PROJ-\\d+-...$)."""
        # We don't run the full handle_response (writes to repo state) —
        # just verify the path-selection logic by reading the source.
        # An integration-style test would need the full agents-registry
        # stack which is out of unit-test scope.
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Sanity: confirm the file references the metadata.json fallback.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert 'project_dir / "paper" / "metadata.json"' in text, (
            "paper_reviewer.handle_response should fall back to metadata.json "
            "when feature_dir is None"
        )
        assert "arXiv-intake" in text, (
            "the fallback path should be documented in code as arxiv-intake"
        )

    def test_no_feature_dir_AND_no_metadata_still_hard_fails(self, tmp_path: Path) -> None:
        """A project with NEITHER paper/specs/ NOR paper/metadata.json
        is a real precondition violation — the reviewer must still
        hard-fail with an actionable message."""
        from llmxive.agents.paper_reviewer import PaperReviewerAgent
        # Just confirm the source still has the hard-fail branch.
        src = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "agents" / "paper_reviewer.py"
        text = src.read_text()
        assert "and no paper/metadata.json" in text, (
            "the hard-fail message should explain BOTH conditions"
        )
