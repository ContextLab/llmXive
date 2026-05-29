"""Single-step convergence on a REAL project directory (spec 015 T021).

Exercises the new ``run_engine_for_project`` bridge between the engine
and an on-disk project tree (see ``src/llmxive/convergence/project_runner.py``).
The test materializes a real ``projects/<id>/specs/<f>/{tasks,spec,plan}.md``
tree under ``tmp_path``, runs the engine, and verifies the engine's
revised tasks.md actually lands back on disk (closes the in-memory-only
gap that ``test_panels_research.py`` doesn't cover).

This is the proving ground for T021's "engine drives a real project"
contract before T027 wires the runner into the production graph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from llmxive.convergence.project_runner import run_engine_for_project
from llmxive.convergence.reviewspecs import build_tasks_reviewspec
from llmxive.convergence.types import Concern, Severity, Verdict


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    responses: list[str]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        if not self.responses:
            raise RuntimeError("ran out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


class _CoverageReviewer:
    """Single-lens reviewer scripted to accept on round 1."""

    name = "coverage"

    def __init__(self) -> None:
        self._rereview_round = 0

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return [
            Concern(
                id="C1", reviewer=self.name, severity=Severity.REQUIREMENT,
                artifact="tasks.md", location="FR-002",
                text="FR-002 has no corresponding task",
            )
        ]

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self._rereview_round += 1
        status = "pass" if self._rereview_round >= 1 else "fail"
        return [
            Verdict(concern_id=c.id, reviewer=self.name, status=status)
            for c in own_concerns
        ]


def _make_real_project_tree(repo: Path, project_id: str) -> dict[str, Path]:
    project_dir = repo / "projects" / project_id
    spec_dir = project_dir / "specs" / "000-x"
    spec_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "tasks_md": spec_dir / "tasks.md",
        "spec_md": spec_dir / "spec.md",
        "plan_md": spec_dir / "plan.md",
    }
    paths["tasks_md"].write_text("# tasks v1\n- T001 [FR-001]: do X\n")
    paths["spec_md"].write_text("# spec\n## FR\n- FR-001: do X\n- FR-002: do Y\n")
    paths["plan_md"].write_text("# plan\n## Phase 1\nimplement X and Y\n")
    return paths


def test_run_engine_for_project_rewrites_tasks_md_on_disk(tmp_path: Path):
    """End-to-end on a real project tree: engine converges + the runner
    writes the revised tasks.md back to disk."""
    project_id = "PROJ-001-test"
    paths = _make_real_project_tree(tmp_path, project_id)

    tasks_key = f"projects/{project_id}/specs/000-x/tasks.md"
    spec_key = f"projects/{project_id}/specs/000-x/spec.md"
    plan_key = f"projects/{project_id}/specs/000-x/plan.md"
    artifact_paths = {
        tasks_key: paths["tasks_md"],
        spec_key: paths["spec_md"],
        plan_key: paths["plan_md"],
    }

    new_tasks_md = "# tasks v2\n- T001 [FR-001]: do X\n- T002 [FR-002]: do Y\n"
    fake_reply = json.dumps({
        "new_tasks_md": new_tasks_md,
        "responses": [
            {"concern_id": "C1", "response": "Added T002",
             "what_changed": "T002 added",
             "artifacts_changed": [tasks_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    repo_root = Path(__file__).resolve().parents[2]
    spec = build_tasks_reviewspec(
        backend=backend, repo_root=repo_root, project_id=project_id,
    )
    spec.reviewers = [_CoverageReviewer()]

    result = run_engine_for_project(
        spec=spec,
        artifact_paths=artifact_paths,
        extra_inputs={"__constitution__": "Principle V: real-call testing."},
        repo_root=repo_root,
        # Partial fixture: this test only exercises the project_runner
        # bridge mechanics (load → engine → write-back), not the
        # tasked-stage's full reviser contract. Opt out of the FR-049
        # fail-loud sentinel-key check.
        require_full_extra_inputs=False,
    )

    # Engine converged successfully.
    assert result.convergence.converged is True
    assert result.convergence.rounds_used == 1
    assert result.convergence.next_stage == "analyzed"

    # The runner wrote tasks.md back to disk; spec + plan unchanged.
    assert paths["tasks_md"] in result.files_written
    assert paths["spec_md"] in result.files_unchanged
    assert paths["plan_md"] in result.files_unchanged

    # On-disk verification: rewritten tasks.md has the new content.
    persisted = paths["tasks_md"].read_text()
    assert "T002" in persisted
    assert "FR-002" in persisted
    assert persisted == new_tasks_md


def test_run_engine_for_project_kickback_writes_nothing(tmp_path: Path):
    """When the panel never accepts, the engine emits a kickback and
    the runner MUST NOT write anything back to disk (the partial
    revisions are discarded — a kickback means "don't apply")."""
    from llmxive.types import Stage

    project_id = "PROJ-002-test"
    paths = _make_real_project_tree(tmp_path, project_id)
    tasks_key = f"projects/{project_id}/specs/000-x/tasks.md"
    artifact_paths = {tasks_key: paths["tasks_md"]}
    original_tasks_content = paths["tasks_md"].read_text()

    class _AlwaysFail:
        name = "coverage"

        def identify(self, artifacts, *, constitution, advisory):
            return [Concern(
                id="C1", reviewer=self.name, severity=Severity.METHODOLOGY,
                artifact=tasks_key, location="", text="plan-root cause",
            )]

        def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
            return [Verdict(concern_id=c.id, reviewer=self.name, status="fail")
                    for c in own_concerns]

    # The reviser is called multiple rounds (3); supply enough responses.
    fake_reply = json.dumps({
        "new_tasks_md": "# attempted revision\n- T001\n- T002\n",
        "responses": [{"concern_id": "C1", "response": "x", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[fake_reply] * 5)
    repo_root = Path(__file__).resolve().parents[2]
    spec = build_tasks_reviewspec(
        backend=backend, repo_root=repo_root, project_id=project_id,
    )
    spec.reviewers = [_AlwaysFail()]

    result = run_engine_for_project(
        spec=spec,
        artifact_paths=artifact_paths,
        repo_root=repo_root,
        write_back=False,  # kickback: read-only run
        require_full_extra_inputs=False,  # partial fixture (see test above)
    )

    assert result.convergence.converged is False
    assert result.convergence.kickback is not None
    # Kickback target is a real Stage enum value (no typos).
    assert result.convergence.kickback.to_stage in {s.value for s in Stage}
    assert result.convergence.kickback.to_stage == "planned"  # METHODOLOGY → planned
    # write_back=False → tasks.md unchanged on disk.
    assert paths["tasks_md"].read_text() == original_tasks_content
    assert result.files_written == []


def test_run_engine_for_project_dry_run_with_write_back_false(tmp_path: Path):
    """A successful run with ``write_back=False`` reports what WOULD be
    written but leaves disk untouched. Useful for dry-runs that preview
    the engine's decision before applying it."""
    project_id = "PROJ-003-test"
    paths = _make_real_project_tree(tmp_path, project_id)
    tasks_key = f"projects/{project_id}/specs/000-x/tasks.md"
    original = paths["tasks_md"].read_text()

    fake_reply = json.dumps({
        "new_tasks_md": "# tasks REVISED (dry run)\n",
        "responses": [{"concern_id": "C1", "response": "x", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[fake_reply])
    repo_root = Path(__file__).resolve().parents[2]
    spec = build_tasks_reviewspec(
        backend=backend, repo_root=repo_root, project_id=project_id,
    )
    spec.reviewers = [_CoverageReviewer()]

    result = run_engine_for_project(
        spec=spec,
        artifact_paths={tasks_key: paths["tasks_md"]},
        repo_root=repo_root,
        write_back=False,
        require_full_extra_inputs=False,  # partial fixture (see test above)
    )

    # Engine converged + the file IS marked unchanged on disk.
    assert result.convergence.converged is True
    assert paths["tasks_md"].read_text() == original  # untouched
