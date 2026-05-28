"""Contract tests for the convergence data model (spec 015 T004-T006)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from llmxive.convergence.types import (
    Concern,
    ConvergenceResult,
    KickbackRecord,
    Severity,
    Verdict,
    from_legacy_severity,
    severity_rank,
    worst_severity,
)


def test_severity_ordering_least_to_most_serious():
    order = [
        Severity.TRIVIAL, Severity.CODE, Severity.WRITING, Severity.REQUIREMENT,
        Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL,
    ]
    ranks = [severity_rank(s) for s in order]
    assert ranks == sorted(ranks)
    assert ranks == list(range(len(order)))


def test_worst_severity_picks_most_serious():
    assert worst_severity([Severity.TRIVIAL, Severity.FATAL, Severity.WRITING]) == Severity.FATAL
    assert worst_severity([Severity.CODE]) == Severity.CODE
    with pytest.raises(ValueError):
        worst_severity([])


def test_legacy_severity_mapping_back_compat():
    assert from_legacy_severity("writing") == Severity.WRITING
    assert from_legacy_severity("science") == Severity.SCIENCE
    assert from_legacy_severity("fatal") == Severity.FATAL
    with pytest.raises(ValueError):
        from_legacy_severity("not-a-severity")


def test_concern_strict_rejects_unknown_field():
    Concern(id="c1", reviewer="plan.methodology", severity=Severity.METHODOLOGY,
            artifact="plan.md", location="§3", text="unsound")
    with pytest.raises(ValidationError):
        Concern(id="c1", reviewer="r", severity=Severity.CODE, artifact="a",
                text="t", bogus_field="x")


def test_verdict_status_constrained():
    Verdict(concern_id="c1", reviewer="r", status="pass")
    Verdict(concern_id="c1", reviewer="r", status="fail",
            new_concerns=[Concern(id="c2", reviewer="r", severity=Severity.WRITING,
                                  artifact="a", text="t")])
    with pytest.raises(ValidationError):
        Verdict(concern_id="c1", reviewer="r", status="maybe")


def test_convergence_result_honest_fields():
    # converged result -> next_stage set, no kickback
    ok = ConvergenceResult(stage="planned", converged=True, rounds_used=1,
                           next_stage="tasked")
    assert ok.converged and ok.kickback is None
    # non-converged -> kickback carries provenance
    kb = KickbackRecord(from_stage="planned", to_stage="clarified",
                        worst_severity=Severity.METHODOLOGY,
                        reason="methodology unresolved after 3 rounds")
    bad = ConvergenceResult(stage="planned", converged=False, rounds_used=3, kickback=kb)
    assert not bad.converged and bad.kickback is not None
    assert bad.kickback.worst_severity == Severity.METHODOLOGY


def test_records_roundtrip_json():
    c = Concern(id="c1", reviewer="r", severity=Severity.SCIENCE, artifact="a", text="t")
    assert Concern.model_validate_json(c.model_dump_json()) == c
