"""Unit tests for adaptive kickback routing (spec 015 T020)."""

from __future__ import annotations

import pytest

from llmxive.convergence.kickback import progress_record, route_kickback
from llmxive.convergence.types import Concern, ReviewSpec, Severity


def _spec(routing: dict[Severity, str]) -> ReviewSpec:
    return ReviewSpec(
        stage="planned", artifacts=["plan.md"], reviewers=[], reviser=None,
        kickback_routing=routing, overflow_goal="preserve ids", max_rounds=3,
    )


def _c(cid: str, sev: Severity, artifact: str = "plan.md") -> Concern:
    return Concern(id=cid, reviewer="r", severity=sev, artifact=artifact, text="t")


def test_routes_to_worst_severity_stage():
    spec = _spec({Severity.WRITING: "clarified", Severity.METHODOLOGY: "planned",
                  Severity.FATAL: "brainstormed"})
    kb = route_kickback(spec, [_c("c1", Severity.WRITING), _c("c2", Severity.FATAL)])
    assert kb.worst_severity == Severity.FATAL
    assert kb.to_stage == "brainstormed"
    assert kb.from_stage == "planned"


def test_nearest_routing_fallback():
    spec = _spec({Severity.METHODOLOGY: "planned"})
    # worst below the only entry -> use the nearest higher
    assert route_kickback(spec, [_c("c", Severity.WRITING)]).to_stage == "planned"
    # worst above the only entry -> use the nearest lower
    assert route_kickback(spec, [_c("c", Severity.FATAL)]).to_stage == "planned"


def test_record_carries_full_provenance():
    spec = _spec({Severity.WRITING: "clarified"})
    kb = route_kickback(spec, [_c("c1", Severity.WRITING, artifact="data-model.md")])
    assert len(kb.unresolved_concerns) == 1
    assert "data-model.md" in kb.artifact_links and "plan.md" in kb.artifact_links
    assert kb.reason and "unresolved" in kb.reason


def test_empty_unresolved_raises():
    with pytest.raises(ValueError):
        route_kickback(_spec({Severity.WRITING: "clarified"}), [])


def test_progress_record_improved_flag():
    first = progress_record(0, [_c("a", Severity.WRITING)], None)
    assert first.improved is True
    same = progress_record(1, [_c("a", Severity.WRITING)], {"a"})
    assert same.improved is False  # identical unresolved set -> not improving
    changed = progress_record(2, [_c("b", Severity.WRITING)], {"a"})
    assert changed.improved is True
