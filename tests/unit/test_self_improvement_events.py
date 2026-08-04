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
                payload={"problem_id": "P1", "attempt_id": "A1", **CLAIM_PAIR_TERMS},
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


#: The generation + terms a claim's TWO halves share. `ClaimAcquired` carries them (it is
#: half of the claim); `ClaimReleased` must NOT — one owner for the number — so the two are
#: no longer schema-identical and the shared cases below add them per type.
CLAIM_PAIR_TERMS = {"claim_generation": 1, "lane_revision": 0, "claim_expiry_s": 13200,
                    "max_claim_hold_time_s": 13200, "max_clock_skew_s": 300,
                    "policy_version": 1}
_CLAIM_EXTRA = {"ClaimAcquired": CLAIM_PAIR_TERMS, "ClaimReleased": {}}


@pytest.mark.parametrize("event_type", ["ClaimAcquired", "ClaimReleased"])
def test_a_claim_records_both_ownership_ids(event_type):
    validate_lane_event(_coord_event(event_type, {
        "problem_id": "P1", "attempt_id": "A1", **_CLAIM_EXTRA[event_type]}))


def test_a_release_may_not_restate_the_claims_generation_or_terms():
    """The asymmetry, pinned. A release that carried its own copy could disagree with the
    claim it releases, and then two records would answer "under what terms" differently."""
    with pytest.raises(ValueError, match="unexpected"):
        validate_lane_event(_coord_event("ClaimReleased", {
            "problem_id": "P1", "attempt_id": "A1", **CLAIM_PAIR_TERMS}))


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
    payload = {**payload, **_CLAIM_EXTRA[event_type]}
    # These ids ARE the lane's ownership record: project_coordinator decides who holds the
    # singleton from them, and cas_release compares them to refuse a stale release. A
    # missing one would explode inside the fold once the event is already durable.
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_coord_event(event_type, payload))


_MERGED_AT = "2026-07-31T12:00:00+00:00"


def _monitor(**over):
    payload = {"problem_id": "P1", "attempt_id": "A1", "merged_at": _MERGED_AT, **over}
    return _coord_event("MonitorStarted", payload)


def test_monitor_started_binds_one_attempt():
    validate_lane_event(_monitor())
    with pytest.raises(ValueError, match="disagrees"):
        validate_lane_event(_monitor(attempt_id="A9"))
    with pytest.raises(ValueError, match="unexpected"):
        validate_lane_event(_monitor(when="now"))


@pytest.mark.parametrize("drop", ["problem_id", "merged_at"])
def test_monitor_started_requires_the_fields_the_COORDINATOR_will_need(drop):
    """Both are REQUIRED, not optional (spec rev 24). `merged_at` is what
    `last_autonomous_merge_at` folds to, and `problem_id` is what lets the ownership check
    compare the PAIR rather than an `attempt_id` alone (the 1A F6 mistake). MonitorStarted
    has exactly one producer and it always knows both, so an optional field would exist
    solely so a record could be written without the value the coordinator then needs."""
    payload = {"problem_id": "P1", "attempt_id": "A1", "merged_at": _MERGED_AT}
    del payload[drop]
    with pytest.raises(ValueError, match=drop):
        validate_lane_event(_coord_event("MonitorStarted", payload))


@pytest.mark.parametrize("bad", ["2026-07-31", "not-a-time", "2026-07-31T12:00:00"])
def test_monitor_started_merged_at_is_an_INSTANT_not_a_date(bad):
    """A bare date parses fine and would order merges from different runners by an offset
    nobody wrote down — the same requirement the envelope timestamp has, and the reason
    both go through one `_instant`."""
    with pytest.raises(ValueError, match="merged_at"):
        validate_lane_event(_monitor(merged_at=bad))


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


# ---- Slice 2: the Attempt lifecycle vocabulary ----


