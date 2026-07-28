"""The lane event record + its fail-closed validation (spec 025 slice 1A, Task 2)."""

from __future__ import annotations

import pytest

from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    SCHEMA_VERSION,
    Event,
    derive_event_id,
    derive_route_id,
    event_from_json,
    event_to_json,
    validate_lane_event,
)


def _raw(**kw):
    # a valid problem-stream event at revision 0 (seq=0, expected=0, resulting=1)
    base = {
        "event_id": "e1", "event_type": "ProblemDiscovered", "problem_id": "prob-1",
        "actor": "disc", "payload": {}, "timestamp": "2026-07-24T00:00:00+00:00",
        "schema_version": SCHEMA_VERSION, "attempt_id": None,
        "expected_problem_revision": 0, "resulting_problem_revision": 1, "seq": 0,
    }
    base.update(kw)
    return base


# ---- envelope ----


def test_valid_event_passes():
    validate_lane_event(_raw())  # no raise


def test_event_id_deterministic_and_scoped():
    a = derive_event_id("prob-1", "discover")
    assert a == derive_event_id("prob-1", "discover") != derive_event_id("prob-2", "discover")


def test_round_trip_carries_all_revision_anchors():
    e = event_from_json(event_to_json(Event(**_raw())))
    assert e.seq == 0 and e.expected_problem_revision == 0 and e.resulting_problem_revision == 1


def test_validate_rejects_unknown_type():
    with pytest.raises(ValueError, match="event_type"):
        validate_lane_event(_raw(event_type="TotallyMadeUp"))


def test_validate_rejects_both_revision_scopes():
    with pytest.raises(ValueError, match="must NOT set"):
        validate_lane_event(_raw(expected_lane_revision=0, resulting_lane_revision=1))


def test_validate_rejects_wrong_scope_for_coordinator():
    # a coordinator event must carry the LANE revision scope, not the problem scope
    with pytest.raises(ValueError, match="lane-stream event must set"):
        validate_lane_event(_raw(problem_id=COORDINATOR_STREAM))


def test_validate_accepts_a_supported_prior_schema_version_note():
    # SUPPORTED_SCHEMA_VERSIONS (not `== SCHEMA_VERSION`) is what makes append-only
    # history readable across future bumps; today it is frozenset({1}).
    from llmxive.self_improvement.events import SUPPORTED_SCHEMA_VERSIONS

    assert SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS


def test_validate_rejects_off_by_one_resulting_revision():
    with pytest.raises(ValueError, match="resulting==seq"):
        validate_lane_event(_raw(resulting_problem_revision=5))  # must be seq+1 == 1


def test_validate_rejects_bad_schema_version():
    with pytest.raises(ValueError, match="schema_version"):
        validate_lane_event(_raw(schema_version=999))


# ---- envelope TYPES (not just presence) ----


def _coord(**kw):
    """The same event on the COORDINATOR stream, which uses the lane revision scope.
    ``ClaimAcquired`` has a payload schema (the fold reads both ids), so the base event
    carries a well-formed one — the envelope cases below are what these vary."""
    base = _raw(problem_id=COORDINATOR_STREAM, event_type="ClaimAcquired", attempt_id="A1",
                payload={"problem_id": "P1", "attempt_id": "A1"},
                expected_problem_revision=None, resulting_problem_revision=None,
                expected_lane_revision=0, resulting_lane_revision=1)
    base.update(kw)
    return base


@pytest.mark.parametrize("stream", ["problem", "coordinator"])
@pytest.mark.parametrize("bad, why", [
    ({"problem_id": ""}, "problem_id"),          # names no stream
    ({"actor": ""}, "actor"),                    # attributes provenance to nobody
    ({"event_id": ""}, "event_id"),
    ({"actor": 123}, "actor"),
    ({"schema_version": True}, "schema_version"),  # True == 1, and hashes as 1
    ({"attempt_id": 123}, "attempt_id"),           # contaminates attribution
    ({"attempt_id": ""}, "attempt_id"),
    ({"timestamp": "2026-07-24"}, "instant"),      # a date is not an instant
    ({"timestamp": "2026-07-24T00:00:00"}, "instant"),  # naive: no timezone
    ({"timestamp": 20260724}, "timestamp"),
])
def test_envelope_rejects_malformed_values(stream, bad, why):
    # Presence alone is not a schema: every field here lands in IMMUTABLE history that
    # later readers must trust (issue #1242), so each is checked for the type it needs.
    make = _raw if stream == "problem" else _coord
    with pytest.raises(ValueError, match=why):
        validate_lane_event(make(**bad))


