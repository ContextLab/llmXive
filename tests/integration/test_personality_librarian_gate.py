"""Librarian-gate integration test (T064, FR-018).

When a personality's contribution contains URL / DOI / arXiv-id
patterns, the artifact MUST be held for human / librarian review
rather than auto-merged. Drives :func:`personality.dispatch` with
fixtures whose `content` contains a citation and asserts the artifact
lands under a `_held/` sub-directory + the outcome is
``librarian_held`` (which makes the rotation pointer HOLD per FR-017).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


def _make_repo(tmp_path: Path) -> Path:
    """Same skeleton as test_personality_tick.py."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "agents" / "prompts" / "personalities").mkdir(parents=True)
    shutil.copy(FIXTURES / "kahneman.md", repo / "agents" / "prompts" / "personalities" / "kahneman.md")
    pid = "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
    spec_dir = repo / "projects" / pid / "specs" / "001-mechanistic-interpretability-of-ctcf-bin"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# Spec\n\nA placeholder.", encoding="utf-8")
    (repo / "state" / "projects").mkdir(parents=True)
    (repo / "state" / "projects" / f"{pid}.yaml").write_text(
        yaml.safe_dump({
            "artifact_hashes": {}, "assigned_agent": None,
            "created_at": "2026-05-01T00:00:00+00:00",
            "current_stage": "in_progress", "failed_stage": None,
            "field": "biology", "human_escalation_reason": None,
            "id": pid,
            "last_run_id": None, "last_run_status": None,
            "points_paper": {}, "points_research": {},
            "revision_round": 0,
            "speckit_paper_dir": None,
            "speckit_research_dir": "specs/001-mechanistic-interpretability-of-ctcf-bin",
            "title": "CTCF Interpretability",
            "updated_at": "2026-05-13T00:00:00+00:00",
        }),
        encoding="utf-8",
    )
    return repo


def _make_persona() -> p.Personality:
    return p.Personality(
        slug="kahneman", display_name="Daniel Kahneman",
        summary="x", sources=["source-A", "source-B", "source-C"], prompt_body="body",
    )


class TestCitationPatternDetection:
    def test_url_pattern(self) -> None:
        assert p._contains_citation("See https://example.com/paper for the result.")

    def test_doi_pattern(self) -> None:
        assert p._contains_citation("doi:10.1038/nature12373 confirms this.")
        assert p._contains_citation("Found at 10.1101/2024.01.01.123456")

    def test_arxiv_id_pattern(self) -> None:
        assert p._contains_citation("Compare with arXiv:2401.00001 for context.")

    def test_no_citation_returns_false(self) -> None:
        assert not p._contains_citation("Plain prose with no URLs, DOIs, or arXiv ids.")


class TestLibrarianHold:
    def test_comment_with_citation_held(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        persona = _make_persona()
        # An action with a URL in its content body — must be held.
        action = p.Action(
            action="comment",
            reason="Cites a paper.",
            target_project_id="PROJ-001-mechanistic-interpretability-of-ctcf-bin",
            target_artifact_kind="spec",
            target_artifact_path=(
                "projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/"
                "specs/001-mechanistic-interpretability-of-ctcf-bin/spec.md"
            ),
            content=(
                "This connects to the literature: see https://example.com/paper "
                "and doi:10.1038/nature12373."
            ),
        )
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_LIBRARIAN_HELD
        # The committed paths must be UNDER a `_held/` directory.
        assert all("/_held/" in path for path in result.committed_paths), result.committed_paths
        # And the original review-file location is EMPTY (the file was moved).
        for path in result.committed_paths:
            assert (repo / path).is_file()

    def test_comment_without_citation_not_held(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        persona = _make_persona()
        action = p.Action(
            action="comment",
            reason="Pure prose.",
            target_project_id="PROJ-001-mechanistic-interpretability-of-ctcf-bin",
            target_artifact_kind="spec",
            target_artifact_path=(
                "projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/"
                "specs/001-mechanistic-interpretability-of-ctcf-bin/spec.md"
            ),
            content="No citations at all. Just a stylistic suggestion about clarity.",
        )
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_COMMITTED
        # File lands in the canonical reviews/research/ directory — NOT under _held/.
        assert all("/_held/" not in path for path in result.committed_paths)

    def test_pointer_holds_on_librarian_held(self, tmp_path: Path) -> None:
        """The hold is meaningful: rotation pointer must NOT advance per FR-017."""
        repo = _make_repo(tmp_path)
        # Prior pointer.
        p.write_rotation_state(
            p.RotationState(
                last_used="prior-slug", last_used_at="2026-05-13T00:00:00+00:00",
                last_outcome=p.OUTCOME_COMMITTED, history=[],
            ),
            repo / p.ROTATION_PATH,
        )
        # Comment fixture with URL inserted into content.
        canned_with_url = tmp_path / "with-url.json"
        canned_with_url.write_text(json.dumps({
            "action": "comment",
            "reason": "I should cite my source.",
            "target": {
                "project_id": "PROJ-001-mechanistic-interpretability-of-ctcf-bin",
                "artifact_kind": "spec",
                "artifact_path":
                    "projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/"
                    "specs/001-mechanistic-interpretability-of-ctcf-bin/spec.md",
            },
            "content": "Reference https://example.com/paper for the methodology.",
        }), encoding="utf-8")
        entry = p.tick(repo, llm_fixture=str(canned_with_url))
        assert entry["outcome"] == p.OUTCOME_LIBRARIAN_HELD
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        # Pointer HELD.
        assert state.last_used == "prior-slug"
