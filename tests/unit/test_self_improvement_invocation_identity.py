"""Audit-derived InvocationIdentity (spec 025 slice 1B, Task 6).

Every audit event here is built from the REAL slice-0 dataclass through the REAL
``_audit_payload`` projection, and every constructed event is run through the REAL
``validate_lane_event``. Hand-written payload dicts would let this suite pass against a
shape production never emits — which is exactly how the sink's ``snapshot_provenance``
datetime bug survived Slice 1A.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchCompleted,
    SelectionFailure,
)
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.audit_sink import _audit_payload
from llmxive.self_improvement.events import (
    REROUTE_FALLBACK_PROFILE,
    REROUTE_PRIMARY_PROFILE,
    REROUTE_RELAXED_CONSTRAINTS,
    REROUTE_TRIGGER,
    Event,
    derive_route_id,
    event_to_json,
    validate_lane_event,
)
from llmxive.self_improvement.invocation_identity import (
    InvocationIdentityError,
    build_invocation_identity,
)

TS = "2026-07-25T00:00:00+00:00"
OBSERVED = datetime(2026, 7, 25, tzinfo=UTC)
_MODEL = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="gemma-3-27b",
                  model_family="gemma", vendor="google")
_PROV = {"catalog": SnapshotProvenance(source="live", observed_at=OBSERVED, age_s=0.0)}
#: The projected form the identity actually reads back out of the log.
_PROV_JSON = {"catalog": {"source": "live", "observed_at": OBSERVED.isoformat(), "age_s": 0.0}}


def _raw_ev(etype, payload, eid, *, attempt="A1"):
    """A lane Event, NOT run through the write-boundary validator.

    Use only to model a stream that is already CORRUPT — see `_corrupt` below."""
    return Event(event_id=eid, event_type=etype, problem_id="P1", actor="a", payload=payload,
                 timestamp=TS, attempt_id=attempt, seq=0,
                 expected_problem_revision=0, resulting_problem_revision=1)


def _ev(etype, payload, eid, *, attempt="A1"):
    """Build a lane Event and PROVE it is well-formed against the real write-boundary
    validator, so a synthetic event in this file can never drift from a persisted one."""
    ev = _raw_ev(etype, payload, eid, attempt=attempt)
    validate_lane_event(json.loads(event_to_json(ev)))
    return ev


def _corrupt(event: Event, **changes) -> Event:
    """Mutate a validated event into one the writer would REFUSE.

    `_validate_review_rerouted` recomputes both route ids from the envelope `attempt_id` at
    WRITE time, so a reroute with a foreign attempt or a borrowed primary leg cannot be
    persisted at all. The reader still checks, because the log is a file on a git ref and a
    reader at a trust boundary should not assume its input was written by this code. These
    tests therefore model post-write corruption, NOT a reachable production path — which is
    exactly why they must bypass validation to construct their input.
    """
    return replace(event, **changes)


def _chain(route_id, eid="c"):
    return _ev("ChainResolved", _audit_payload(ChainResolved(
        route_id=route_id, requirement_digest="rq-1", prompt_digest="pd",
        context_digest="cd", snapshot_digest="sd", snapshot_provenance=_PROV,
        selection_policy_version=4, resolved_at=TS, explanation=("only free family",),
        candidates=(_MODEL,),
    )), eid)


def _done(route_id, eid="d", attempt="A1"):
    return _ev("DispatchCompleted", _audit_payload(DispatchCompleted(
        route_id=route_id, candidate_index=0, candidate=_MODEL, reservation_id=None,
    )), eid, attempt=attempt)


def _selfail(route_id, exception_type=REROUTE_TRIGGER, eid="s", message="none live"):
    return _ev("SelectionFailure", _audit_payload(SelectionFailure(
        route_id=route_id, exception_type=exception_type, message=message,
        requirement_digest="rq-1", snapshot_provenance=_PROV,
    )), eid)


_OP = "worthwhile-improvement:identify:abc123"
#: The two legs of _OP under attempt A1 — the ONLY route ids a valid reroute can name.
_R_PRIMARY = derive_route_id("A1", _OP, "primary")
_R_FALLBACK = derive_route_id("A1", _OP, "fallback")


def _rerouted(primary=_R_PRIMARY, fallback=_R_FALLBACK, operation_id=_OP, message="none live",
              eid="rr"):
    # Built from the SSoT constants `record_reroute` writes and `_validate_review_rerouted`
    # enforces, so this fixture cannot encode a combination production would refuse.
    return _ev("ReviewRerouted", {
        "operation_id": operation_id, "lens": "worthwhile-improvement",
        "primary_profile": REROUTE_PRIMARY_PROFILE,
        "fallback_profile": REROUTE_FALLBACK_PROFILE,
        "primary_route_id": primary, "fallback_route_id": fallback,
        "primary_failure": {"exception_type": REROUTE_TRIGGER, "message": message},
        "relaxed_constraints": list(REROUTE_RELAXED_CONSTRAINTS)}, eid)


def _build(events, route_id="R"):
    return build_invocation_identity(events, route_id=route_id, attempt_id="A1")


def test_success_identity_carries_full_selection_provenance():
    ii = _build([_chain("R"), _done("R")])
    assert ii is not None
    assert (ii.model, ii.family, ii.backend) == ("gemma-3-27b", "gemma", "dartmouth")
    assert (ii.serving_endpoint, ii.vendor) == ("chat", "google")   # reproduce WHY
    assert ii.snapshot_provenance == _PROV_JSON
    assert (ii.prompt_digest, ii.context_digest, ii.snapshot_digest) == ("pd", "cd", "sd")
    assert ii.selection_policy_version == 4
    assert ii.route_outcome == "success" and ii.degradation is None
    assert ii.actor_instance_id == "R"


def test_degradation_joins_the_primary_leg_SelectionFailure():
    # F5: FR-002 (spec line 149) requires primary_failure to carry FOUR fields. The last
    # two live on the primary leg's SelectionFailure (route.py:236-240) — join, don't
    # duplicate, so the two records can never disagree.
    events = [_selfail(_R_PRIMARY), _rerouted(), _chain(_R_FALLBACK), _done(_R_FALLBACK)]
    ii = _build(events, route_id=_R_FALLBACK)
    assert ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == REROUTE_PRIMARY_PROFILE
    assert ii.degradation.fallback_profile == REROUTE_FALLBACK_PROFILE
    assert ii.degradation.relaxed_constraints == REROUTE_RELAXED_CONSTRAINTS
    pf = ii.degradation.primary_failure
    assert pf["exception_type"] == REROUTE_TRIGGER
    assert pf["message"] == "none live"
    assert pf["requirement_digest"] == "rq-1"          # from the SelectionFailure
    assert pf["snapshot_provenance"] == _PROV_JSON     # from the SelectionFailure


def test_a_reroute_without_its_primary_SelectionFailure_fails_closed():
    # An unjoinable degradation record cannot describe WHY the primary failed; emitting a
    # partial identity would be provenance that looks authoritative but isn't.
    with pytest.raises(InvocationIdentityError, match="SelectionFailure"):
        _build([_rerouted(), _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_whose_primary_failed_for_another_reason_fails_closed():
    with pytest.raises(InvocationIdentityError, match="ModelUnavailable"):
        _build([_selfail(_R_PRIMARY, exception_type="ChainExhausted"), _rerouted(),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_whose_failure_message_diverges_fails_closed():
    # F4: exception_type + message exist on BOTH records. Two sources for one fact can
    # disagree; a silent disagreement is exactly the provenance drift the join removes.
    with pytest.raises(InvocationIdentityError, match="divergent degradation provenance"):
        _build([_selfail(_R_PRIMARY, message="no independent family"),
                _rerouted(message="something else entirely"),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_a_reroute_from_ANOTHER_attempt_cannot_mark_this_route_degraded():
    # F3: ReviewRerouted keys on fallback_route_id, not route_id, so the scoped Attempt
    # check never saw it. A foreign reroute must not classify this route.
    foreign = _corrupt(_rerouted(), attempt_id="A2")
    with pytest.raises(InvocationIdentityError, match="attempt"):
        _build([_selfail(_R_PRIMARY), foreign, _chain(_R_FALLBACK), _done(_R_FALLBACK)],
               route_id=_R_FALLBACK)


def test_a_reroute_borrowing_a_foreign_primary_leg_fails_closed():
    # Both legs must be THIS Attempt's own claims for the named operation.
    borrowed_primary = derive_route_id("A2", _OP, "primary")
    borrowed = _corrupt(_rerouted(), payload={**_rerouted().payload,
                                              "primary_route_id": borrowed_primary})
    with pytest.raises(InvocationIdentityError, match="primary_route_id"):
        _build([_selfail(borrowed_primary), borrowed,
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_the_WRITER_already_refuses_both_of_those_corruptions():
    # The two tests above bypass validation on purpose. This one proves WHY that was
    # necessary: `_validate_review_rerouted` recomputes both legs from the envelope
    # attempt_id, so neither record can be persisted in the first place. The reader's
    # checks are defense-in-depth at a trust boundary, not the only guard.
    foreign = _corrupt(_rerouted(), attempt_id="A2")
    borrowed = _corrupt(_rerouted(), payload={**_rerouted().payload,
                                              "primary_route_id": derive_route_id(
                                                  "A2", _OP, "primary")})
    for bad in (foreign, borrowed):
        with pytest.raises(ValueError, match="ReviewRerouted payload invalid"):
            validate_lane_event(json.loads(event_to_json(bad)))


def test_a_selection_failure_alone_does_not_imply_degradation():
    # F10: no inference from an event PATTERN — without an explicit ReviewRerouted record
    # naming this route as the fallback leg, the outcome is a plain success.
    ii = _build([_selfail("R"), _chain("R"), _done("R")])
    assert ii.route_outcome == "success" and ii.degradation is None


def test_no_dispatch_yields_no_identity():
    assert _build([_chain("R")]) is None


def test_no_chain_resolved_yields_no_identity():
    assert _build([_done("R")]) is None


def test_events_for_another_route_are_ignored():
    ii = _build([_chain("R"), _done("R"), _chain("OTHER", eid="c2"), _done("OTHER", eid="d2")])
    assert ii is not None and ii.actor_instance_id == "R"


# ---- F8: uniqueness + Attempt binding ----


def test_duplicate_chain_resolved_is_corruption():
    # next() would silently take the first. route.py:393 emits exactly ONE per route_chat.
    with pytest.raises(InvocationIdentityError, match="ChainResolved"):
        _build([_chain("R"), _chain("R", eid="c2"), _done("R")])


def test_duplicate_dispatch_completed_is_corruption():
    with pytest.raises(InvocationIdentityError, match="DispatchCompleted"):
        _build([_chain("R"), _done("R"), _done("R", eid="d2")])


def test_two_reroutes_naming_the_same_fallback_is_corruption():
    with pytest.raises(InvocationIdentityError, match="ReviewRerouted"):
        _build([_selfail(_R_PRIMARY), _rerouted(), _rerouted(eid="rr2"),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_two_selection_failures_for_the_primary_leg_is_corruption():
    with pytest.raises(InvocationIdentityError, match="SelectionFailure"):
        _build([_selfail(_R_PRIMARY), _selfail(_R_PRIMARY, eid="s2"), _rerouted(),
                _chain(_R_FALLBACK), _done(_R_FALLBACK)], route_id=_R_FALLBACK)


def test_an_event_from_another_attempt_fails_closed():
    with pytest.raises(InvocationIdentityError, match="attempt"):
        _build([_chain("R"), _done("R", eid="d2", attempt="A2")])


# ---- F4: the completed candidate must come from the RESOLVED chain ----


def _done_at(route_id, *, index, model=None, eid="d"):
    return _ev("DispatchCompleted", _audit_payload(DispatchCompleted(
        route_id=route_id, candidate_index=index, candidate=model or _MODEL,
        reservation_id=None,
    )), eid)


def test_an_out_of_range_candidate_index_is_corruption():
    with pytest.raises(InvocationIdentityError, match="not a valid position"):
        _build([_chain("R"), _done_at("R", index=7)])


def test_a_candidate_the_chain_never_held_is_corruption():
    # The security-relevant case: `family` from this record becomes the independence
    # provenance FR-002 is judged on, and `_baseline_for` derives a whole review's family
    # exclusion from it. Attributing execution to a model selection never chose would let
    # a same-family reviewer pass as independent.
    other = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="gpt-oss-120b",
                     model_family="gpt-oss", vendor="openai")
    with pytest.raises(InvocationIdentityError, match="the chain it resolved holds"):
        _build([_chain("R"), _done_at("R", index=0, model=other)])


def test_a_matching_candidate_at_a_valid_index_is_accepted():
    ii = _build([_chain("R"), _done_at("R", index=0)])
    assert ii is not None and ii.family == "gemma"


def test_a_boolean_index_is_not_treated_as_an_integer_position():
    # `True == 1` in Python, so a bool would silently index the chain. It is not a
    # candidate position and must be refused like any other malformed value.
    ev = _ev("DispatchCompleted", {**_audit_payload(DispatchCompleted(
        route_id="R", candidate_index=0, candidate=_MODEL, reservation_id=None,
    )), "candidate_index": True}, "d")
    with pytest.raises(InvocationIdentityError, match="not a valid position"):
        _build([_chain("R"), ev])


def test_paid_reservation_opened_payload_is_unchanged_by_the_funded_usd_field():
    """A paid ``ReservationOpened`` (``reserved_usd`` None) serializes exactly as it did
    before the field existed, so replaying a route recorded earlier is not a conflicting
    payload; a funded one carries its USD hold."""
    from llmxive.model_selection.attempt_hooks import ReservationOpened

    paid = ReservationOpened("r1", 0, _MODEL, "rid-1", 12.5)
    before_the_field = {
        "route_id": "r1", "candidate_index": 0,
        "candidate": {"backend": _MODEL.backend, "serving_endpoint": _MODEL.serving_endpoint,
                      "model_id": _MODEL.model_id, "model_family": _MODEL.model_family,
                      "vendor": _MODEL.vendor},
        "reservation_id": "rid-1", "reserved_credits": 12.5, "audit_event_id": paid.event_id,
    }
    assert _audit_payload(paid) == before_the_field and "reserved_usd" not in _audit_payload(paid)
    assert json.dumps(_audit_payload(paid), sort_keys=True) == json.dumps(before_the_field, sort_keys=True)
    funded = ReservationOpened("r1", 0, _MODEL, "rid-1", 1.8, reserved_usd=0.0018)
    assert _audit_payload(funded)["reserved_usd"] == 0.0018
