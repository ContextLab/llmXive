"""Tests for the tasker → convergence-engine bridge (spec 015 T027).

Verifies the migration path that lets TaskerAgent opt into the spec-015
convergence engine via ``LLMXIVE_TASKER_USE_ENGINE=1``. The bridge:

1. ``tasker_engine_enabled()`` honors the env var.
2. ``analyze_findings_to_concerns(...)`` translates legacy analyze-report
   findings into spec-015 Concerns with correct severity mapping.
3. ``run_tasker_via_engine(...)`` exercises the engine end-to-end on a
   real on-disk project tree and writes the rewritten tasks.md back.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from llmxive.convergence.types import Severity
from llmxive.speckit._tasker_engine_bridge import (
    analyze_findings_to_concerns,
    run_tasker_via_engine,
    tasker_engine_enabled,
)


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


# --- env-var flag ---------------------------------------------------------


def test_tasker_engine_enabled_default_false(monkeypatch):
    monkeypatch.delenv("LLMXIVE_TASKER_USE_ENGINE", raising=False)
    assert tasker_engine_enabled() is False


def test_tasker_engine_enabled_when_set(monkeypatch):
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "1")
    assert tasker_engine_enabled() is True
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "true")
    assert tasker_engine_enabled() is True


def test_tasker_engine_disabled_when_false_value(monkeypatch):
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "0")
    assert tasker_engine_enabled() is False
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "")
    assert tasker_engine_enabled() is False


# --- findings → concerns translation -------------------------------------


def test_analyze_findings_to_concerns_maps_class_to_severity():
    findings = [
        {"id": "F001", "class": "coverage", "text": "FR-002 lacks a task",
         "artifact": "tasks.md", "location": "FR-002"},
        {"id": "F002", "class": "methodology", "text": "approach won't answer RQ",
         "artifact": "tasks.md", "location": "T003"},
        {"id": "F003", "class": "fatal", "text": "central thesis unsalvageable",
         "artifact": "tasks.md", "location": "T005"},
    ]
    concerns = analyze_findings_to_concerns(findings, default_artifact_path="tasks.md")
    assert len(concerns) == 3
    assert concerns[0].severity == Severity.REQUIREMENT  # coverage → REQUIREMENT
    assert concerns[1].severity == Severity.METHODOLOGY
    assert concerns[2].severity == Severity.FATAL
    # Ids preserved.
    assert [c.id for c in concerns] == ["F001", "F002", "F003"]


def test_analyze_findings_unknown_class_falls_back_to_writing():
    findings = [
        {"id": "F001", "class": "totally_unknown_lens",
         "text": "?", "artifact": "tasks.md", "location": ""},
    ]
    concerns = analyze_findings_to_concerns(findings, default_artifact_path="tasks.md")
    assert concerns[0].severity == Severity.WRITING


def test_analyze_findings_synthesize_id_when_missing():
    findings = [
        {"class": "coverage", "text": "no id provided", "artifact": "tasks.md",
         "location": ""},
    ]
    concerns = analyze_findings_to_concerns(findings, default_artifact_path="tasks.md")
    assert concerns[0].id == "F001"  # synthetic ID


# --- end-to-end run_tasker_via_engine ------------------------------------


def test_run_tasker_via_engine_rewrites_tasks_md(tmp_path: Path):
    """End-to-end on a real project tree: legacy analyze findings →
    engine → rewritten tasks.md persisted to disk."""
    project_id = "PROJ-001-test"
    spec_dir = tmp_path / "projects" / project_id / "specs" / "000-x"
    spec_dir.mkdir(parents=True)
    tasks_path = spec_dir / "tasks.md"
    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"

    tasks_path.write_text("# tasks v1\n- T001 [FR-001]: do X\n")
    spec_path.write_text("# spec\n## FR\n- FR-001: do X\n- FR-002: do Y\n")
    plan_path.write_text("# plan\nphase 1: X and Y\n")

    findings = [
        {"id": "F001", "class": "coverage",
         "text": "FR-002 has no corresponding task",
         "artifact": "tasks.md", "location": "FR-002"},
    ]

    new_tasks_md = (
        "# tasks v2\n- T001 [FR-001]: do X\n- T002 [FR-002]: do Y\n"
    )
    fake_reply = json.dumps({
        "new_tasks_md": new_tasks_md,
        "responses": [
            {"concern_id": "F001", "response": "added T002",
             "what_changed": "tasks.md now has T002 satisfying FR-002",
             "artifacts_changed": [f"projects/{project_id}/specs/000-x/tasks.md"]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    repo_root = Path(__file__).resolve().parents[2]

    result = run_tasker_via_engine(
        project_id=project_id,
        repo_root=repo_root,
        tasks_path=tasks_path,
        spec_path=spec_path,
        plan_path=plan_path,
        analyze_findings=findings,
        backend=backend,
        constitution_text="Principle V: real-call testing.",
        analyze_report_text="coverage: FR-002 has no task",
    )

    # Engine converged + wrote tasks.md back to disk.
    assert result.convergence.converged is True
    assert tasks_path in result.files_written
    assert spec_path in result.files_unchanged
    assert plan_path in result.files_unchanged
    persisted = tasks_path.read_text()
    assert "T002" in persisted
    assert "FR-002" in persisted
