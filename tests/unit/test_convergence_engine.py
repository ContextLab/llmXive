"""Unit tests for the convergence engine round loop (spec 015 T019/T028).

Uses real in-memory Reviewer/Reviser implementations (not mocks) to exercise the
engine's actual R1->R2->R3 orchestration, cap, honest reporting, self-review
exclusion, stale handling, and per-round budget.
"""

from __future__ import annotations

import time

import pytest

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


class FakeReviewer:
    """Real Reviewer impl: raises fixed R1 concerns, judges them per-round."""

    def __init__(self, name="rev", r1=None, *, pass_at=None, stale=(), selfreview=(),
                 add_in_round=None):
        self.name = name
        self._r1 = list(r1 or [])
        self.pass_at = dict(pass_at or {})      # cid -> round at/after which it passes (default 1)
        self.stale = set(stale)
        self.selfreview = set(selfreview)
        self.add_in_round = dict(add_in_round or {})  # round -> [Concern]
        self.rereview_calls = 0

    def identify(self, artifacts, *, constitution, advisory):
        return list(self._r1)

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
        self.rereview_calls += 1
        rnd = self.rereview_calls
        verdicts: list[Verdict] = []
        for c in own_concerns:
            if c.id in self.stale:
                verdicts.append(Verdict(concern_id=c.id, reviewer=self.name, status="pass", stale=True))
            elif c.id in self.selfreview:
                verdicts.append(Verdict(concern_id=c.id, reviewer=self.name, status="pass", self_review=True))
            else:
                status = "pass" if rnd >= self.pass_at.get(c.id, 1) else "fail"
                verdicts.append(Verdict(concern_id=c.id, reviewer=self.name, status=status))
        extra = self.add_in_round.get(rnd)
        if extra:
            (verdicts or [Verdict(concern_id="_", reviewer=self.name, status="pass")])[-1].new_concerns.extend(extra)
            if not verdicts:
                verdicts.append(Verdict(concern_id="_", reviewer=self.name, status="pass", new_concerns=extra))
        return verdicts


class FakeReviser:
    def __init__(self, *, sleep=0.0):
        self.calls = 0
        self.sleep = sleep

    def revise(self, artifacts, concerns):
        self.calls += 1
        if self.sleep:
            time.sleep(self.sleep)
        new = {"a.md": artifacts.get("a.md", "") + f"\n<rev{self.calls}>"}
        return new, [ConcernResponse(concern_id=c.id, response="addressed", what_changed="edit")
                     for c in concerns]


def _spec(reviewers, reviser, *, max_rounds=3, exempt=False) -> ReviewSpec:
    return ReviewSpec(
        stage="planned", artifacts=["a.md"], reviewers=reviewers, reviser=reviser,
        kickback_routing={Severity.WRITING: "clarified", Severity.METHODOLOGY: "clarified",
                          Severity.FATAL: "brainstormed"},
        overflow_goal="preserve ids", advance_stage="tasked", max_rounds=max_rounds,
        exempt=exempt,
    )


def test_converges_immediately_when_no_concerns():
    rev = FakeReviewer(r1=[])
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is True
    assert res.rounds_used == 0
    assert res.next_stage == "tasked"
    assert res.kickback is None


def test_converges_after_one_revision():
    rev = FakeReviewer(r1=[_c("c1")])  # passes on first re-review
    reviser = FakeReviser()
    res = run_convergence(_spec([rev], reviser), {"a.md": "x"})
    assert res.converged is True
    assert res.rounds_used == 1
    assert reviser.calls == 1
    assert res.next_stage == "tasked"


def test_kickback_when_unresolved_after_cap():
    rev = FakeReviewer(r1=[_c("c1", sev=Severity.METHODOLOGY)], pass_at={"c1": 99})
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is False        # honest reporting (FR-016)
    assert res.rounds_used == 3
    assert res.next_stage is None
    assert res.kickback is not None
    assert res.kickback.worst_severity == Severity.METHODOLOGY
    assert res.kickback.to_stage == "clarified"


def test_stale_verdict_never_counts_as_pass():
    rev = FakeReviewer(r1=[_c("c1")], stale={"c1"})
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is False and res.kickback is not None


def test_self_review_flag_never_counts_as_pass():
    rev = FakeReviewer(r1=[_c("c1")], selfreview={"c1"})
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is False


def test_producer_reviewer_excluded():
    # revA would raise a blocking concern, but it produced the artifact -> excluded.
    revA = FakeReviewer(name="revA", r1=[_c("ca", reviewer="revA", sev=Severity.FATAL)],
                        pass_at={"ca": 99})
    revB = FakeReviewer(name="revB", r1=[])
    res = run_convergence(_spec([revA, revB], FakeReviser()), {"a.md": "x"}, producer="revA")
    assert res.converged is True          # revA excluded -> no concern raised
    assert res.concern_history == []
    assert revA.rereview_calls == 0


def test_new_concern_in_r3_is_tracked_and_resolved():
    rev = FakeReviewer(r1=[_c("c1")], add_in_round={1: [_c("c2", sev=Severity.WRITING)]})
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is True
    assert res.rounds_used == 2           # c1 round1, c2 surfaced then resolved round2
    assert any(c.id == "c2" for c in res.concern_history)


def test_exempt_stage_raises():
    with pytest.raises(ValueError):
        run_convergence(_spec([FakeReviewer(r1=[])], FakeReviser(), exempt=True), {"a.md": "x"})


def test_per_round_budget_short_circuits():
    rev = FakeReviewer(r1=[_c("c1")], pass_at={"c1": 99})
    reviser = FakeReviser(sleep=0.02)
    res = run_convergence(_spec([rev], reviser, max_rounds=5), {"a.md": "x"},
                          per_round_budget_s=0.001)
    assert res.rounds_used == 1           # budget cut it short before the 5-round cap
    assert res.converged is False