def _attempt(event_type, payload=None, *, problem_id="prob-1", attempt_id="A1", **over):
    """A Problem-stream Attempt event: the identity pair in the payload, matching the
    envelope, plus whatever the type adds."""
    body = {"problem_id": problem_id, "attempt_id": attempt_id, **(payload or {})}
    return _raw(event_type=event_type, problem_id=problem_id, attempt_id=attempt_id,
                payload=body, **over)


def test_every_declared_transition_has_a_writable_event_type():
    """`lifecycle` DECLARES the machine; `events` decides what the store will accept. If the
    two drift, a transition the table says is legal is refused at the write boundary — so
    the drift is a failing test rather than a runtime surprise."""
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES

    missing = ATTEMPT_EVENT_TYPES - KNOWN_EVENT_TYPES_V1
    assert not missing, f"transitions the store would refuse to write: {sorted(missing)}"


def test_every_attempt_event_type_has_a_payload_validator():
    """Envelope-only is a deliberate choice for the audit-mirror types, which re-serialize
    already-typed dataclasses. It is NEVER right for an Attempt event: `walk_attempt` reads
    these payloads, and an unchecked one lands durably and then makes the fold raise."""
    from llmxive.self_improvement.events import TYPE_VALIDATORS
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES

    assert not (ATTEMPT_EVENT_TYPES - set(TYPE_VALIDATORS))


def test_no_event_type_lives_on_both_streams():
    """`ClaimGranted`/`ClaimExpired` (Attempt) and `ClaimAcquired`/`ClaimReleased`
    (coordinator) describe the same moments from two sides and are NOT duplicates. Keeping
    the vocabularies disjoint is what makes "which stream is this?" answerable from the
    event type alone — and rev 22's coordinator-side `ClaimExpired` is the temptation this
    pins shut."""
    from llmxive.self_improvement.coordinator import _COORDINATOR_TYPES
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES

    assert not (ATTEMPT_EVENT_TYPES & _COORDINATOR_TYPES)


def test_side_effect_intents_are_not_attempt_transitions():
    """`PromotionRequested` (a TRANSITION) and `SideEffectRequested{effect:"merge"}` (the
    saga's fencing record) are different layers, and the machine must not confuse them: the
    transition moves the Attempt, the intent is what blocks a reclaim until reconciled."""
    from llmxive.self_improvement.lifecycle import ATTEMPT_EVENT_TYPES

    assert "SideEffectRequested" not in ATTEMPT_EVENT_TYPES
    assert "SideEffectObserved" not in ATTEMPT_EVENT_TYPES
    assert "PromotionRequested" in ATTEMPT_EVENT_TYPES


@pytest.mark.parametrize("event_type", ["Implementing", "EvaluationPassed", "Retained"])
def test_a_plain_transition_binds_its_problem_and_its_attempt(event_type):
    validate_lane_event(_attempt(event_type))
    # A transition may carry per-transition fields (a head_sha, a reason); the schema is
    # required-fields, not exact, because those are declared by the task that writes them.
    validate_lane_event(_attempt(event_type, {"head_sha": "abc123"}))


@pytest.mark.parametrize("payload, envelope, why", [
    ({"attempt_id": "A1"}, {}, "problem_id"),
    ({"problem_id": "prob-1"}, {}, "attempt_id"),
    ({"problem_id": "prob-2", "attempt_id": "A1"}, {}, "disagrees"),
    ({"problem_id": "prob-1", "attempt_id": "A2"}, {}, "disagrees"),
])
def test_a_transition_filed_against_the_WRONG_timeline_is_refused(payload, envelope, why):
    """The ids decide which timeline the record joins: `project_attempt` selects by the
    envelope `attempt_id`, and the cross-stream pairing walks compare `(problem_id,
    attempt_id)`. A disagreement files the event against the wrong Attempt — silently, and
    durably."""
    with pytest.raises(ValueError, match=why):
        validate_lane_event(_raw(event_type="Implementing", problem_id="prob-1",
                                 attempt_id="A1", payload=payload, **envelope))


