"""Personality-agent integration tests (T014, T018-T023, US1).

Drives the full per-tick orchestrator end-to-end against tmp-dir fixture
projects. The LLM is mocked via the ``LLMXIVE_PERSONALITY_FIXTURE`` env
var / ``llm_fixture`` kwarg so no real network is used.

Covers:
  - build_catalog (T014) — fixture projects → catalog shape + ordering
  - dispatch comment (T018) — review file lands with right frontmatter
  - dispatch contribute (T019) — feedback file lands with right metadata
  - dispatch propose_arxiv (T020) — submission stub lands
  - dispatch abstain (T021) — no files, abstain outcome
  - tick (T023) — pointer advances on committed/abstained; HOLDS on
    target_missing / malformed / model_error
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


def _make_repo(tmp_path: Path) -> Path:
    """Build a minimal repo skeleton: agents/prompts/personalities/,
    state/projects/, a fixture project with an idea + spec, and the
    umbrella prompt.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    # Personalities pool — just kahneman.
    (repo / "agents" / "prompts" / "personalities").mkdir(parents=True)
    shutil.copy(FIXTURES / "kahneman.md", repo / "agents" / "prompts" / "personalities" / "kahneman.md")
    # Umbrella prompt — minimal stub; the LLM is fixtured.
    (repo / "agents" / "prompts" / "personality.md").write_text(
        "# Personality umbrella\nReturn JSON.", encoding="utf-8")
    # Fixture project — same id as the canned action_comment fixture.
    pid = "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
    spec_dir = repo / "projects" / pid / "specs" / "001-mechanistic-interpretability-of-ctcf-bin"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "spec.md"
    spec_path.write_text(
        "# Spec — CTCF interpretability\n\nA placeholder.", encoding="utf-8")
    tasks_path = spec_dir / "tasks.md"
    tasks_path.write_text("# Tasks\n\n- [ ] T1\n", encoding="utf-8")
    # Project state YAML — required for build_catalog's project_store.list_all.
    state_dir = repo / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_dir.joinpath(f"{pid}.yaml").write_text(
        yaml.safe_dump({
            "artifact_hashes": {},
            "assigned_agent": None,
            "created_at": "2026-05-01T00:00:00+00:00",
            "current_stage": "in_progress",
            "failed_stage": None,
            "field": "biology",
            "human_escalation_reason": None,
            "id": pid,
            "last_run_id": None,
            "last_run_status": None,
            "points_paper": {},
            "points_research": {},
            "revision_round": 0,
            "speckit_paper_dir": None,
            "speckit_research_dir": f"specs/001-mechanistic-interpretability-of-ctcf-bin",
            "title": "CTCF Interpretability",
            "updated_at": "2026-05-13T00:00:00+00:00",
        }),
        encoding="utf-8",
    )
    return repo


# -- T014: build_catalog ---------------------------------------------------


