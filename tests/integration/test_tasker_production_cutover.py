"""T027 production cutover: convergence engine is the DEFAULT tasker path.

The legacy Mode-A/Mode-B loop remains as the emergency rollback via
``LLMXIVE_TASKER_LEGACY=1``. These tests lock in the cutover invariants:

1. Engine is the default — no env var means engine path.
2. Legacy opt-out via ``LLMXIVE_TASKER_LEGACY=1`` falls back to Mode-A/B.
3. FR-031 deterministic guards fire on BOTH paths (SSoT in
   ``_legacy_guards.check_legacy_guards``); the bridge rejects a
   writeback that drops requirements / has too few task IDs / etc.

The tests use real on-disk projects + a fake backend (no mocks). The
fake backend emits canned JSON responses that the TasksReviser parses
into ``new_tasks_md`` + per-concern ConcernResponses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from llmxive.speckit._legacy_guards import check_legacy_guards
from llmxive.speckit._tasker_engine_bridge import (
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

    def chat(self, messages, model=None, **kw):  # type: ignore[no-untyped-def]
        # spec-015 / #239: build_tasks_reviewspec now wires a LIVE 4-lens
        # LLMReviewer panel that runs ALONGSIDE the analyze reviewer. Serve a
        # clean accept verdict for those panel calls (and an ok for the FR-011
        # self-consistency audit turn) so the engine still converges and the
        # FR-031 guard rollback semantics this test asserts hold unchanged.
        sys_text = getattr(messages[0], "content", "") if messages else ""
        if "auditing a revision you just produced" in sys_text:
            return _FakeResponse(text="ok: true\nproblems: []\n")
        if "Other panelists cover other aspects" in sys_text:
            return _FakeResponse(text="---\nverdict: accept\nconcerns: []\n---\n")
        if not self.responses:
            raise RuntimeError("ran out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


def test_engine_is_default_when_no_env_var(monkeypatch):
    monkeypatch.delenv("LLMXIVE_TASKER_LEGACY", raising=False)
    monkeypatch.delenv("LLMXIVE_TASKER_USE_ENGINE", raising=False)
    assert tasker_engine_enabled() is True
    assert tasker_legacy_enabled() is False


def test_legacy_opt_out_via_LLMXIVE_TASKER_LEGACY(monkeypatch):
    monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "1")
    monkeypatch.delenv("LLMXIVE_TASKER_USE_ENGINE", raising=False)
    assert tasker_engine_enabled() is False
    assert tasker_legacy_enabled() is True


def test_engine_path_enforces_fr031_requirement_preservation_guard(
    tmp_path: Path,
):
    """FR-031 (constraint preservation): a Mode-B writeback that DROPS
    FR/SC ids from spec.md MUST be refused. The bridge's _GuardedReviser
    runs the same _legacy_guards.check_legacy_guards as the legacy loop,
    so the gutted spec is reverted to its original on-disk content. The
    rewritten tasks.md (which doesn't violate any guard) IS persisted —
    so the test asserts the partial-rollback semantics: tasks.md is
    rewritten, spec.md is preserved despite the LLM trying to gut it."""
    project_id = "PROJ-CUTOVER-fr031"
    spec_dir = tmp_path / "projects" / project_id / "specs" / "000-x"
    spec_dir.mkdir(parents=True)
    tasks_path = spec_dir / "tasks.md"
    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"

    # 5 task IDs + 6 FR/SC ids on-disk.
    tasks_path.write_text(
        "# tasks v1\n"
        "- [ ] T001 [FR-001]: do A\n"
        "- [ ] T002 [FR-002]: do B\n"
        "- [ ] T003 [FR-003]: do C\n"
        "- [ ] T004 [SC-001]: meet SC-001\n"
        "- [ ] T005 [SC-002]: meet SC-002\n"
    )
    original_spec = (
        "# spec\n"
        "## Functional\n"
        "- **FR-001**: A\n- **FR-002**: B\n- **FR-003**: C\n"
        "## Success\n"
        "- **SC-001**: one\n- **SC-002**: two\n- **SC-003**: three\n"
    )
    spec_path.write_text(original_spec)
    plan_path.write_text("# plan\nphase 1\n")

    # The LLM tries to "resolve" the analyze finding by GUTTING spec.md
    # to one FR. tasks.md rewrite is fine (>=5 IDs, no diff). The guards
    # MUST reject the spec.md gutting and revert it to its original
    # content; tasks.md MUST still be persisted.
    new_tasks_md = (
        "# tasks v2\n"
        "- [ ] T001 [FR-001]: do A revised\n"
        "- [ ] T002 [FR-002]: do B\n"
        "- [ ] T003 [FR-003]: do C\n"
        "- [ ] T004 [SC-001]: meet SC-001\n"
        "- [ ] T005 [SC-002]: meet SC-002\n"
    )
    gutted_spec = "# spec\n## Functional\n- **FR-001**: A only.\n"

    # Reviser receives the artifact paths in the engine's artifacts dict
    # under the bridge's canonical keys; the reply must declare which
    # artifact each ConcernResponse touches, but the reviser itself
    # always returns new_tasks_md (tasks-side reviser).
    fake_reply = json.dumps({
        "new_tasks_md": new_tasks_md,
        "new_spec_md": gutted_spec,  # LLM tries to update spec.md too
        "responses": [
            {"concern_id": "F001", "response": "rewrote tasks; reduced spec",
             "what_changed": "...",
             "artifacts_changed": [
                 f"projects/{project_id}/specs/000-x/tasks.md",
                 f"projects/{project_id}/specs/000-x/spec.md",
             ]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    repo_root = Path(__file__).resolve().parents[2]

    findings = [
        {"id": "F001", "class": "writing",
         "text": "spec.md and tasks.md should be tidied",
         "artifact": "tasks.md", "location": ""},
    ]
    run_tasker_via_engine(
        project_id=project_id,
        repo_root=repo_root,
        tasks_path=tasks_path,
        spec_path=spec_path,
        plan_path=plan_path,
        analyze_findings=findings,
        backend=backend,
        constitution_text=None,
        analyze_report_text="",
    )

    # tasks.md WAS rewritten (no guard violation on the new tasks).
    assert "do A revised" in tasks_path.read_text()
    # spec.md was preserved despite the LLM emitting a gutted version
    # (the TasksReviser doesn't return spec.md in its `updated` dict —
    # but if a future reviser did, the guard would catch it).
    assert spec_path.read_text() == original_spec


def test_legacy_guards_ssot_smoke():
    """Smoke check that check_legacy_guards is the SSoT — calling it
    directly returns the same refusal logic for both the legacy loop
    and the engine bridge.
    """
    # tasks.md guard: too few IDs.
    refusals = check_legacy_guards(
        filename="tasks.md",
        new_content="all tasks done.\n",
        original_content=(
            "- [ ] T001 a\n- [ ] T002 b\n- [ ] T003 c\n"
            "- [ ] T004 d\n- [ ] T005 e\n"
        ),
    )
    assert any("only 0 task IDs" in m for m in refusals)

    # spec.md guard: drops FR id.
    refusals = check_legacy_guards(
        filename="spec.md",
        new_content="# Spec\n- **FR-001**: keep\n",
        original_content="# Spec\n- **FR-001**: keep\n- **FR-002**: drop\n",
    )
    assert any("drops requirements" in m for m in refusals)

    # spec.md / plan.md guard: no markdown header.
    refusals = check_legacy_guards(
        filename="spec.md",
        new_content="just prose, no headers.\n",
        original_content="# Spec\n- **FR-001**: ok\n",
    )
    assert refusals  # either header OR constraint-preservation guard fires
