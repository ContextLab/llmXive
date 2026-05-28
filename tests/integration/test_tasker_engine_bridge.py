"""Tests for the tasker → convergence-engine bridge (spec 015 T027).

Post-T027 production cutover: the engine is the DEFAULT path; the
``LLMXIVE_TASKER_LEGACY=1`` env var is the emergency rollback. These
tests cover:

1. ``tasker_engine_enabled()`` honors the env var (default True post-T027).
2. ``analyze_findings_to_concerns(...)`` translates legacy analyze-report
   findings into spec-015 Concerns with correct severity mapping.
3. ``run_tasker_via_engine(...)`` exercises the engine end-to-end on a
   real on-disk project tree and writes the rewritten tasks.md back,
   gated by the FR-031 deterministic guards (``_legacy_guards``).
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
    tasker_legacy_enabled,
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


def test_tasker_engine_enabled_default_true_post_T027(monkeypatch):
    """Post-T027: engine is the DEFAULT. Unset env vars → True."""
    monkeypatch.delenv("LLMXIVE_TASKER_USE_ENGINE", raising=False)
    monkeypatch.delenv("LLMXIVE_TASKER_LEGACY", raising=False)
    assert tasker_engine_enabled() is True
    assert tasker_legacy_enabled() is False


def test_tasker_legacy_enabled_when_set(monkeypatch):
    monkeypatch.delenv("LLMXIVE_TASKER_USE_ENGINE", raising=False)
    monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "1")
    assert tasker_legacy_enabled() is True
    assert tasker_engine_enabled() is False
    monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "true")
    assert tasker_engine_enabled() is False


def test_tasker_engine_disabled_when_back_compat_var_false(monkeypatch):
    """Back-compat: the historic ``LLMXIVE_TASKER_USE_ENGINE=0`` still
    forces the legacy path (operators with existing scripts get the
    expected opt-out behavior)."""
    monkeypatch.delenv("LLMXIVE_TASKER_LEGACY", raising=False)
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "0")
    assert tasker_engine_enabled() is False
    monkeypatch.setenv("LLMXIVE_TASKER_USE_ENGINE", "")
    # Empty explicit value is treated as falsy (back-compat with the
    # pre-T027 semantics of the opt-in flag).
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

    # Post-T027: the bridge runs FR-031 deterministic guards on every
    # writeback. tasks.md must have >=5 ``- [ ] T###`` checkbox lines
    # (the format the production tasker emits), and spec.md must
    # preserve every FR-/SC- id from the on-disk content.
    tasks_path.write_text(
        "# tasks v1\n"
        "- [ ] T001 [FR-001]: do X\n"
        "- [ ] T002 [FR-002]: do Y\n"
        "- [ ] T003 [FR-003]: do Z\n"
        "- [ ] T004 [FR-004]: do W\n"
        "- [ ] T005 [FR-005]: do V\n"
    )
    spec_path.write_text(
        "# spec\n"
        "## FR\n"
        "- FR-001: do X\n- FR-002: do Y\n- FR-003: do Z\n"
        "- FR-004: do W\n- FR-005: do V\n- FR-006: do U\n"
    )
    plan_path.write_text("# plan\nphase 1: X..V; phase 2: U\n")

    findings = [
        {"id": "F001", "class": "coverage",
         "text": "FR-006 has no corresponding task",
         "artifact": "tasks.md", "location": "FR-006"},
    ]

    new_tasks_md = (
        "# tasks v2\n"
        "- [ ] T001 [FR-001]: do X\n"
        "- [ ] T002 [FR-002]: do Y\n"
        "- [ ] T003 [FR-003]: do Z\n"
        "- [ ] T004 [FR-004]: do W\n"
        "- [ ] T005 [FR-005]: do V\n"
        "- [ ] T006 [FR-006]: do U\n"
    )
    fake_reply = json.dumps({
        "new_tasks_md": new_tasks_md,
        "responses": [
            {"concern_id": "F001", "response": "added T006",
             "what_changed": "tasks.md now has T006 satisfying FR-006",
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
        analyze_report_text="coverage: FR-006 has no task",
    )

    # Engine converged + wrote tasks.md back to disk (the FR-031 guard
    # accepts a writeback that has >=5 task IDs AND preserves all
    # FR/SC ids — both invariants hold for the new content).
    assert result.convergence.converged is True
    assert tasks_path in result.files_written
    assert spec_path in result.files_unchanged
    assert plan_path in result.files_unchanged
    persisted = tasks_path.read_text()
    assert "T006" in persisted
    assert "FR-006" in persisted