class TestBuildCatalog:
    def test_catalog_includes_fixture_project(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        catalog = p.build_catalog(repo)
        assert len(catalog) == 1
        e = catalog[0]
        assert e.id == "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
        assert e.title == "CTCF Interpretability"
        assert e.field == "biology"
        assert e.current_stage == "in_progress"
        # Recent artifacts include the spec.md or tasks.md we created.
        kinds = {a["kind"] for a in e.recent_artifacts}
        assert "spec" in kinds or "tasks" in kinds

    def test_catalog_capped_at_limit(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        # Add 35 more projects.
        for i in range(35):
            pid = f"PROJ-{i:03d}-test-project"
            state_dir = repo / "state" / "projects"
            state_dir.joinpath(f"{pid}.yaml").write_text(
                yaml.safe_dump({
                    "artifact_hashes": {},
                    "assigned_agent": None,
                    "created_at": "2026-05-01T00:00:00+00:00",
                    "current_stage": "brainstormed",
                    "failed_stage": None,
                    "field": "general",
                    "human_escalation_reason": None,
                    "id": pid,
                    "last_run_id": None, "last_run_status": None,
                    "points_paper": {}, "points_research": {},
                    "revision_round": 0,
                    "speckit_paper_dir": None,
                    "speckit_research_dir": None,
                    "title": f"Test {i}",
                    "updated_at": f"2026-04-{(i % 28) + 1:02d}T00:00:00+00:00",
                }),
                encoding="utf-8",
            )
        catalog = p.build_catalog(repo)
        assert len(catalog) == p.DEFAULT_CATALOG_LIMIT

    def test_empty_project_list_returns_empty(self, tmp_path: Path) -> None:
        repo = tmp_path / "empty-repo"
        (repo / "state").mkdir(parents=True)
        catalog = p.build_catalog(repo)
        assert catalog == []


# -- T018: comment dispatch -------------------------------------------------


class TestDispatchComment:
    def test_review_file_lands_with_simulated_attribution(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        pool = p.load_pool(repo / p.POOL_PATH)
        persona = pool.personalities[0]
        # Comment fixture targets the spec.md we created in _make_repo.
        raw = (FIXTURES / "action_comment.json").read_text(encoding="utf-8")
        action = p.parse_action(raw)
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_COMMITTED
        assert len(result.committed_paths) == 1
        # The review file MUST be under reviews/research/ (the spec.md is
        # NOT under /paper/) with the (simulated) filename marker.
        rev_path = repo / result.committed_paths[0]
        assert rev_path.is_file()
        assert "-simulated__" in rev_path.name
        # Front-matter MUST tag this as an LLM review at qwen.qwen3.5-122b.
        text = rev_path.read_text(encoding="utf-8")
        assert "reviewer_kind: llm" in text
        assert "model_name: qwen.qwen3.5-122b" in text
        # Body contains the persona's content AND the disclaimer footer.
        assert "System 1" in text
        assert "simulated AI persona" in text


# -- T019: contribute dispatch ---------------------------------------------


class TestDispatchContribute:
    def test_feedback_file_lands_with_simulated_attribution(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        pool = p.load_pool(repo / p.POOL_PATH)
        persona = pool.personalities[0]
        raw = (FIXTURES / "action_contribute.json").read_text(encoding="utf-8")
        action = p.parse_action(raw)
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_COMMITTED
        path = repo / result.committed_paths[0]
        assert path.is_file()
        assert "-simulated__" in path.name
        text = path.read_text(encoding="utf-8")
        # Front-matter has the simulated submitter + the simulator markers.
        assert "submitter: Daniel Kahneman (simulated)" in text
        assert "personality_slug: kahneman" in text
        assert "model_kind: personality_simulator" in text
        # Body contains the persona's content AND the disclaimer footer.
        assert "Proposed edit" in text
        assert "simulated AI persona" in text


# -- T020: propose_arxiv dispatch ------------------------------------------


class TestDispatchProposeArxiv:
    def test_submission_stub_lands(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        pool = p.load_pool(repo / p.POOL_PATH)
        persona = pool.personalities[0]
        raw = (FIXTURES / "action_propose_arxiv.json").read_text(encoding="utf-8")
        action = p.parse_action(raw)
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_COMMITTED
        # File under state/personality-submissions/.
        path = repo / result.committed_paths[0]
        assert path.is_file()
        assert "personality-submissions" in str(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["submitter"] == "Daniel Kahneman (simulated)"
        assert data["arxiv_url"] == "https://arxiv.org/abs/2401.00001"
        assert "simulated AI persona" in data["disclaimer"]


# -- T021: abstain dispatch -------------------------------------------------


class TestDispatchAbstain:
    def test_abstain_writes_nothing(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        pool = p.load_pool(repo / p.POOL_PATH)
        persona = pool.personalities[0]
        raw = (FIXTURES / "action_abstain.json").read_text(encoding="utf-8")
        action = p.parse_action(raw)
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_ABSTAINED
        assert result.committed_paths == []


# -- T023: full tick pointer-advancement rule (FR-017) ---------------------


class TestTickPointerRule:
    def test_committed_advances_pointer(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        entry = p.tick(repo, llm_fixture=str(FIXTURES / "action_comment.json"))
        assert entry["outcome"] == p.OUTCOME_COMMITTED
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "kahneman"
        assert state.last_outcome == p.OUTCOME_COMMITTED

    def test_abstained_advances_pointer(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        entry = p.tick(repo, llm_fixture=str(FIXTURES / "action_abstain.json"))
        assert entry["outcome"] == p.OUTCOME_ABSTAINED
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "kahneman"

    def test_malformed_holds_pointer(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        # Pre-set the rotation pointer so we can detect "no advance."
        p.write_rotation_state(
            p.RotationState(
                last_used="some-prior-slug",
                last_used_at="2026-05-13T00:00:00+00:00",
                last_outcome=p.OUTCOME_COMMITTED,
                history=[],
            ),
            repo / p.ROTATION_PATH,
        )
        # Bad fixture (not valid JSON).
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        entry = p.tick(repo, llm_fixture=str(bad))
        assert entry["outcome"] == p.OUTCOME_MALFORMED
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        # Pointer HELD — same as before the tick.
        assert state.last_used == "some-prior-slug"
        assert state.last_outcome == p.OUTCOME_MALFORMED

    def test_target_missing_holds_pointer(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        # Synthesize an action with a target that doesn't exist on disk.
        bad_target = tmp_path / "bad-target.json"
        bad_target.write_text(json.dumps({
            "action": "comment",
            "reason": "...",
            "target": {
                "project_id": "PROJ-001-mechanistic-interpretability-of-ctcf-bin",
                "artifact_kind": "spec",
                "artifact_path": "projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/specs/missing/spec.md",
            },
            "content": "should not be written",
        }), encoding="utf-8")
        # Set a prior pointer to detect the hold.
        p.write_rotation_state(
            p.RotationState(
                last_used="prior-slug",
                last_used_at="2026-05-13T00:00:00+00:00",
                last_outcome=p.OUTCOME_COMMITTED,
                history=[],
            ),
            repo / p.ROTATION_PATH,
        )
        entry = p.tick(repo, llm_fixture=str(bad_target))
        assert entry["outcome"] == p.OUTCOME_TARGET_MISSING
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        # HELD.
        assert state.last_used == "prior-slug"

    def test_run_log_entry_has_all_required_fields(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        entry = p.tick(repo, llm_fixture=str(FIXTURES / "action_comment.json"))
        # Required attribution markers (data-model.md E6 + FR-010).
        assert entry["agent_name"] == "personality"
        assert entry["model_name"] == "qwen.qwen3.5-122b"
        assert entry["model_kind"] == "personality_simulator"
        assert entry["personality_slug"] == "kahneman"
        assert entry["display_name"] == "Daniel Kahneman (simulated)"
        assert entry["action"] == "comment"
        assert entry["outcome"] == "committed"
        assert len(entry["committed_paths"]) == 1