@pytest.mark.parametrize("stream", ["problem", "coordinator"])
def test_envelope_rejects_boolean_and_negative_sequence_fields(stream):
    # seq is the lane's ORDERING authority. `True == 1` sails through every arithmetic
    # check and then orders the projection as position 1 — a corruption of the sequence
    # itself, not a cosmetic type issue.
    make = _raw if stream == "problem" else _coord
    field = "problem" if stream == "problem" else "lane"
    with pytest.raises(ValueError, match="seq"):
        validate_lane_event(make(**{"seq": True,
                                    f"expected_{field}_revision": True,
                                    f"resulting_{field}_revision": 2}))
    with pytest.raises(ValueError, match="seq"):
        validate_lane_event(make(**{"seq": -1,
                                    f"expected_{field}_revision": -1,
                                    f"resulting_{field}_revision": 0}))
    with pytest.raises(ValueError, match="revision"):
        validate_lane_event(make(**{"seq": 0,
                                    f"expected_{field}_revision": False,
                                    f"resulting_{field}_revision": 1}))


@pytest.mark.parametrize("stream", ["problem", "coordinator"])
def test_a_well_formed_event_on_either_stream_still_passes(stream):
    validate_lane_event(_raw() if stream == "problem" else _coord())


def test_a_timezone_aware_timestamp_is_accepted_in_several_forms():
    for ts in ("2026-07-24T00:00:00+00:00", "2026-07-24T12:30:05.123456+02:00",
               "2026-07-24T00:00:00Z"):
        validate_lane_event(_raw(timestamp=ts))


# ---- per-type payload validation ----


def _claim_payload(**kw):
    base = {
        "attempt_id": "A1", "operation_id": "op-1", "leg": "primary",
        "route_id": derive_route_id("A1", "op-1", "primary"), "call_ceiling": 56,
    }
    base.update(kw)
    return base


def _claim_event(**kw):
    return _raw(event_type="LaneCallClaimed", attempt_id="A1", payload=_claim_payload(**kw))


def test_lane_call_claimed_payload_validates():
    validate_lane_event(_claim_event())


@pytest.mark.parametrize("bad", [
    {"route_id": None},        # missing
    {"route_id": ""},          # empty
    {"route_id": "r" * 32},    # well-formed but NOT derived from this (attempt, op, leg)
    {"leg": "tertiary"},       # not one of LEGS
    {"call_ceiling": 0},       # non-positive
    {"call_ceiling": "56"},    # wrong type
    {"call_ceiling": True},    # bool is an int in Python — must still be rejected
])
def test_lane_call_claimed_payload_rejects_malformed(bad):
    # The ENVELOPE alone would accept every one of these; the projection would then
    # KeyError (or route on a bogus id) long after the event became durable.
    payload = _claim_payload(**bad)
    for k, v in bad.items():
        if v is None:
            payload.pop(k)     # also cover the MISSING-key case
    with pytest.raises(ValueError, match="LaneCallClaimed payload invalid"):
        validate_lane_event(_raw(event_type="LaneCallClaimed", attempt_id="A1", payload=payload))


def test_a_claim_whose_payload_attempt_disagrees_with_the_envelope_is_rejected():
    # project_call_claims filters by the PAYLOAD's attempt_id. If the envelope says
    # something else, the claim is counted against one Attempt while the event records
    # another — a silent misattribution of a safety limit.
    with pytest.raises(ValueError, match="disagrees with the event"):
        validate_lane_event(
            _raw(event_type="LaneCallClaimed", attempt_id="A2", payload=_claim_payload())
        )


def test_attempt_configured_validates_and_rejects_malformed():
    ok = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": 50.0}
    validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=ok))
    for bad in ({**ok, "call_ceiling": 0}, {**ok, "attempt_budget_credits": -1.0}):
        with pytest.raises(ValueError, match="AttemptConfigured payload invalid"):
            validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=bad))


