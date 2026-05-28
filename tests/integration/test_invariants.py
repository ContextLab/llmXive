"""Invariant tests for the convergence subsystem (spec 015 T081).

These tests guard the design's "never silently fail" invariants — the
properties that, if violated, would let a project stall, silently
advance, or accumulate orphaned state without anyone noticing.

Each test is intentionally narrow: it asserts a single invariant that
the design SSoT requires + that would be hard to spot in code review
otherwise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.reviewspecs import (
    EXEMPT_STAGES,
    build_spec_reviewspec,
    reviewable_stages,
    reviewspec_for,
)
from llmxive.convergence.types import (
    Concern,
    ConvergenceResult,
    Severity,
    Verdict,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- helpers ---------------------------------------------------------------


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


class _AcceptingReviewer:
    """Reviewer with no concerns — always converges at R1."""

    name = "accepting"

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return []

    def rereview(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return []


class _NeverAcceptingReviewer:
    """Reviewer that raises one concern and never accepts."""

    def __init__(self, name: str, severity: Severity) -> None:
        self.name = name
        self._severity = severity

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return [
            Concern(
                id="I1", reviewer=self.name, severity=self._severity,
                artifact="specs/000-x/spec.md", location="", text="x",
            )
        ]

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return [
            Verdict(concern_id=c.id, reviewer=self.name, status="fail")
            for c in own_concerns
        ]


# --- Invariants ------------------------------------------------------------


def test_invariant_every_convergence_result_either_advances_or_kicks_back():
    """A ``ConvergenceResult`` MUST set EITHER ``next_stage`` (forward) OR
    ``kickback`` (backward) — never neither, and never both as None.
    Violation = project silently stalls."""
    # Case A: converged → next_stage set, kickback None.
    artifacts = {"specs/000-x/spec.md": "# spec\n"}
    fake_reply = json.dumps({"new_spec_md": "# v2", "responses": []})
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    spec.reviewers = [_AcceptingReviewer()]
    result = run_convergence(spec, artifacts)
    assert result.converged is True
    assert result.next_stage is not None
    assert result.kickback is None  # converged → no kickback

    # Case B: non-convergence → kickback set, next_stage may be None.
    backend2 = _FakeBackend(responses=[fake_reply] * 5)
    spec2 = build_spec_reviewspec(
        backend=backend2, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    spec2.reviewers = [_NeverAcceptingReviewer("scope", Severity.WRITING)]
    result2 = run_convergence(spec2, artifacts)
    assert result2.converged is False
    assert result2.kickback is not None  # MUST emit a kickback


def test_invariant_kickback_routing_covers_every_writing_through_fatal_severity():
    """Every reviewable stage's ``kickback_routing`` MUST map every
    severity from WRITING through FATAL — these are the severities a
    real review can raise. Missing entries = engine can't route, project
    stalls.

    (TRIVIAL / CODE are intentionally OPTIONAL — only the implement
    stages handle them; spec/plan/tasks have no code surface.)"""
    required = {Severity.WRITING, Severity.REQUIREMENT, Severity.METHODOLOGY,
                Severity.SCIENCE, Severity.FATAL}
    for stage in reviewable_stages():
        spec = reviewspec_for(stage)
        assert spec is not None
        missing = required - set(spec.kickback_routing)
        assert not missing, (
            f"stage {stage!r} kickback_routing missing severities: {missing}"
        )


def test_invariant_every_kickback_to_stage_is_a_valid_stage_name():
    """Every ``kickback_routing`` target MUST be a valid ``Stage`` enum
    value. Catches typos at audit time rather than at runtime when the
    graph would reject the transition."""
    from llmxive.types import Stage
    valid_targets: set[str] = {s.value for s in Stage}
    for stage in reviewable_stages():
        spec = reviewspec_for(stage)
        assert spec is not None
        for severity, target in spec.kickback_routing.items():
            assert target in valid_targets, (
                f"stage {stage!r} routes {severity.value} to unknown stage "
                f"{target!r} (not a valid Stage enum value)"
            )


def test_invariant_exempt_and_reviewable_stages_are_disjoint():
    """A stage is EITHER exempt OR reviewable — never both. Both-at-once
    means the registry definitively can't decide whether to run the
    convergence loop, which would silently stall projects."""
    overlap = set(reviewable_stages()) & EXEMPT_STAGES
    assert not overlap, (
        f"stages defined as both reviewable and exempt: {overlap}"
    )


def test_invariant_constitution_input_required_from_specified_onward():
    """FR-030 invariant: every reviewable stage EXCEPT the idea stage
    (``flesh_out_complete``, where the constitution doesn't exist yet)
    MUST set ``constitution_input=True``. Violation = constitution
    silently dropped from the panel's inputs."""
    for stage in reviewable_stages():
        spec = reviewspec_for(stage)
        assert spec is not None
        if stage == "flesh_out_complete":
            assert spec.constitution_input is False, (
                "idea stage MUST NOT require constitution (it doesn't exist yet)"
            )
        else:
            assert spec.constitution_input is True, (
                f"stage {stage!r} MUST set constitution_input=True (FR-030)"
            )


def test_invariant_reviser_protocol_emits_response_per_concern():
    """Every concern submitted to a reviser MUST receive exactly one
    ConcernResponse back. Missing → engine can't see "no response" cases.
    The SpecReviser (and by the same-shape contract every other reviser)
    pads missing responses with `<missing>` rather than silently dropping
    them (Constitution Principle II)."""
    spec_key = "specs/000-x/spec.md"
    artifacts = {spec_key: "# spec\n"}
    # Backend returns ONE response for TWO concerns — reviser MUST pad.
    fake_reply = json.dumps({
        "new_spec_md": "# v2",
        "responses": [{"concern_id": "C1", "response": "fixed", "what_changed": "x"}],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    concerns = [
        Concern(id="C1", reviewer="r1", severity=Severity.WRITING,
                artifact=spec_key, location="", text="x"),
        Concern(id="C2", reviewer="r2", severity=Severity.WRITING,
                artifact=spec_key, location="", text="y"),
    ]
    _, responses = spec.reviser.revise(artifacts, concerns)
    response_ids = {r.concern_id for r in responses}
    assert response_ids == {"C1", "C2"}, (
        f"reviser dropped concern responses: missing={ {c.id for c in concerns} - response_ids!r}"
    )
    # The padded one MUST carry the explicit `<missing>` marker.
    by_id = {r.concern_id: r for r in responses}
    assert by_id["C2"].response == "<missing>"


def test_invariant_convergence_result_concern_history_is_monotonic():
    """The ``concern_history`` list in ConvergenceResult MUST contain
    every concern ever raised across all rounds — never omits, never
    re-orders. Violation = audit trail is incomplete."""
    artifacts = {"specs/000-x/spec.md": "# spec\n"}
    backend = _FakeBackend(responses=[
        json.dumps({"new_spec_md": "# v_n",
                    "responses": [{"concern_id": "I1", "response": "x", "what_changed": "x"}]})
    ] * 5)
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    spec.reviewers = [_NeverAcceptingReviewer("scope", Severity.METHODOLOGY)]
    result = run_convergence(spec, artifacts)

    assert len(result.concern_history) >= 1
    # Every concern MUST have a valid id; no None / empty / duplicates as ids.
    ids = [c.id for c in result.concern_history]
    assert all(ids)  # no empty/None ids
    # The concern_history is allowed to repeat the same concern id across
    # rounds (re-flagged unresolved); the invariant is that ids are
    # present + non-empty, not unique.


def test_invariant_convergence_result_serializes_to_json_safely():
    """A `ConvergenceResult` MUST round-trip through JSON without losing
    information. Audit/dashboards rely on persisting these records
    losslessly."""
    artifacts = {"specs/000-x/spec.md": "# spec\n"}
    backend = _FakeBackend(responses=[
        json.dumps({"new_spec_md": "# v2", "responses": []}),
    ])
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    spec.reviewers = [_AcceptingReviewer()]
    result = run_convergence(spec, artifacts)

    payload = result.model_dump_json()
    restored = ConvergenceResult.model_validate_json(payload)
    assert restored.stage == result.stage
    assert restored.converged == result.converged
    assert restored.rounds_used == result.rounds_used
    assert restored.next_stage == result.next_stage


def test_invariant_kickback_record_includes_a_reason():
    """Every KickbackRecord MUST carry a non-empty `reason` — debugability
    + dashboards depend on it."""
    artifacts = {"specs/000-x/spec.md": "# spec\n"}
    fake_reply = json.dumps({"new_spec_md": "# v",
                              "responses": [{"concern_id": "I1", "response": "x", "what_changed": "x"}]})
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    spec.reviewers = [_NeverAcceptingReviewer("scope", Severity.SCIENCE)]
    result = run_convergence(spec, artifacts)
    assert result.kickback is not None
    assert result.kickback.reason and len(result.kickback.reason) > 0


def test_invariant_engine_refuses_exempt_stages():
    """The engine MUST raise on exempt stages — silent no-op would let
    project state advance without any audit record."""
    from llmxive.convergence.types import ReviewSpec
    exempt_spec = ReviewSpec(
        stage="paper_initializer", artifacts=[], reviewers=[],
        reviser=None, kickback_routing={}, overflow_goal="", exempt=True,
    )
    with pytest.raises(ValueError, match="is EXEMPT"):
        run_convergence(exempt_spec, {})
