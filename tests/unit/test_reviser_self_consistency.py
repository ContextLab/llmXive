"""Unit tests for FR-011's reviser self-consistency second pass (spec 015, #239).

FR-011 requires every reviser to run a self-consistency pass after addressing
R1 concerns. The implementation lives in
``src/llmxive/convergence/revisers/_self_consistency.py`` and is wired into
every reviser's ``revise()``. These tests exercise:

* the helper (:func:`self_consistency_pass`, :func:`run_with_self_consistency`)
  in isolation, with an in-memory multi-response fake backend, and
* the end-to-end wiring on :class:`SpecReviser`.

No mocks — a real in-memory ``_QueueBackend`` (mirroring the existing
``_FakeBackend`` pattern in ``tests/integration/test_spec_reviser.py``) queues
a FIXED list of replies and serves them in order, raising when exhausted (which
is exactly how the ~50 existing single-reply reviser tests reach the
self-consistency fallback path).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.convergence.revisers._self_consistency import (
    SelfConsistencyResult,
    run_with_self_consistency,
    self_consistency_pass,
)
from llmxive.convergence.revisers.spec_reviser import SpecReviser, _scan_markers
from llmxive.convergence.types import Concern, ConcernResponse, Severity

# Real repo root so ``render_prompt`` / ``load_prompt`` resolve the prompt
# files (clarifier.md + the self-consistency block). The summarize cache uses
# tmp_path so tests leave no on-disk side effects.
_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- in-memory fake backend (no mocks) ------------------------------------


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _QueueBackend:
    """Serves queued replies in order; raises when exhausted.

    Records each call's messages so tests can assert on prompt content. An
    exhausted queue mirrors production's "the check's backend call failed"
    path — the self-consistency helper must catch that and fall back.
    """

    replies: list[str]
    calls: list[list] = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        self.calls.append(list(messages))
        if not self.replies:
            raise RuntimeError("_QueueBackend: ran out of canned responses")
        return _FakeResponse(text=self.replies.pop(0))


# --- fixtures --------------------------------------------------------------


def _concerns() -> list[Concern]:
    return [
        Concern(
            id="C1",
            reviewer="requirements_coverage",
            severity=Severity.REQUIREMENT,
            artifact="specs/000-x/spec.md",
            location="FR-002",
            text="FR-002 must name a concrete threshold.",
        ),
        Concern(
            id="C2",
            reviewer="testability",
            severity=Severity.WRITING,
            artifact="specs/000-x/spec.md",
            location="SC-001",
            text="SC-001 must tie '< 5 minutes' to a measurement procedure.",
        ),
    ]


def _responses() -> list[ConcernResponse]:
    return [
        ConcernResponse(
            concern_id="C1", response="named threshold 0.5", what_changed="FR-002 set"
        ),
        ConcernResponse(
            concern_id="C2", response="pinned to a test", what_changed="SC-001 set"
        ),
    ]


def _ok_audit() -> str:
    return "```yaml\nok: true\nproblems: []\n```"


def _flag_audit(problem: str) -> str:
    return f"```yaml\nok: false\nproblems:\n  - \"{problem}\"\n```"


# --- self_consistency_pass (the audit call) -------------------------------


def test_self_consistency_pass_clean_returns_ok():
    backend = _QueueBackend(replies=[_ok_audit()])
    result = self_consistency_pass(
        backend=backend,
        model=None,
        revised_artifacts={"specs/000-x/spec.md": "FR-002 threshold 0.5"},
        concerns=_concerns(),
        responses=_responses(),
        repo_root=_REPO_ROOT,
    )
    assert isinstance(result, SelfConsistencyResult)
    assert result.ok is True
    assert result.problems == []
    assert len(backend.calls) == 1  # exactly one audit call


def test_self_consistency_pass_flags_problem():
    backend = _QueueBackend(replies=[_flag_audit("C1 still unresolved in FR-002")])
    result = self_consistency_pass(
        backend=backend,
        model=None,
        revised_artifacts={"specs/000-x/spec.md": "FR-002 unchanged"},
        concerns=_concerns(),
        responses=_responses(),
        repo_root=_REPO_ROOT,
    )
    assert result.ok is False
    assert result.problems == ["C1 still unresolved in FR-002"]


def test_self_consistency_pass_backend_error_falls_back_ok():
    """An exhausted/erroring backend must NOT crash — falls back to ok=True."""
    backend = _QueueBackend(replies=[])  # immediately raises on chat()
    result = self_consistency_pass(
        backend=backend,
        model=None,
        revised_artifacts={"specs/000-x/spec.md": "x"},
        concerns=_concerns(),
        responses=_responses(),
        repo_root=_REPO_ROOT,
    )
    assert result.ok is True
    assert result.problems == []


def test_self_consistency_pass_unparseable_falls_back_ok():
    """A non-YAML / non-mapping reply must fall back to ok=True (no crash)."""
    backend = _QueueBackend(replies=["this is not yaml: [unclosed"])
    result = self_consistency_pass(
        backend=backend,
        model=None,
        revised_artifacts={"specs/000-x/spec.md": "x"},
        concerns=_concerns(),
        responses=_responses(),
        repo_root=_REPO_ROOT,
    )
    assert result.ok is True
    assert result.problems == []


# --- run_with_self_consistency (orchestration) ----------------------------


def test_run_clean_audit_no_corrective_pass():
    """Clean first pass + OK audit → returns first-pass output, redo NOT called."""
    backend = _QueueBackend(replies=[_ok_audit()])
    first = ({"a": "v1"}, _responses())
    redo_calls: list[str] = []

    def redo(extra: str):
        redo_calls.append(extra)
        return ({"a": "v2"}, _responses())

    updated, responses = run_with_self_consistency(
        backend=backend,
        model=None,
        repo_root=_REPO_ROOT,
        concerns=_concerns(),
        first_pass=first,
        redo=redo,
    )
    assert updated == {"a": "v1"}  # first-pass output preserved
    assert redo_calls == []  # no corrective re-pass
    assert {r.concern_id for r in responses} == {"C1", "C2"}


def test_run_flagged_audit_triggers_one_corrective_pass():
    """Audit flags a problem → exactly ONE corrective redo → corrected output."""
    backend = _QueueBackend(replies=[_flag_audit("C1 not actually fixed")])
    first = ({"a": "v1"}, _responses())
    redo_calls: list[str] = []

    def redo(extra: str):
        redo_calls.append(extra)
        return ({"a": "v2-corrected"}, _responses())

    updated, responses = run_with_self_consistency(
        backend=backend,
        model=None,
        repo_root=_REPO_ROOT,
        concerns=_concerns(),
        first_pass=first,
        redo=redo,
    )
    assert updated == {"a": "v2-corrected"}  # corrected output returned
    assert len(redo_calls) == 1  # exactly one corrective pass
    assert "C1 not actually fixed" in redo_calls[0]  # problem appended to task
    assert {r.concern_id for r in responses} == {"C1", "C2"}  # log still complete


def test_run_corrective_loop_runs_at_most_once():
    """Even if a hypothetical 2nd audit would still complain, redo runs ONCE.

    The audit is only consulted before the corrective pass; the corrected
    output is returned without re-auditing. We prove this by queueing a
    SECOND flag reply that must never be consumed.
    """
    backend = _QueueBackend(
        replies=[_flag_audit("first problem"), _flag_audit("second problem")]
    )
    first = ({"a": "v1"}, _responses())
    redo_calls: list[str] = []

    def redo(extra: str):
        redo_calls.append(extra)
        return ({"a": "v2"}, _responses())

    updated, _ = run_with_self_consistency(
        backend=backend,
        model=None,
        repo_root=_REPO_ROOT,
        concerns=_concerns(),
        first_pass=first,
        redo=redo,
    )
    assert updated == {"a": "v2"}
    assert len(redo_calls) == 1  # NOT two — at most one corrective pass
    assert len(backend.calls) == 1  # only the first audit was consumed


# --- end-to-end wiring on SpecReviser -------------------------------------


def _spec_with_marker() -> str:
    return (
        "# Spec — PROJ-test-x\n\n"
        "## Functional Requirements\n"
        "- FR-002: System SHOULD [NEEDS CLARIFICATION: pick a threshold].\n\n"
        "## Success Criteria\n"
        "- SC-001: First user finishes in < 5 minutes.\n"
    )


def _spec_revise_reply(spec_text: str) -> str:
    return json.dumps(
        {
            "new_spec_md": spec_text,
            "responses": [
                {
                    "concern_id": "C1",
                    "response": "named threshold 0.5",
                    "what_changed": "FR-002 now names 0.5",
                    "artifacts_changed": ["specs/000-x/spec.md"],
                },
                {
                    "concern_id": "C2",
                    "response": "pinned SC-001 to a test",
                    "what_changed": "added pytest path",
                    "artifacts_changed": ["specs/000-x/spec.md"],
                },
            ],
        }
    )


def test_spec_reviser_clean_first_pass_no_correction(tmp_path: Path):
    """SpecReviser: clean first pass + OK audit → first-pass spec returned,
    no corrective re-pass (only 2 backend calls: revise + audit)."""
    spec_path = "specs/000-x/spec.md"
    first_spec = (
        "# Spec — PROJ-test-x\n\n"
        "## Functional Requirements\n- FR-002: threshold 0.5.\n\n"
        "## Success Criteria\n- SC-001: finishes in < 5 minutes "
        "(measured by `tests/e2e/test_flow.py`).\n"
    )
    backend = _QueueBackend(
        replies=[_spec_revise_reply(first_spec), _ok_audit()]
    )
    reviser = SpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "cache",
    )
    updated, responses = reviser.revise({spec_path: _spec_with_marker()}, _concerns())

    assert updated[spec_path] == first_spec
    assert _scan_markers(updated[spec_path]) == []
    assert {r.concern_id for r in responses} == {"C1", "C2"}
    assert len(backend.calls) == 2  # revise + audit, no correction


def test_spec_reviser_flagged_audit_runs_one_correction(tmp_path: Path):
    """SpecReviser: audit flags a problem → ONE corrective revise → corrected
    spec returned, change-log still complete (one response per concern)."""
    spec_path = "specs/000-x/spec.md"
    first_spec = (
        "# Spec — PROJ-test-x\n\n## Functional Requirements\n"
        "- FR-002: threshold 0.5.\n\n## Success Criteria\n- SC-001: < 5 min.\n"
    )
    corrected_spec = (
        "# Spec — PROJ-test-x (corrected)\n\n## Functional Requirements\n"
        "- FR-002: threshold 0.5.\n\n## Success Criteria\n"
        "- SC-001: < 5 min (measured by `tests/e2e/test_flow.py`).\n"
    )
    backend = _QueueBackend(
        replies=[
            _spec_revise_reply(first_spec),
            _flag_audit("SC-001 still has no measurement procedure"),
            _spec_revise_reply(corrected_spec),
        ]
    )
    reviser = SpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "cache",
    )
    updated, responses = reviser.revise({spec_path: _spec_with_marker()}, _concerns())

    assert updated[spec_path] == corrected_spec  # corrected output returned
    assert {r.concern_id for r in responses} == {"C1", "C2"}  # log complete
    assert len(backend.calls) == 3  # revise + audit + ONE corrective revise
    # The corrective revise prompt must carry the flagged problem.
    corrective_user_msg = backend.calls[2][1].content
    assert "SC-001 still has no measurement procedure" in corrective_user_msg


def test_spec_reviser_audit_failure_falls_back_to_first_pass(tmp_path: Path):
    """SpecReviser with a SINGLE queued reply (the classic existing-test
    shape): the audit's 2nd backend call raises → caught → first-pass output
    returned unchanged, with one ConcernResponse per concern. This is the
    regression-safety guarantee for the ~50 existing reviser tests."""
    spec_path = "specs/000-x/spec.md"
    first_spec = (
        "# Spec — PROJ-test-x\n\n## Functional Requirements\n"
        "- FR-002: threshold 0.5.\n\n## Success Criteria\n"
        "- SC-001: < 5 min (measured by `tests/e2e/test_flow.py`).\n"
    )
    backend = _QueueBackend(replies=[_spec_revise_reply(first_spec)])  # only ONE reply
    reviser = SpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "cache",
    )
    updated, responses = reviser.revise({spec_path: _spec_with_marker()}, _concerns())

    assert updated[spec_path] == first_spec  # first-pass output, unchanged
    assert {r.concern_id for r in responses} == {"C1", "C2"}  # log complete
    assert len(backend.calls) == 2  # revise + the (failed) audit attempt


def test_spec_reviser_no_concerns_audit_still_runs(tmp_path: Path):
    """With zero concerns the reviser still produces a spec; the audit runs
    and a clean verdict returns the first-pass output."""
    spec_path = "specs/000-x/spec.md"
    clean_spec = "# Spec\n\n## Functional Requirements\n- FR-001: do X.\n"
    backend = _QueueBackend(
        replies=[
            json.dumps({"new_spec_md": clean_spec, "responses": []}),
            _ok_audit(),
        ]
    )
    reviser = SpecReviser(
        backend=backend,
        repo_root=_REPO_ROOT,
        project_id="PROJ-000-x",
        summarize_cache_dir=tmp_path / "cache",
    )
    updated, responses = reviser.revise({spec_path: clean_spec}, [])
    assert updated[spec_path] == clean_spec
    assert responses == []


# --- parsing edge: ok/problems disagreement -------------------------------


def test_parse_problems_win_over_ok_true():
    """If the model says ok:true but lists problems, problems win (ok=False)."""
    backend = _QueueBackend(
        replies=['```yaml\nok: true\nproblems:\n  - "contradiction in FR-003"\n```']
    )
    result = self_consistency_pass(
        backend=backend,
        model=None,
        revised_artifacts={"specs/000-x/spec.md": "x"},
        concerns=_concerns(),
        responses=_responses(),
        repo_root=_REPO_ROOT,
    )
    assert result.ok is False
    assert result.problems == ["contradiction in FR-003"]