def test_the_new_safety_events_reject_unknown_keys():
    # AttemptConfigured binds MONEY and a call cap; LaneCallClaimed binds routing
    # identity. Both get the same exact-schema rule — an unrecognized key is
    # indistinguishable from a typo, and once it is in append-only history readers must
    # guess at semantics nobody defined.
    with pytest.raises(ValueError, match="unexpected LaneCallClaimed payload keys"):
        validate_lane_event(_claim_event(surprise="extra"))
    cfg = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": 50.0,
           "surprise": "extra"}
    with pytest.raises(ValueError, match="unexpected AttemptConfigured payload keys"):
        validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=cfg))


@pytest.mark.parametrize("budget", [float("nan"), float("inf"), True])
def test_attempt_configured_rejects_a_non_finite_budget(budget):
    # A hand-written or corrupted record must not be able to install an unbounded cap.
    payload = {"attempt_id": "A1", "call_ceiling": 56, "attempt_budget_credits": budget}
    with pytest.raises(ValueError, match="AttemptConfigured payload invalid"):
        validate_lane_event(_raw(event_type="AttemptConfigured", attempt_id="A1", payload=payload))


@pytest.mark.parametrize("credits, why", [
    (-1.0, "> 0"),               # REOPENS spent budget: counting_total goes DOWN
    (0.0, "> 0"),                # a paid dispatch the Attempt cap can never bind
    (float("nan"), "FINITE"),    # every later comparison is False -> always admit
    (float("inf"), "FINITE"),
    (True, "not a bool"),
])
def test_attempt_credit_reserved_rejects_unsafe_amounts(credits, why):
    # project_reservations SUMS reserved_credits into counting_total, which IS the
    # number the Attempt cap compares against. A bad amount here is a money defect, so
    # the event must not rest on trusted construction.
    payload = {"reservation_id": "r1", "call_id": "c1", "reserved_credits": credits}
    with pytest.raises(ValueError, match=why):
        validate_lane_event(
            _raw(event_type="AttemptCreditReserved", attempt_id="A1", payload=payload)
        )


def test_attempt_credit_reserved_requires_an_envelope_attempt_and_exact_keys():
    ok = {"reservation_id": "r1", "call_id": "c1", "reserved_credits": 2.5}
    validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id="A1", payload=ok))
    with pytest.raises(ValueError, match="envelope attempt_id"):
        validate_lane_event(_raw(event_type="AttemptCreditReserved", attempt_id=None, payload=ok))
    with pytest.raises(ValueError, match="unexpected AttemptCreditReserved payload keys"):
        validate_lane_event(
            _raw(event_type="AttemptCreditReserved", attempt_id="A1",
                 payload={**ok, "surprise": 1})
        )


def test_the_canonical_serializer_refuses_non_finite_numbers():
    # json.dumps emits bare `NaN`/`Infinity` by default — valid to Python, invalid JSON
    # to everyone else. The ref must never carry it.
    ev = Event(**_raw(payload={"credits": float("nan")}))
    with pytest.raises(ValueError, match="not JSON compliant"):
        event_to_json(ev)


@pytest.mark.parametrize("event_type", ["AttemptCreditRetained", "AttemptCreditReleased",
                                        "AttemptCreditReconciled"])
def test_a_reservation_transition_names_its_reservation_and_attempt(event_type):
    validate_lane_event(
        _raw(event_type=event_type, attempt_id="A1", payload={"reservation_id": "r1"})
    )


@pytest.mark.parametrize("event_type", ["AttemptCreditRetained", "AttemptCreditReleased",
                                        "AttemptCreditReconciled"])
@pytest.mark.parametrize("attempt_id, payload, why", [
    ("A1", {}, "reservation_id"),                          # names no reservation
    ("A1", {"reservation_id": ""}, "reservation_id"),
    ("A1", {"reservation_id": 7}, "reservation_id"),
    (None, {"reservation_id": "r1"}, "envelope attempt_id"),  # the projection filters on it
    ("A1", {"reservation_id": "r1", "note": "x"}, "unexpected"),
])
def test_a_malformed_reservation_transition_is_rejected(event_type, attempt_id, payload, why):
    # project_reservations filters by the envelope attempt_id and keys on reservation_id.
    # An event missing either is skipped rather than applied — so a Released that vanished
    # would leave its credits counting against the Attempt's budget forever.
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_raw(event_type=event_type, attempt_id=attempt_id, payload=payload))