def test_claim_granted_must_carry_the_generation_the_FOLD_reads():
    """`walk_attempt` reads `claim_generation` off every grant. Refusing a grant without one
    HERE is the difference between a rejected append and an Attempt whose every future
    projection raises on a record that is already durable."""
    validate_lane_event(_attempt("ClaimGranted", CLAIM_PAIR_TERMS))
    with pytest.raises(ValueError, match="claim_generation"):
        validate_lane_event(_attempt("ClaimGranted", {
            k: v for k, v in CLAIM_PAIR_TERMS.items() if k != "claim_generation"}))
    for bad in (0, -1, True, "1"):
        with pytest.raises(ValueError, match="claim_generation"):
            validate_lane_event(_attempt(
                "ClaimGranted", {**CLAIM_PAIR_TERMS, "claim_generation": bad}))


@pytest.mark.parametrize("term", sorted(CLAIM_PAIR_TERMS))
def test_a_grant_MISSING_any_claim_bound_term_is_refused(term):
    """The terms are not decoration: a reclaimer reads `claim_expiry_s` and
    `max_claim_hold_time_s` off the record to decide whether a LIVE holder may be evicted,
    and `max_clock_skew_s` to decide how far a disagreeing clock may move that decision. A
    grant missing one would send the reclaimer to live policy — which is exactly the
    retroactive expiry recording them on the claim exists to prevent."""
    with pytest.raises(ValueError, match=term):
        validate_lane_event(_attempt("ClaimGranted", {
            k: v for k, v in CLAIM_PAIR_TERMS.items() if k != term}))


def test_a_grant_and_its_coordinator_half_share_ONE_payload_schema():
    """One construction wrote both, and the auditor compares them field-for-field. A field
    one half may carry and the other may not is a disagreement that comparison would report
    as corruption."""
    body = {"problem_id": "P1", "attempt_id": "A1", **CLAIM_PAIR_TERMS}
    validate_lane_event(_attempt("ClaimGranted", CLAIM_PAIR_TERMS))
    validate_lane_event(_coord_event("ClaimAcquired", body))


def test_a_heartbeat_names_its_generation_and_its_tick():
    validate_lane_event(_attempt("ClaimHeartbeat", {"claim_generation": 1, "tick": 0}))
    with pytest.raises(ValueError, match="unexpected"):
        validate_lane_event(
            _attempt("ClaimHeartbeat", {"claim_generation": 1, "tick": 0, "extra": 1}))
    with pytest.raises(ValueError, match="tick"):
        validate_lane_event(_attempt("ClaimHeartbeat", {"claim_generation": 1, "tick": -1}))
    with pytest.raises(ValueError, match="tick"):
        validate_lane_event(_attempt("ClaimHeartbeat", {"claim_generation": 1}))


def test_the_FIRST_beat_of_a_claim_is_tick_zero():
    """`tick` is non-negative, not positive: a positive-int check would reject the first
    record of every claim's heartbeat series."""
    validate_lane_event(_attempt("ClaimHeartbeat", {"claim_generation": 1, "tick": 0}))


def test_claim_expired_names_the_generation_and_the_reason():
    validate_lane_event(
        _attempt("ClaimExpired", {"claim_generation": 2, "reason": "heartbeat_lapsed"}))
    validate_lane_event(
        _attempt("ClaimExpired", {"claim_generation": 2, "reason": "hold_time_exceeded"}))
    with pytest.raises(ValueError, match="reason"):
        validate_lane_event(
            _attempt("ClaimExpired", {"claim_generation": 2, "reason": "crashed"}))


def _aborted(**over):
    payload = {"stage": "proposal", "cause": "model_unavailable",
               "unresolved_dispatches": [], **over}
    return _attempt("ReviewAborted", payload)


