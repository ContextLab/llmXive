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
from pathlib import Path

import yaml

from llmxive.agents import personality as p
from llmxive.agents import personality_turn as pt
from tests.personality_fixture import make_repo

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


_make_repo = make_repo


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
        # This exercises the canonical review WRITER, not the reply parser. A
        # turn no longer declares its own target -- it is given one -- so the
        # Action is built the way tick() now builds it.
        reply = json.loads((FIXTURES / "action_comment.json").read_text(encoding="utf-8"))
        target = pt.select_target(repo)
        assert target is not None, "the fixture project must be substantive"
        action = p.Action(
            action=p.ACTION_COMMENT,
            target_project_id=target.project_id,
            target_artifact_path=target.artifact_rel,
            target_artifact_kind=target.kind,
            content=reply["comment"],
            reason="grounded comment on a read artifact",
        )
        result = p.dispatch(action, persona, repo)
        assert result.outcome == p.OUTCOME_COMMITTED
        assert len(result.committed_paths) == 1
        # The review file MUST be under reviews/research/ (the spec.md is
        # NOT under /paper/) with the (simulated) filename marker.
        rev_path = repo / result.committed_paths[0]
        assert rev_path.is_file()
        assert "-simulated__" in rev_path.name
        # Front-matter MUST tag this as an LLM review at openai.gpt-oss-120b.
        text = rev_path.read_text(encoding="utf-8")
        assert "reviewer_kind: llm" in text
        assert "model_name: openai.gpt-oss-120b" in text
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

    def test_no_substantive_artifact_abstains_without_a_model_call(self, tmp_path: Path) -> None:
        """A turn is GIVEN a target, so it can no longer name a missing one.

        The old lane let the model declare `target.artifact_path`, and a bad
        one produced OUTCOME_TARGET_MISSING with the pointer HELD. A turn now
        selects the artifact itself, so the equivalent case is "no active
        authored project has anything substantive to read" -- decided before
        any model call. The pointer ADVANCES: nothing is this persona's fault
        and there is nothing for it to do differently, so holding would stall
        the whole rotation while no project has a substantive artifact.
        """
        repo = _make_repo(tmp_path)
        # Reduce the only project's spec to a stub: nothing substantive remains.
        spec = next((repo / "projects").glob("*/specs/*/spec.md"))
        spec.write_text("# Spec\n\nTODO.\n", encoding="utf-8")
        next((repo / "projects").glob("*/specs/*/tasks.md")).write_text(
            "# Tasks\n\n- [ ] T1\n", encoding="utf-8")
        p.write_rotation_state(
            p.RotationState(last_used="some-prior-slug",
                            last_used_at="2026-05-13T00:00:00+00:00",
                            last_outcome=p.OUTCOME_COMMITTED, history=[]),
            repo / p.ROTATION_PATH,
        )

        def _forbidden(*_a, **_k):
            raise AssertionError("no model call may be made without a target")

        import llmxive.agents.personality as module
        original = module._grounded_call
        module._grounded_call = _forbidden
        try:
            entry = p.tick(repo)
        finally:
            module._grounded_call = original
        assert entry["outcome"] == p.OUTCOME_ABSTAINED
        assert "substantive" in entry["note"]
        state = p.load_rotation_state(repo / p.ROTATION_PATH)
        assert state.last_used == "kahneman", "the rotation advances past a dead turn"

    def test_run_log_entry_has_all_required_fields(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        entry = p.tick(repo, llm_fixture=str(FIXTURES / "action_comment.json"))
        # Required attribution markers (data-model.md E6 + FR-010).
        assert entry["agent_name"] == "personality"
        # The audit's provenance finding: MODEL_NAME is a module constant that
        # the run log recorded for EVERY tick regardless of what answered. The
        # entry now carries the model that actually produced the reply -- here
        # the fixture that stood in for one.
        assert entry["model_name"] == "fixture"
        assert entry["model_kind"] == "personality_simulator"
        assert entry["personality_slug"] == "kahneman"
        assert entry["display_name"] == "Daniel Kahneman (simulated)"
        assert entry["action"] == "comment"
        assert entry["outcome"] == "committed"
        assert len(entry["committed_paths"]) == 1