# ---- the coordinator stream's payload schemas ----


def _coord_event(event_type, payload, *, attempt_id="A1"):
    return _raw(problem_id=COORDINATOR_STREAM, event_type=event_type, payload=payload,
                attempt_id=attempt_id, expected_problem_revision=None,
                resulting_problem_revision=None,
                expected_lane_revision=0, resulting_lane_revision=1)


@pytest.mark.parametrize("event_type", ["ClaimAcquired", "ClaimReleased"])
def test_a_claim_records_both_ownership_ids(event_type):
    validate_lane_event(_coord_event(event_type, {"problem_id": "P1", "attempt_id": "A1"}))


@pytest.mark.parametrize("event_type", ["ClaimAcquired", "ClaimReleased"])
@pytest.mark.parametrize("payload, why", [
    ({"attempt_id": "A1"}, "problem_id"),                      # the fold would KeyError
    ({"problem_id": "P1"}, "attempt_id"),
    ({"problem_id": "", "attempt_id": "A1"}, "problem_id"),    # empty compares equal to nothing
    ({"problem_id": "P1", "attempt_id": ""}, "attempt_id"),
    ({"problem_id": "P1", "attempt_id": "A2"}, "disagrees"),   # envelope says A1
    ({"problem_id": "P1", "attempt_id": "A1", "extra": 1}, "unexpected"),
])
def test_a_malformed_claim_is_rejected_at_the_write_boundary(event_type, payload, why):
    # These ids ARE the lane's ownership record: project_coordinator decides who holds the
    # singleton from them, and cas_release compares them to refuse a stale release. A
    # missing one would explode inside the fold once the event is already durable.
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_coord_event(event_type, payload))


def test_monitor_started_binds_one_attempt():
    validate_lane_event(_coord_event("MonitorStarted", {"attempt_id": "A1"}))
    with pytest.raises(ValueError, match="disagrees"):
        validate_lane_event(_coord_event("MonitorStarted", {"attempt_id": "A9"}))
    with pytest.raises(ValueError, match="unexpected"):
        validate_lane_event(_coord_event("MonitorStarted", {"attempt_id": "A1", "when": "now"}))


def test_promotion_enabled_must_be_an_actual_bool():
    # bool("false") is True. Coercing here would ENABLE autonomous promotion from a record
    # written to disable it — so the type is required, not inferred.
    validate_lane_event(
        _coord_event("PromotionEnabledSet", {"promotion_enabled": False, "policy_version": 2},
                     attempt_id=None)
    )
    for bad in ("false", 0, 1, None):
        with pytest.raises(ValueError, match="promotion_enabled"):
            validate_lane_event(
                _coord_event("PromotionEnabledSet", {"promotion_enabled": bad}, attempt_id=None)
            )


def test_policy_version_is_optional_but_typed():
    # A flip that does not change policy carries the previous version forward.
    validate_lane_event(
        _coord_event("PromotionEnabledSet", {"promotion_enabled": True}, attempt_id=None)
    )
    for bad in (-1, True, "3"):
        with pytest.raises(ValueError, match="policy_version"):
            validate_lane_event(
                _coord_event("PromotionEnabledSet",
                             {"promotion_enabled": True, "policy_version": bad}, attempt_id=None)
            )


# ---- Slice 1B: the FR-002 degradation record ----

_OP = "op-1"


def _reroute_payload(**kw):
    base = {
        "operation_id": _OP, "lens": "worthwhile-improvement",
        "primary_profile": "independent_review", "fallback_profile": "deep_review",
        "primary_route_id": derive_route_id("A1", _OP, "primary"),
        "fallback_route_id": derive_route_id("A1", _OP, "fallback"),
        "primary_failure": {"exception_type": "ModelUnavailable",
                            "message": "no independent family live"},
        "relaxed_constraints": ["family_independence", "snapshot_freshness"],
    }
    base.update(kw)
    return base