def test_review_aborted_records_which_review_and_why():
    validate_lane_event(_aborted())
    validate_lane_event(_aborted(stage="patch", cause="wall_clock",
                                 unresolved_dispatches=["route-1", "route-2"]))


@pytest.mark.parametrize("field, bad", [
    ("stage", "review"),          # not one of {proposal, patch}
    ("stage", "Proposal"),        # case matters — a vocabulary, not a label
    ("cause", "wallclock"),       # the typo this vocabulary exists to catch
    ("cause", "rejected"),        # a VERDICT, not an operational cause
])
def test_review_aborted_vocabularies_are_closed(field, bad):
    """A free-form string here is how a typo becomes a silent new category: nothing rejects
    it, the counter that keys on the real value never sees it, and the record is durable
    and wrong forever."""
    with pytest.raises(ValueError, match=field):
        validate_lane_event(_aborted(**{field: bad}))


def test_unresolved_dispatches_is_a_LIST_never_a_bare_string():
    """`str` is iterable, so an element-wise check over `"route-1"` passes one character at
    a time and a single id silently records as seven."""
    with pytest.raises(ValueError, match="unresolved_dispatches"):
        validate_lane_event(_aborted(unresolved_dispatches="route-1"))
    with pytest.raises(ValueError, match=r"unresolved_dispatches'\[1\]"):
        validate_lane_event(_aborted(unresolved_dispatches=["route-1", ""]))


def _intent(event_type="SideEffectRequested", **over):
    payload = {"problem_id": "prob-1", "attempt_id": "A1", "claim_generation": 1,
               "effect": "merge", "idempotency_key": "k1", **over}
    return _raw(event_type=event_type, problem_id="prob-1", attempt_id=None, payload=payload)


def test_an_intent_and_its_observation_round_trip():
    validate_lane_event(_intent())
    validate_lane_event(_intent("SideEffectObserved", disposition="landed"))


@pytest.mark.parametrize("disposition", ["landed", "rejected", "contained", "ambiguous"])
def test_all_FOUR_dispositions_are_writable(disposition):
    """Four, not two. `contained` (may still land, but only where it is harmless) and
    `rejected` (landing is now impossible) are different facts, and collapsing them is the
    rev-22 error."""
    validate_lane_event(_intent("SideEffectObserved", disposition=disposition))


def test_an_observation_without_a_disposition_is_refused():
    with pytest.raises(ValueError, match="disposition"):
        validate_lane_event(_intent("SideEffectObserved"))


def test_an_intent_must_not_carry_a_disposition():
    with pytest.raises(ValueError, match="unexpected"):
        validate_lane_event(_intent(disposition="landed"))


def _cooldown(**over):
    payload = {"problem_id": "prob-1", "cause": "quality", "epoch": 0,
               "cooldown_until": "2026-08-30T00:00:00+00:00", **over}
    return _raw(event_type="Cooldown", problem_id="prob-1", attempt_id=None, payload=payload)


@pytest.mark.parametrize("event_type", ["SideEffectRequested", "SideEffectObserved", "Cooldown"])
def test_a_NON_TRANSITION_problem_event_may_not_carry_an_envelope_attempt_id(event_type):
    """`project_attempt` selects an Attempt's history by the ENVELOPE `attempt_id` and folds
    everything it finds, failing closed on any type outside `ATTEMPT_EVENT_TYPES`. So a
    record filed under an Attempt's envelope that is not one of its transitions would make
    every LATER projection of that Attempt raise — permanently, since history is
    append-only, and the Attempt could not even record its own terminal. The association
    still exists; it lives in the payload."""
    raw = (_cooldown() if event_type == "Cooldown"
           else _intent(event_type, **({"disposition": "landed"}
                                       if event_type == "SideEffectObserved" else {})))
    raw["attempt_id"] = "A1"
    with pytest.raises(ValueError, match="must not carry an envelope attempt_id"):
        validate_lane_event(raw)


