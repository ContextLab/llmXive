"""Persist-before-abort (observability): when a CLEAN-ABORT backend failure
(``BackendUnavailable`` from an open circuit breaker, or ``TransientBackendError``
/ ``DeadlineExceededError`` from a hung/flapping endpoint) propagates out of the
convergence round loop, the engine invokes an ``on_abort(round_index, reason)``
hook BEFORE re-raising — so an unattended run leaves an OBSERVABLE record of
WHERE and WHY it aborted instead of the silent zero-trail run that hid the
PROJ-552 plan-stage CI aborts (a 3.5h step that committed nothing). The original
exception is NEVER masked, and a converging run never fires ``on_abort``.

Real in-memory reviewers/revisers (no mocks); the abort is raised by the same
seam (``identify`` / ``revise`` / ``rereview``) where the real backend breaker
raises.
"""

from __future__ import annotations

import json

import pytest

from llmxive.backends.base import BackendUnavailable, TransientBackendError
from llmxive.convergence.engine import run_convergence
from llmxive.convergence.types import (
    Concern,
    ConcernResponse,
    ReviewSpec,
    Severity,
    Verdict,
)


def _c(cid: str, reviewer: str = "rev", sev: Severity = Severity.WRITING) -> Concern:
    return Concern(id=cid, reviewer=reviewer, severity=sev, artifact="a.md", text="t")


def _spec(reviewers, reviser, *, max_rounds: int = 3) -> ReviewSpec:
    return ReviewSpec(
        stage="planned", artifacts=["a.md"], reviewers=reviewers, reviser=reviser,
        kickback_routing={
            Severity.WRITING: "clarified",
            Severity.METHODOLOGY: "clarified",
            Severity.FATAL: "brainstormed",
        },
        overflow_goal="preserve ids", advance_stage="tasked", max_rounds=max_rounds,
    )


class _IdentifyAborts:
    """Reviewer whose R1 ``identify`` raises the given abort exception."""

    def __init__(self, exc: Exception, name: str = "rev") -> None:
        self.name = name
        self._exc = exc

    def identify(self, artifacts, *, constitution, advisory):
        raise self._exc

    def rereview(self, artifacts, own, responses, *, constitution, advisory):
        return []


class _IdentifyOk:
    """Reviewer that raises one concern in R1, then passes its own in re-review."""

    def __init__(self, name: str = "rev") -> None:
        self.name = name

    def identify(self, artifacts, *, constitution, advisory):
        return [_c("c1", self.name)]

    def rereview(self, artifacts, own, responses, *, constitution, advisory):
        return [Verdict(concern_id=c.id, reviewer=self.name, status="pass") for c in own]


class _OkReviewer:
    """Reviewer that finds nothing -> the run converges in R1."""

    name = "rev"

    def identify(self, artifacts, *, constitution, advisory):
        return []

    def rereview(self, artifacts, own, responses, *, constitution, advisory):
        return []


class _OkReviser:
    def revise(self, artifacts, concerns):
        new = {"a.md": artifacts.get("a.md", "") + "\n<rev>"}
        return new, [
            ConcernResponse(concern_id=c.id, response="addressed", what_changed="edit")
            for c in concerns
        ]


class _AbortingReviser:
    """Reviser whose ``revise`` raises the given abort exception (R2 abort)."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def revise(self, artifacts, concerns):
        raise self._exc


class _RecordingAbort:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str]] = []

    def __call__(self, round_index: int, reason: str) -> None:
        self.calls.append((round_index, reason))


@pytest.mark.parametrize(
    "exc",
    [BackendUnavailable("circuit breaker open"), TransientBackendError("hung past deadline")],
)
def test_identify_abort_flushes_on_abort_then_reraises(exc: Exception) -> None:
    rec = _RecordingAbort()
    with pytest.raises(type(exc)):
        run_convergence(
            _spec([_IdentifyAborts(exc)], _AbortingReviser(exc)),
            {"a.md": "x"},
            on_abort=rec,
        )
    assert len(rec.calls) == 1, "on_abort must fire exactly once on a clean abort"
    rnd, reason = rec.calls[0]
    assert rnd == 1, "an R1-identify abort is recorded at round 1 (the CI zero-trail case)"
    assert type(exc).__name__ in reason
    assert str(exc) in reason


def test_revise_abort_flushes_with_later_round_index() -> None:
    exc = TransientBackendError("endpoint dropped mid-revision")
    rec = _RecordingAbort()
    with pytest.raises(TransientBackendError):
        run_convergence(
            _spec([_IdentifyOk()], _AbortingReviser(exc)),
            {"a.md": "x"},
            on_abort=rec,
        )
    assert len(rec.calls) == 1
    rnd, reason = rec.calls[0]
    assert rnd >= 2, "identify (round 1) completed; the abort is recorded in a later round"
    assert "TransientBackendError" in reason


def test_no_abort_hook_still_reraises_unchanged() -> None:
    """Backward-compat: without on_abort the original exception still propagates
    and nothing crashes (the hook is purely additive observability)."""
    exc = BackendUnavailable("down")
    with pytest.raises(BackendUnavailable):
        run_convergence(_spec([_IdentifyAborts(exc)], _OkReviser()), {"a.md": "x"})


def test_buggy_on_abort_never_masks_the_real_abort() -> None:
    """A throwing on_abort hook must NOT replace/swallow the genuine backend abort
    (observability is best-effort; the abort is the signal that must surface)."""

    def boom(round_index: int, reason: str) -> None:
        raise ValueError("hook is buggy")

    e = BackendUnavailable("real outage")
    with pytest.raises(BackendUnavailable):
        run_convergence(
            _spec([_IdentifyAborts(e)], _OkReviser()), {"a.md": "x"}, on_abort=boom
        )


def test_converging_run_never_fires_on_abort() -> None:
    rec = _RecordingAbort()
    res = run_convergence(
        _spec([_OkReviewer()], _AbortingReviser(BackendUnavailable("x"))),
        {"a.md": "x"},
        on_abort=rec,
    )
    assert res.converged is True
    assert rec.calls == [], "a clean convergence must not invoke the abort hook"


def test_stage_panel_abort_hook_writes_aborted_trail_record(tmp_path) -> None:
    """The ``_stage_panel`` abort hook appends an ``{round, aborted}`` record to the
    SAME convergence trail the round hook writes — so the abort is visible in the
    committed provenance, not just the run-log."""
    from llmxive.speckit._stage_panel import _make_abort_hook

    trail = tmp_path / "plan-001.jsonl"
    hook = _make_abort_hook(trail)
    hook(2, "DeadlineExceededError: model gave no response within 360s")

    lines = trail.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["round"] == 2
    assert "DeadlineExceededError" in rec["aborted"]
