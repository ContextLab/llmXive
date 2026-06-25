"""Best-so-far convergence: a reviser that REGRESSES a near-clean artifact must
not poison the panel.

Live failure (PROJ-492 spec panel, trajectory 27->2->32->14): the reviser
regenerates the whole spec each round and sometimes drops the FR->US anchors it
had just added; the accepter lenses correctly re-flag the regression, and the
engine — feeding that regressed artifact to the next revise — compounds the drift
and never converges even though an earlier round was nearly clean. The engine now
keeps the fewest-concern artifact and refines from THAT, so a regressing round is
discarded rather than built upon.
"""

from __future__ import annotations

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.types import Concern, ReviewSpec, Severity, Verdict


def _c(cid: str, reviewer: str = "A") -> Concern:
    return Concern(id=cid, reviewer=reviewer, severity=Severity.WRITING, artifact="a.md", text="t")


class _RegressionReviewer:
    """Passes its open concern once the fix marker is present, but raises new
    breakage concerns whenever the artifact also contains the BROKE marker."""

    name = "A"

    def identify(self, artifacts, *, constitution, advisory):
        return [] if "FIXED1" in artifacts.get("a.md", "") else [_c("c1")]

    def rereview(self, artifacts, own, responses, *, constitution, advisory):
        text = artifacts.get("a.md", "")
        broke = [_c("cbad1"), _c("cbad2")] if "BROKE" in text else []
        out = []
        for c in own:
            status = "pass" if "FIXED1" in text else "fail"
            out.append(
                Verdict(concern_id=c.id, reviewer=self.name, status=status,
                        new_concerns=broke if c.id == own[0].id else [])
            )
        return out


class _RegressingReviser:
    """First revise introduces a fix AND breakage (FIXED1 + BROKE). A later
    revise can only produce a clean fix when given a base that is NOT already
    BROKE — i.e. only when the engine refines the best (pre-regression) artifact."""

    def __init__(self) -> None:
        self.calls = 0

    def revise(self, artifacts, concerns):
        from llmxive.convergence.types import ConcernResponse
        self.calls += 1
        base = artifacts.get("a.md", "")
        if self.calls == 1:
            new_text = base + " FIXED1 BROKE"          # regression on the first fix
        elif "BROKE" in base:
            new_text = base                              # stuck: cannot un-break a broken base
        else:
            new_text = base + " FIXED1"                  # clean fix from a clean base
        resps = [ConcernResponse(concern_id=c.id, response="ok", what_changed="e") for c in concerns]
        return {"a.md": new_text}, resps


def _spec(reviewer, reviser) -> ReviewSpec:
    return ReviewSpec(
        stage="planned", artifacts=["a.md"], reviewers=[reviewer], reviser=reviser,
        kickback_routing={Severity.WRITING: "clarified", Severity.FATAL: "brainstormed"},
        overflow_goal="x", advance_stage="tasked", max_rounds=3,
    )


def test_best_so_far_converges_through_a_regressing_round() -> None:
    reviser = _RegressingReviser()
    res = run_convergence(_spec(_RegressionReviewer(), reviser), {"a.md": "init"})
    # Round 1 fix regresses (BROKE) -> 2 concerns; best-so-far reverts to the
    # pre-regression base and the next revise produces a clean fix -> converged.
    assert res.converged, f"expected convergence via best-so-far; got {res!r}"


def test_provably_false_orphan_concerns_are_dropped() -> None:
    """A reviewer that flags an FR as "not anchored to any user story" when the
    FR's line explicitly says "(See US-1)" is provably WRONG; the engine drops it
    so the panel isn't blocked by a false positive the reviser cannot fix (the
    PROJ-492 spec stall). Genuinely orphaned FRs and non-traceability concerns
    are kept — this makes review RELIABLE, it does not lower the bar."""
    from llmxive.convergence.engine import _drop_false_orphan_concerns
    from llmxive.convergence.types import Concern, Severity

    arts = {"spec.md": "**FR-001**: accept URLs (See US-1)\n**FR-007**: no anchor here\n"}

    def C(t):
        return Concern(id="x", reviewer="scope", severity=Severity.REQUIREMENT,
                       artifact="spec.md", text=t)

    cons = [
        C("FR-001 is not anchored to any user story, breaking traceability."),  # false
        C("FR-007 is orphaned; no user story references it."),                   # true
        C("FR-001 uses a vague threshold that is untestable."),                  # not orphan
    ]
    kept = _drop_false_orphan_concerns(cons, arts)
    texts = [c.text for c in kept]
    assert not any("not anchored" in t for t in texts)   # the false one is gone
    assert any("FR-007 is orphaned" in t for t in texts)  # the real one stays
    assert any("untestable" in t for t in texts)          # non-traceability stays
