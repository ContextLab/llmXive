"""Integration tests for TasksReviser + PaperTasksReviser (spec 015 T057).

Fake-backend tests covering the Mode-B revise flow:
- Single-artifact revision (tasks.md is the only writable artifact).
- Side filtering (research-side ignores paper-side keys + vice-versa).
- Context injection: spec + plan + analyze report + constitution + comments.
- Honest failure modes: missing `new_tasks_md`, non-JSON, no tasks.md
  artifact, padded missing concern responses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.revisers.tasks_reviser import (
    PaperTasksReviser,
    TasksReviser,
    _is_context_artifact,
    _is_tasks_artifact,
)
from llmxive.convergence.types import Concern, Severity

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    response_text: str
    last_messages: list = None  # type: ignore[assignment]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        # FR-011 self-consistency audit turns are content-distinct (their
        # system prompt opens with the audit banner). Return a clean 'ok'
        # audit reply for those WITHOUT recording them as last_messages, so
        # the revision call's messages stay observable for assertions.
        sys_text = getattr(messages[0], "content", "") if messages else ""
        if "auditing a revision you just produced" in sys_text:
            return _FakeResponse(text="ok: true\nproblems: []\n")
        self.last_messages = list(messages)
        return _FakeResponse(text=self.response_text)


# --- predicate tests ------------------------------------------------------


def test_is_tasks_artifact_filters_by_side():
    assert _is_tasks_artifact("specs/000-x/tasks.md", paper=False)
    assert not _is_tasks_artifact("specs/000-x/tasks.md", paper=True)
    assert _is_tasks_artifact("paper/specs/000-x/tasks.md", paper=True)
    assert not _is_tasks_artifact("paper/specs/000-x/tasks.md", paper=False)
    assert not _is_tasks_artifact("specs/000-x/spec.md", paper=False)


def test_is_context_artifact_filters_by_suffix_and_side():
    assert _is_context_artifact("specs/000-x/spec.md", "spec.md", paper=False)
    assert _is_context_artifact("specs/000-x/plan.md", "plan.md", paper=False)
    assert not _is_context_artifact("paper/specs/000-x/spec.md", "spec.md", paper=False)
    assert _is_context_artifact("paper/specs/000-x/spec.md", "spec.md", paper=True)


# --- research-side TasksReviser ------------------------------------------


def test_tasks_reviser_revises_and_records_responses(tmp_path: Path):
    tasks_key = "specs/000-x/tasks.md"
    artifacts = {
        tasks_key: "# tasks v1\n- T001 [FR-001]: write code.\n",
        "specs/000-x/spec.md": "# spec\n## FR\n- FR-001: X\n- FR-002: Y (untestable)\n",
        "specs/000-x/plan.md": "# plan\n- phase 1: X\n- phase 2: Y\n",
        "__analyze_report__": "coverage: FR-002 has no task.",
        "__constitution__": "Principle V: real-call testing.",
        "__comments_block__": "reviewer: FR-002 needs a task too.",
    }
    concerns = [
        Concern(
            id="C1", reviewer="coverage", severity=Severity.REQUIREMENT,
            artifact=tasks_key, location="FR-002",
            text="FR-002 has no corresponding T### task.",
        ),
    ]
    new_tasks = (
        "# tasks v2\n"
        "- T001 [FR-001]: write code (verified by tests/unit/test_x.py).\n"
        "- T002 [FR-002]: implement Y check (verified by tests/integration/test_y.py).\n"
    )
    fake_reply = {
        "new_tasks_md": new_tasks,
        "responses": [
            {"concern_id": "C1", "response": "Added T002 for FR-002",
             "what_changed": "new task T002 tied to FR-002",
             "artifacts_changed": [tasks_key]},
        ],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = TasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, responses = reviser.revise(artifacts, concerns)

    assert updated[tasks_key] == new_tasks
    assert "T002" in updated[tasks_key]  # new task present
    assert {r.concern_id for r in responses} == {"C1"}

    user_msg = backend.last_messages[1].content
    assert "FR-001" in user_msg  # spec injected
    assert "phase 1" in user_msg  # plan injected
    assert "Principle V" in user_msg  # constitution injected
    assert "coverage: FR-002 has no task" in user_msg  # analyze report
    assert "reviewer: FR-002 needs" in user_msg  # comments
    assert "[concern C1]" in user_msg


def test_tasks_reviser_rejects_missing_new_tasks_md(tmp_path: Path):
    tasks_key = "specs/000-x/tasks.md"
    backend = _FakeBackend(response_text='{"responses": []}')
    reviser = TasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="no usable 'new_tasks_md'"):
        reviser.revise({tasks_key: "# tasks"}, [])


def test_tasks_reviser_rejects_non_json(tmp_path: Path):
    tasks_key = "specs/000-x/tasks.md"
    backend = _FakeBackend(response_text="not json")
    reviser = TasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(RuntimeError, match="parseable JSON"):
        reviser.revise({tasks_key: "# tasks"}, [])


def test_tasks_reviser_raises_when_no_tasks_artifact(tmp_path: Path):
    backend = _FakeBackend(
        response_text=json.dumps({"new_tasks_md": "x", "responses": []})
    )
    reviser = TasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    with pytest.raises(ValueError, match=r"no research-side 'tasks\.md'"):
        reviser.revise({"specs/000-x/spec.md": "# spec"}, [])


def test_tasks_reviser_pads_missing_responses(tmp_path: Path):
    tasks_key = "specs/000-x/tasks.md"
    backend = _FakeBackend(
        response_text=json.dumps(
            {
                "new_tasks_md": "# revised tasks",
                "responses": [{"concern_id": "C1", "response": "done", "what_changed": "x"}],
            }
        )
    )
    reviser = TasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    concerns = [
        Concern(id="C1", reviewer="coverage", severity=Severity.REQUIREMENT,
                artifact=tasks_key, location="", text="x"),
        Concern(id="C2", reviewer="ordering", severity=Severity.WRITING,
                artifact=tasks_key, location="", text="y"),
    ]
    _, responses = reviser.revise({tasks_key: "# tasks"}, concerns)
    by_id = {r.concern_id: r for r in responses}
    assert by_id["C2"].response == "<missing>"


# --- paper-side PaperTasksReviser ----------------------------------------


def test_paper_tasks_reviser_isolates_paper_side(tmp_path: Path):
    paper_tasks_key = "paper/specs/000-x/tasks.md"
    artifacts = {
        paper_tasks_key: "# paper tasks v1",
        "paper/specs/000-x/spec.md": "# paper spec",
        "paper/specs/000-x/plan.md": "# paper plan",
        # research-side artifacts that must NOT be confused for paper-side
        "specs/000-x/tasks.md": "# research tasks (different)",
        "specs/000-x/spec.md": "# research spec",
    }
    fake_reply = {
        "new_tasks_md": "# paper tasks v2",
        "responses": [],
    }
    backend = _FakeBackend(response_text=json.dumps(fake_reply))
    reviser = PaperTasksReviser(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "summarize_cache",
    )
    updated, _ = reviser.revise(artifacts, [])

    assert updated[paper_tasks_key] == "# paper tasks v2"
    # research-side tasks.md must NOT have been touched.
    assert updated["specs/000-x/tasks.md"] == "# research tasks (different)"

    user_msg = backend.last_messages[1].content
    # Source spec for the paper reviser is the paper-side spec.md.
    assert "# paper spec" in user_msg
    assert "# research spec" not in user_msg


def test_tasks_reviser_names():
    assert TasksReviser.name == "tasker"
    assert PaperTasksReviser.name == "paper_tasker"