def _reroute_event(**kw):
    return _raw(event_type="ReviewRerouted", attempt_id="A1", payload=_reroute_payload(**kw))


def test_review_rerouted_is_a_known_event_type():
    # A VOCABULARY extension, so SCHEMA_VERSION must NOT change — bumping it would make a
    # reader reject every prior-version record in the append-only history.
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1

    assert "ReviewRerouted" in KNOWN_EVENT_TYPES_V1
    assert SCHEMA_VERSION == 1


def test_review_rerouted_event_validates():
    validate_lane_event(_reroute_event())


def test_review_rerouted_is_registered_for_payload_validation():
    # Vocabulary membership alone leaves the payload unchecked.
    from llmxive.self_improvement.events import TYPE_VALIDATORS

    assert "ReviewRerouted" in TYPE_VALIDATORS


def test_review_rerouted_route_ids_are_recomputed_at_write_time():
    # The same binding the identity projection checks at read time, enforced at WRITE time,
    # so a foreign or borrowed leg never becomes durable in the first place.
    foreign = derive_route_id("A2", _OP, "primary")
    with pytest.raises(ValueError, match="primary_route_id"):
        validate_lane_event(_reroute_event(primary_route_id=foreign))
    with pytest.raises(ValueError, match="attempt_id"):
        validate_lane_event(_raw(event_type="ReviewRerouted", attempt_id=None,
                                 payload=_reroute_payload()))


def test_review_rerouted_rejects_unknown_keys():
    # The schema is EXACT, not merely "required fields present" — otherwise a typo'd key is
    # indistinguishable from a new one and the contract is untestable.
    with pytest.raises(ValueError, match="unexpected ReviewRerouted payload keys"):
        validate_lane_event(_reroute_event(surprise="extra"))
    with pytest.raises(ValueError, match="unexpected ReviewRerouted primary_failure keys"):
        validate_lane_event(_reroute_event(
            primary_failure={"exception_type": "ModelUnavailable", "message": "x", "extra": 1}))


@pytest.mark.parametrize("bad, why", [
    # both legs the same id: caught by the write-time derivation check (two identical ids
    # cannot both be correct derivations), with the distinctness guard behind it
    ({"primary_route_id": "same", "fallback_route_id": "same"}, "route_id"),
    ({"primary_profile": "deep_review"}, "primary_profile"),
    ({"fallback_profile": "standard_generation"}, "fallback_profile"),
    ({"primary_failure": {"exception_type": "ChainExhausted", "message": "x"}},
     "ModelUnavailable"),
    ({"primary_failure": {"message": "x"}}, "exception_type"),
    ({"relaxed_constraints": ["family_independence"]}, "relaxed_constraints"),
    ({"relaxed_constraints": ["snapshot_freshness", "family_independence"]},
     "relaxed_constraints"),
    ({"lens": ""}, "lens"),
])
def test_review_rerouted_rejects_malformed_payloads(bad, why):
    # Each of these would otherwise land durably and then either KeyError inside the
    # identity projection or assert a FALSE claim about what the fallback relaxed.
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_reroute_event(**bad))


def test_review_rerouted_rejects_a_missing_key():
    payload = _reroute_payload()
    del payload["fallback_route_id"]
    with pytest.raises(ValueError, match="fallback_route_id"):
        validate_lane_event(_raw(event_type="ReviewRerouted", attempt_id="A1", payload=payload))


def test_a_reroute_for_a_different_operation_cannot_borrow_these_legs():
    # operation_id is part of the derivation, so a record that renames the operation while
    # keeping the route ids is refused — the ids ARE the claim about which call ran.
    with pytest.raises(ValueError, match="route_id"):
        validate_lane_event(_reroute_event(operation_id="some-other-operation"))


def test_types_without_a_validator_are_envelope_only():
    # By design: the audit-mirror types re-serialize already-typed slice-0 dataclasses.
    from llmxive.self_improvement.events import TYPE_VALIDATORS

    assert "ChainResolved" not in TYPE_VALIDATORS
    validate_lane_event(_raw(event_type="ChainResolved", payload={"anything": 1}))