def test_a_cooldown_names_its_cause_and_its_epoch():
    validate_lane_event(_cooldown())
    validate_lane_event(_cooldown(cause="operational", epoch=3))


def test_a_cooldown_epoch_starts_at_zero_and_is_never_negative():
    """The key is `(problem_id,"cooldown",cause,epoch)`. Without the epoch a Problem that
    cooled down once could never cool down again (the rev-18 defect), and the FIRST cooldown
    of a cause is epoch 0 — so non-negative, not positive."""
    validate_lane_event(_cooldown(epoch=0))
    with pytest.raises(ValueError, match="epoch"):
        validate_lane_event(_cooldown(epoch=-1))


def test_a_cooldown_until_is_an_instant():
    with pytest.raises(ValueError, match="cooldown_until"):
        validate_lane_event(_cooldown(cooldown_until="2026-08-30"))


def test_a_cooldown_cause_is_one_of_the_two_counters():
    with pytest.raises(ValueError, match="cause"):
        validate_lane_event(_cooldown(cause="tired"))


def test_monitor_ended_records_which_terminal_closed_the_window():
    validate_lane_event(
        _coord_event("MonitorEnded", {"problem_id": "P1", "attempt_id": "A1",
                                      "outcome": "retained"}))
    with pytest.raises(ValueError, match="outcome"):
        validate_lane_event(
            _coord_event("MonitorEnded", {"problem_id": "P1", "attempt_id": "A1",
                                          "outcome": "promoted"}))


# ---- the ONE coordinator-record keying ----


def test_a_coordinator_partner_id_is_COMPUTED_not_searched_for():
    """Given either half of a cross-stream transaction, the other half's id is a pure
    function of `(event_type, problem_id, attempt_id)` — which is what makes a partner
    locatable on replay and auditable after the fact."""
    from llmxive.self_improvement.events import coordinator_event_id

    a = coordinator_event_id("ClaimReleased", "P1", "A1")
    assert a == coordinator_event_id("ClaimReleased", "P1", "A1")
    assert a != coordinator_event_id("ClaimAcquired", "P1", "A1")
    assert a != coordinator_event_id("ClaimReleased", "P2", "A1")
    assert a != coordinator_event_id("ClaimReleased", "P1", "A2")


def test_a_type_with_no_declared_key_cannot_be_keyed_by_guesswork():
    """`PromotionEnabledSet` is a coordinator event but NOT a cross-stream partner — it is
    keyed by `(coordinator,"reenable")`, not by a Problem and an Attempt. Deriving an id for
    it here would invent a pairing that does not exist."""
    from llmxive.self_improvement.events import coordinator_event_id

    with pytest.raises(ValueError, match="not a cross-stream coordinator event"):
        coordinator_event_id("PromotionEnabledSet", "P1", "A1")


def test_the_builder_and_the_derivation_agree_by_construction():
    """One builder, one derivation. Two of them drifting on id derivation would mint
    duplicate records of a single decision — the half-state this slice exists to prevent."""
    from llmxive.self_improvement.events import (
        COORDINATOR_STREAM as CS,
    )
    from llmxive.self_improvement.events import (
        coord_event,
        coordinator_event_id,
    )

    event = coord_event("ClaimReleased", problem_id="P1", attempt_id="A1",
                        payload={"problem_id": "P1", "attempt_id": "A1"},
                        actor="a", timestamp="2026-07-31T12:00:00+00:00")
    assert event.event_id == coordinator_event_id("ClaimReleased", "P1", "A1")
    # The ENVELOPE names the stream this lands on; the PAYLOAD names the claimed Problem.
    assert event.problem_id == CS and event.payload["problem_id"] == "P1"
    # The store stamps the anchors inside the CAS — a value fixed here would be a guess
    # about a revision we have not won yet.
    assert event.seq is None and event.expected_lane_revision is None
