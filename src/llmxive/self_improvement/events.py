"""The lane's append-only event record (FR-011) + fail-closed validation + its
deterministic idempotency key (FR-009).

Ordering is by the store-assigned ``seq`` (never timestamps): a projection that
sorted by wall clock could place a ``Retained`` before the ``Reserved`` it
follows. ``validate_lane_event`` rejects any event that could corrupt a
projection, at BOTH the write boundary and every read.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

COORDINATOR_STREAM = "coordinator"
SCHEMA_VERSION = 1  # the version NEW events are written with
#: Versions a reader accepts: append-only history means older events of a PRIOR
#: version stay readable forever, so a reader NEVER rejects on `!= SCHEMA_VERSION`.
#: Adding an event TYPE (same record shape) extends `KNOWN_EVENT_TYPES_V1` WITHOUT a
#: version bump; only a change to the record SHAPE bumps `SCHEMA_VERSION` and adds the
#: new version here with its own validator/projection support (so v1 events keep
#: validating under their own rules).
SUPPORTED_SCHEMA_VERSIONS = frozenset({1})
SEQ_FIELD = "seq"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")

# The event vocabulary THIS schema version understands. It is deliberately the
# Slice-1A subset — NOT the full spec-025 transition set. A fail-closed reader rejects
# any type outside it, so EVERY later slice that introduces a new event type MUST
# extend BOTH this set AND the projection handlers together. Adding a type does NOT
# bump SCHEMA_VERSION — the record SHAPE is unchanged, and a bump would make a reader
# reject prior-version history.
KNOWN_EVENT_TYPES_V1 = frozenset({
    "ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet",
    "AttemptCreditReserved", "AttemptCreditReleased", "AttemptCreditRetained",
    "AttemptCreditReconciled",
    "AttemptConfigured",  # Task 13: the durable per-Attempt safety limits
    "LaneCallClaimed",    # Task 14: durable per-Attempt LLM-call admission
    "ChainResolved", "SelectionFailure", "ReservationOpened", "DispatchStarted",
    "DispatchCompleted", "DispatchUnknown", "CandidateOutcome",
    "ProblemDiscovered", "Proposed", "ProposalVerified", "Rejected",
    # Slice 1B (FR-002): the EXPLICIT proposal-review degradation record. Its payload is
    # schema-checked by _validate_review_rerouted below. `relaxed_constraints` is FACTUAL
    # (what the fallback always relaxes), NOT a causal claim about which constraint made
    # the primary fail. A vocabulary extension only — the record SHAPE is unchanged, so
    # SCHEMA_VERSION stays 1.
    "ReviewRerouted",
    # --- Slice 2 (FR-035): the Attempt lifecycle vocabulary -----------------------------
    # These MIRROR `lifecycle.ATTEMPT_EVENT_TYPES`, which is the declaration;
    # `test_every_declared_transition_has_a_writable_event_type` fails if the two drift.
    # A vocabulary extension only — the record SHAPE is unchanged, so SCHEMA_VERSION stays
    # 1 (Slice 1A F7); bumping it would make a reader reject prior-version history.
    #
    # `ClaimGranted`/`ClaimExpired` on a Problem stream are ATTEMPT transitions (they move
    # the Attempt). `ClaimAcquired`/`ClaimReleased` on the coordinator stream are LANE
    # mutations (they move the singleton). NEITHER IS A DUPLICATE OF THE OTHER and neither
    # is derivable from the other: they live on different STREAMS with independent revision
    # lines, so each needs its own record. They are not independent in TIME, though — the
    # pair is written in ONE transaction (`append_many`), which is why no reconciler ever
    # has to correlate them or handle seeing one without the other.
    #
    # No event type appears on BOTH streams (pinned by
    # `test_no_event_type_lives_on_both_streams`). A reclaim's coordinator side is the
    # ordinary `ClaimReleased` every other release writes; a coordinator-side `ClaimExpired`
    # would be a second type whose only content — the next generation — the next
    # `ClaimAcquired` computes anyway. Disjoint vocabularies also make "which stream is
    # this?" answerable from the event type alone.
    "ClaimGranted", "Implementing", "ImplementationFailed", "PublishFailed",
    "TestingFailed", "EvaluationFailed", "ScopeUnsupported", "FreshnessStale",
    "EvaluationPassed", "PromotionRequested", "PromotionObserved", "PromotionAborted",
    "RevertRequested", "RevertObserved", "RevertAborted", "Retained", "BreakerTripped",
    "ReviewAborted", "ClaimExpired", "ClaimHeartbeat",
    # Slice-2 records that are NOT Attempt transitions: the monitoring close-out
    # (coordinator stream) and the spec's `‡` Problem-scoped rows.
    "MonitorEnded", "SideEffectRequested", "SideEffectObserved", "Cooldown",
})

LEGS = ("primary", "fallback")   # FR-002's two-attempt reroute; nothing else is a leg


def derive_event_id(stream: str, idempotency_key: str) -> str:
    """The DETERMINISTIC id for one side-effecting operation (FR-009). A retried or
    re-invoked identical operation re-derives the same id, so the store returns
    idempotently instead of appending a duplicate."""
    return hashlib.sha256(f"{stream}\x00{idempotency_key}".encode()).hexdigest()


def derive_route_id(attempt_id: str, operation_id: str, leg: str) -> str:
    """The RETRY-STABLE route id for one logical ``route_chat`` call (Task 14).
    Deterministic in the Attempt + operation + leg, so a replay re-derives it rather
    than minting a fresh uuid.

    Defined HERE, beside :func:`derive_event_id`, because ``validate_lane_event`` must
    recompute it to verify a ``LaneCallClaimed`` payload — ``call_ledger`` imports this
    module, so the reverse import would be a cycle.
    """
    return hashlib.sha256(f"{attempt_id}\x00{operation_id}\x00{leg}".encode()).hexdigest()[:32]


@dataclass(frozen=True)
class Event:
    """One lane event (FR-011).

    The four CAS anchors + ``seq`` are stamped by the STORE inside the successful CAS,
    from the authoritative parent, so that ``seq == expected_*_revision`` and
    ``resulting_*_revision == seq + 1`` (an event at seq=N transforms revision N →
    N+1). Exactly one revision SCOPE is populated (coordinator → ``*_lane_revision``,
    per-Problem → ``*_problem_revision``), matching the stream. All are ``None`` before
    the append assigns them.
    """

    event_id: str
    event_type: str
    problem_id: str  # a problem_id, or COORDINATOR_STREAM for coordinator events
    actor: str
    payload: Mapping[str, Any]
    timestamp: str
    schema_version: int = SCHEMA_VERSION
    attempt_id: str | None = None
    expected_lane_revision: int | None = None
    resulting_lane_revision: int | None = None
    expected_problem_revision: int | None = None
    resulting_problem_revision: int | None = None
    seq: int | None = None


def _as_dict(e: Event) -> dict[str, Any]:
    return {
        "event_id": e.event_id,
        "event_type": e.event_type,
        "problem_id": e.problem_id,
        "actor": e.actor,
        "payload": dict(e.payload),
        "timestamp": e.timestamp,
        "schema_version": e.schema_version,
        "attempt_id": e.attempt_id,
        "expected_lane_revision": e.expected_lane_revision,
        "resulting_lane_revision": e.resulting_lane_revision,
        "expected_problem_revision": e.expected_problem_revision,
        "resulting_problem_revision": e.resulting_problem_revision,
        "seq": e.seq,
    }


#: The idempotency-key prefix each cross-stream coordinator event is keyed by.
#: Declared once because FOUR places need it and they must agree EXACTLY: :func:`coord_event`
#: builds with it, `lifecycle`'s effect builders build with it, `cas_claim` derives its
#: ``ClaimAcquired`` id from it, and both the replay path and ``assert_lane_consistent``
#: compute a partner's id from it WITHOUT building the event. It was a bare ``"release"`` /
#: ``"monitor"`` / ``"claim"`` literal in five places across three modules; a typo in any one
#: of them mints a SECOND record for one decision, which is precisely the half-state the
#: whole slice exists to prevent.
COORDINATOR_KEYS: dict[str, str] = {
    "ClaimAcquired": "claim",
    "ClaimReleased": "release",
    "MonitorStarted": "monitor",
}


def coordinator_event_id(event_type: str, problem_id: str, attempt_id: str) -> str:
    """The derived id of a coordinator record — computed, never searched for.

    This is what makes a transaction's partner LOCATABLE on replay and auditable after the
    fact: given either half, the other half's id is a pure function of
    ``(event_type, problem_id, attempt_id)``."""
    if event_type not in COORDINATOR_KEYS:
        raise ValueError(
            f"{event_type!r} is not a cross-stream coordinator event — "
            f"expected one of {sorted(COORDINATOR_KEYS)}"
        )
    return derive_event_id(
        COORDINATOR_STREAM,
        "\x00".join((COORDINATOR_KEYS[event_type], problem_id, attempt_id)))


def coord_event(event_type: str, *, problem_id: str, attempt_id: str, payload: dict,
                actor: str, timestamp: str) -> Event:
    """One coordinator event with a DETERMINISTIC id, so a re-invoked operation rebuilds
    the same event rather than minting a second record of the same decision.

    Lives HERE rather than in :mod:`coordinator` because ``lifecycle``'s effect builders
    also construct coordinator events, and this module is the one both can import without a
    cycle. A second deterministic-id builder there would be the duplication Constitution I
    forbids, and two builders drifting on id derivation would mint duplicate records of one
    decision.

    ``problem_id`` is the CLAIMED Problem and goes in the payload; the ENVELOPE's is always
    :data:`COORDINATOR_STREAM`, because that is the stream this lands on.

    The revision anchors and ``seq`` are deliberately left unset: the store stamps all of
    them inside the CAS from the verified parent (see ``lane_log._finalize``), and a value
    fixed out here would be a guess about a revision we have not yet won."""
    return Event(
        event_id=coordinator_event_id(event_type, problem_id, attempt_id),
        event_type=event_type, problem_id=COORDINATOR_STREAM, actor=actor,
        payload=payload, timestamp=timestamp, attempt_id=attempt_id,
    )


# --- per-type payload schemas ---------------------------------------------------
#
# The envelope check accepts ANY payload, so an event carrying a SAFETY CLAIM a
# projection acts on needs its own validator: a missing/mistyped/inconsistent key
# would otherwise land durably and surface as a KeyError inside the projection, or
# (worse) project false provenance. A type ABSENT from TYPE_VALIDATORS is
# envelope-only BY DESIGN — the audit-mirror types (ChainResolved, DispatchStarted,
# …) are re-serializations of slice-0 dataclasses already type-checked at
# construction. Cross-EVENT invariants (a consistent call_ceiling across an Attempt,
# legal state transitions) belong to the projections, not here.


def _require(payload: Mapping[str, Any], key: str, types: type | tuple[type, ...]) -> Any:
    """Fetch ``key``, raising ValueError (never KeyError/TypeError) if it is absent or
    the wrong type — so a malformed payload is rejected AT THE WRITE BOUNDARY rather
    than exploding inside a projection later."""
    if key not in payload:
        raise ValueError(f"payload missing required key {key!r}")
    value = payload[key]
    if not isinstance(value, types) or (types is str and not value):
        raise ValueError(f"payload key {key!r} must be a non-empty {types}, got {value!r}")
    return value


def _exact_keys(mapping: Mapping[str, Any], allowed: frozenset[str], label: str) -> None:
    """Reject unknown keys. Every event that binds a LIMIT or a ROUTING IDENTITY has an
    EXACT schema, not merely required fields: an unrecognized key cannot be told from a
    typo, and once it is in append-only history readers must guess at semantics nobody
    defined. (Matches the convergence types' ``extra="forbid"``.)"""
    extra = set(mapping) - allowed
    if extra:
        raise ValueError(f"unexpected {label} keys {sorted(extra)} — the schema is exact")


def _positive_int(payload: Mapping[str, Any], key: str) -> int:
    value = _require(payload, key, int)
    if isinstance(value, bool) or value <= 0:   # bool IS an int in Python
        raise ValueError(f"payload key {key!r} must be a positive int, got {value!r}")
    return value


def _non_negative_int(payload: Mapping[str, Any], key: str) -> int:
    """Zero is a legitimate value for a COUNTER that starts at zero — a Problem's first
    cooldown ``epoch``, a claim's first heartbeat ``tick`` — where :func:`_positive_int`
    would reject the very first record of the series."""
    value = _require(payload, key, int)
    if isinstance(value, bool) or value < 0:   # bool IS an int in Python
        raise ValueError(f"payload key {key!r} must be a non-negative int, got {value!r}")
    return value


def _one_of(payload: Mapping[str, Any], key: str, allowed: frozenset[str], label: str) -> str:
    """A CONSTRAINED vocabulary, checked at the write boundary.

    A free-form string here is how a typo becomes a silent new category: nothing rejects
    ``cause="wallclock"``, the counter that keys on ``"wall_clock"`` never sees it, and the
    record is durable and wrong forever."""
    value = _require(payload, key, str)
    if value not in allowed:
        raise ValueError(
            f"{label} payload key {key!r} must be one of {sorted(allowed)}, got {value!r}")
    return value


def _string_list(payload: Mapping[str, Any], key: str, label: str) -> list[str]:
    """A LIST of non-empty strings — possibly empty, never a bare string.

    The bare-string case is the one worth spelling out: ``str`` is iterable, so an
    element-wise check over ``"abc"`` passes one character at a time and a single id
    silently records as three."""
    if key not in payload:
        raise ValueError(f"payload missing required key {key!r}")
    value = payload[key]
    if not isinstance(value, list):
        raise ValueError(
            f"{label} payload key {key!r} must be a list, got {type(value).__name__}")
    for position, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ValueError(
                f"{label} payload key {key!r}[{position}] must be a non-empty string, "
                f"got {item!r}")
    return value


def _instant(value: str, label: str) -> datetime:
    """An ISO-8601 INSTANT: a time AND a timezone, never a bare calendar date.

    One implementation for the envelope timestamp and for every payload field that records
    a moment (``merged_at``, ``cooldown_until``), because they are the same requirement:
    ``"2026-07-24"`` parses fine and would order records from different runners by an offset
    nobody wrote down, and FR-036's whole point is that lane runs execute on independent
    clocks."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} {value!r} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(
            f"{label} {value!r} must include a time AND a timezone "
            "(an instant, not a date)"
        )
    return parsed


def _payload_instant(payload: Mapping[str, Any], key: str) -> datetime:
    return _instant(_require(payload, key, str), f"payload key {key!r}")


def _finite_number(payload: Mapping[str, Any], key: str, *, strictly_positive: bool) -> float:
    """A MONEY value must be a real, FINITE number.

    ``nan``/``inf`` slip past a naive ``value < 0`` guard — and NaN is the worst
    possible failure on this path: the ledger's admission test is ``counting_total +
    credits > budget``, and EVERY comparison against NaN is False, so the cap silently
    becomes "always admit". ``inf`` is an unbounded value by another name. ``bool`` is
    rejected because ``True`` is a perfectly good ``int`` to Python and a nonsense
    credit amount to us. A NEGATIVE reserved amount is rejected outright
    (``strictly_positive``): it would lower ``counting_total`` and hand back budget
    that was already consumed.
    """
    value = _require(payload, key, (int, float))
    if isinstance(value, bool):
        raise ValueError(f"payload key {key!r} must be a number, not a bool")
    if not math.isfinite(value):
        raise ValueError(
            f"payload key {key!r} must be FINITE, got {value!r} — a non-finite credit "
            "value disables the cap (every comparison against NaN is False)"
        )
    if strictly_positive:
        if value <= 0:
            raise ValueError(
                f"payload key {key!r} must be > 0, got {value!r} — a negative reservation "
                "REOPENS spent budget, and a zero one dispatches a paid call the Attempt "
                "cap can never bind"
            )
    elif value < 0:
        raise ValueError(f"payload key {key!r} must be non-negative, got {value!r}")
    return float(value)


def _finite_non_negative(payload: Mapping[str, Any], key: str) -> float:
    """A budget CEILING may legitimately be zero (an Attempt allowed no paid spend)."""
    return _finite_number(payload, key, strictly_positive=False)


def _finite_positive(payload: Mapping[str, Any], key: str) -> float:
    """A reserved AMOUNT may not be zero or negative — see :func:`_finite_number`."""
    return _finite_number(payload, key, strictly_positive=True)


def _same_attempt(raw: Mapping[str, Any]) -> str:
    """The payload's attempt_id MUST equal the envelope's. Projections filter by the
    PAYLOAD's attempt id, so a disagreement would file a claim/limit under one Attempt
    while the event envelope says another — a silent misattribution."""
    payload = raw["payload"]
    attempt = _require(payload, "attempt_id", str)
    if raw.get("attempt_id") != attempt:
        raise ValueError(
            f"payload attempt_id {attempt!r} disagrees with the event's "
            f"attempt_id {raw.get('attempt_id')!r}"
        )
    return attempt


def _same_problem(raw: Mapping[str, Any]) -> str:
    """The payload's ``problem_id`` MUST equal the envelope's, for a PROBLEM-stream event.

    Sibling of :func:`_same_attempt` and the same failure it prevents one level up: a
    record filed on stream P1 whose payload names P2 has two readings and no way to tell
    which the writer meant. Deliberately NOT applied to coordinator-stream events, where
    the payload's ``problem_id`` is the CLAIMED Problem and the envelope's is
    :data:`COORDINATOR_STREAM` — there the two are meant to differ."""
    payload = raw["payload"]
    problem = _require(payload, "problem_id", str)
    if raw.get("problem_id") != problem:
        raise ValueError(
            f"payload problem_id {problem!r} disagrees with the event's "
            f"problem_id {raw.get('problem_id')!r}"
        )
    return problem


def _no_envelope_attempt(raw: Mapping[str, Any]) -> None:
    """A Problem-stream record that is NOT an Attempt transition must carry NO envelope
    ``attempt_id``.

    ``project_attempt`` selects an Attempt's history as ``[e for e in stream if
    e.attempt_id == attempt_id]`` and folds everything it finds, failing closed on any type
    outside ``lifecycle.ATTEMPT_EVENT_TYPES``. So an intent or a cooldown stamped with an
    envelope ``attempt_id`` would make every LATER projection of that Attempt raise —
    permanently, because history is append-only, and the Attempt would be unable to record
    even its own terminal. The association still exists: it lives in the PAYLOAD, which is
    what the intent reader filters on. `lifecycle.NON_TRANSITIONS` is the ONLY way an event
    legitimately lands under an Attempt's envelope without moving its state, and it carries
    the rules that make such a record legal."""
    if raw.get("attempt_id") is not None:
        raise ValueError(
            f"{raw['event_type']} must not carry an envelope attempt_id "
            f"({raw['attempt_id']!r}) — it is not an Attempt transition, and project_attempt "
            "folds every event filed under an Attempt's envelope"
        )


_ATTEMPT_CONFIG_KEYS = frozenset({"attempt_id", "call_ceiling", "attempt_budget_credits"})
_CALL_CLAIM_KEYS = frozenset({"attempt_id", "operation_id", "leg", "route_id", "call_ceiling"})
_CREDIT_RESERVED_KEYS = frozenset({"reservation_id", "call_id", "reserved_credits"})


def _validate_attempt_configured(raw: Mapping[str, Any]) -> None:
    """Task 13's durable limits. These two numbers ARE the Attempt's safety envelope and
    they are IMMUTABLE once written, so they must be exactly well-formed before binding."""
    payload = raw["payload"]
    _exact_keys(payload, _ATTEMPT_CONFIG_KEYS, "AttemptConfigured payload")
    _same_attempt(raw)
    _positive_int(payload, "call_ceiling")
    _finite_non_negative(payload, "attempt_budget_credits")


def _validate_attempt_credit_reserved(raw: Mapping[str, Any]) -> None:
    """The reservation record. ``project_reservations`` SUMS ``reserved_credits`` into
    ``counting_total``, which is the number the Attempt cap is compared against — so
    this payload carries a monetary safety claim and must not rest on trusted
    construction alone. A negative amount persisted here lowers the running total and
    hands back budget that was already spent; a NaN one makes every later comparison
    False. The Attempt binding is the ENVELOPE's ``attempt_id`` (the projection filters
    on ``Event.attempt_id``), so there is no payload copy to cross-check — but an event
    with no Attempt at all could never be projected, so require one."""
    payload = raw["payload"]
    _exact_keys(payload, _CREDIT_RESERVED_KEYS, "AttemptCreditReserved payload")
    if not raw.get("attempt_id"):
        raise ValueError("an AttemptCreditReserved event must carry its envelope attempt_id")
    _require(payload, "reservation_id", str)
    _require(payload, "call_id", str)
    _finite_positive(payload, "reserved_credits")


def _validate_lane_call_claimed(raw: Mapping[str, Any]) -> None:
    """Task 14's admission record. The ceiling projection COUNTS these and the router
    ROUTES on the recorded ``route_id``, so every field it reads must be present, typed,
    and SELF-CONSISTENT — a claim whose route_id was not derived from its own (attempt,
    operation, leg) would route one logical call onto another's identity."""
    payload = raw["payload"]
    _exact_keys(payload, _CALL_CLAIM_KEYS, "LaneCallClaimed payload")
    attempt = _same_attempt(raw)
    operation_id = _require(payload, "operation_id", str)
    leg = _require(payload, "leg", str)
    if leg not in LEGS:
        raise ValueError(f"payload key 'leg' must be one of {LEGS}, got {leg!r}")
    route_id = _require(payload, "route_id", str)
    expected = derive_route_id(attempt, operation_id, leg)
    if route_id != expected:
        raise ValueError(
            f"route_id {route_id!r} was not derived from (attempt={attempt!r}, "
            f"operation={operation_id!r}, leg={leg!r}) — expected {expected!r}"
        )
    _positive_int(payload, "call_ceiling")


#: The ONE sanctioned proposal reroute (FR-002). Pinned, not merely documented: a record
#: naming other profiles would assert a degradation that never happened.
#:
#: PUBLIC because they are the single source of truth for three separate consumers — this
#: validator (write boundary), ``route_context.record_reroute`` (what gets written), and
#: ``LLMReviewer``'s configuration check (what actually EXECUTES). A second copy is exactly
#: how a reviewer comes to run one profile pair while durably recording another.
REROUTE_PRIMARY_PROFILE = "independent_review"
REROUTE_FALLBACK_PROFILE = "deep_review"
REROUTE_TRIGGER = "ModelUnavailable"
REROUTE_RELAXED_CONSTRAINTS = ("family_independence", "snapshot_freshness")

#: The EXACT key set. "Required fields" alone would let extras ride along: harmless today,
#: but it makes the contract untestable and future schema evolution ambiguous — a reader
#: could not tell a typo'd key from a new one.
_REROUTE_KEYS = frozenset({
    "operation_id", "lens", "primary_profile", "fallback_profile",
    "primary_route_id", "fallback_route_id", "primary_failure", "relaxed_constraints",
})
_REROUTE_FAILURE_KEYS = frozenset({"exception_type", "message"})


def _validate_review_rerouted(raw: Mapping[str, Any]) -> None:
    """FR-002's degradation record.

    ``build_invocation_identity`` builds its ``IndependenceDegraded`` straight out of this
    payload, so an unchecked key is either a ``KeyError`` inside that projection or — worse
    — a FALSE claim about which safeguards the fallback gave up. The profile, trigger, and
    relaxed-constraint values are pinned to v1's sanctioned reroute: a later stage that
    reroutes differently must EXTEND this validator with its own combination, never bypass
    it."""
    payload = raw["payload"]
    _exact_keys(payload, _REROUTE_KEYS, "ReviewRerouted payload")
    for key in ("operation_id", "lens", "primary_route_id", "fallback_route_id"):
        _require(payload, key, str)
    # Recompute BOTH legs at WRITE time from the envelope's attempt_id — the same binding
    # build_invocation_identity checks at projection time. The projection already fails
    # closed, so this is defense in depth, but a record that can never become durable beats
    # one that is only rejected when read.
    attempt_id = raw.get("attempt_id")
    if not attempt_id:
        raise ValueError("a ReviewRerouted event must carry its envelope attempt_id")
    for key, leg in (("primary_route_id", "primary"), ("fallback_route_id", "fallback")):
        expected = derive_route_id(attempt_id, payload["operation_id"], leg)
        if payload[key] != expected:
            raise ValueError(
                f"{key}={payload[key]!r} is not attempt {attempt_id!r}'s {leg} claim for "
                f"operation {payload['operation_id']!r} — expected {expected!r}"
            )
    if payload["primary_route_id"] == payload["fallback_route_id"]:
        raise ValueError("primary_route_id and fallback_route_id must be distinct "
                         "(the two legs are two logical route_chat invocations)")
    primary = _require(payload, "primary_profile", str)
    if primary != REROUTE_PRIMARY_PROFILE:
        raise ValueError(f"primary_profile must be {REROUTE_PRIMARY_PROFILE!r}, got {primary!r}")
    fallback = _require(payload, "fallback_profile", str)
    if fallback != REROUTE_FALLBACK_PROFILE:
        raise ValueError(
            f"fallback_profile must be {REROUTE_FALLBACK_PROFILE!r}, got {fallback!r}"
        )
    failure = _require(payload, "primary_failure", Mapping)
    _exact_keys(failure, _REROUTE_FAILURE_KEYS, "ReviewRerouted primary_failure")
    for key in ("exception_type", "message"):
        _require(failure, key, str)
    if failure["exception_type"] != REROUTE_TRIGGER:
        raise ValueError(f"primary_failure.exception_type must be {REROUTE_TRIGGER!r} — FR-002 "
                         f"reroutes on nothing else; got {failure['exception_type']!r}")
    relaxed = _require(payload, "relaxed_constraints", list)
    if tuple(relaxed) != REROUTE_RELAXED_CONSTRAINTS:
        raise ValueError(f"relaxed_constraints must be exactly {list(REROUTE_RELAXED_CONSTRAINTS)} (the "
                         f"fallback always relaxes both, in that order), got {relaxed!r}")


_RESERVATION_TRANSITION_KEYS = frozenset({"reservation_id"})


def _validate_reservation_transition(raw: Mapping[str, Any]) -> None:
    """``AttemptCreditRetained``/``Released``/``Reconciled`` — the money state machine's
    transitions.

    Both fields the projection reads are required. Without ``reservation_id`` the
    transition names nothing and would be skipped; without the envelope ``attempt_id`` the
    projection — which filters on it — would never see the event at all. Either way a
    ``Released`` that silently vanishes leaves its credits counting against the Attempt's
    budget forever, and a lost ``Retained`` breaks the reconcile chain that follows it."""
    payload = raw["payload"]
    _exact_keys(payload, _RESERVATION_TRANSITION_KEYS, f"{raw['event_type']} payload")
    if not raw.get("attempt_id"):
        raise ValueError(f"an {raw['event_type']} event must carry its envelope attempt_id")
    _require(payload, "reservation_id", str)


_CLAIM_KEYS = frozenset({"problem_id", "attempt_id"})
_MONITOR_KEYS = frozenset({"problem_id", "attempt_id", "merged_at"})
_MONITOR_ENDED_KEYS = frozenset({"problem_id", "attempt_id", "outcome"})
_PROMOTION_KEYS = frozenset({"promotion_enabled", "policy_version"})


def _validate_claim(raw: Mapping[str, Any]) -> None:
    """``ClaimAcquired``/``ClaimReleased`` — the lane's OWNERSHIP record.

    ``project_coordinator`` reads these two ids to decide who holds the singleton claim,
    and ``cas_release`` compares them to refuse a delayed release from a previous owner.
    A missing or empty id would therefore either explode inside the projection or, worse,
    compare equal to nothing and let a stale release clear a live claim.

    The payload's ``problem_id`` is the CLAIMED Problem; the envelope's is
    ``COORDINATOR_STREAM`` (this is a coordinator-stream event), so those two are
    deliberately NOT cross-checked. The ``attempt_id`` is cross-checked, because the
    envelope and the payload are naming the same Attempt.
    """
    payload = raw["payload"]
    _exact_keys(payload, _CLAIM_KEYS, f"{raw['event_type']} payload")
    _require(payload, "problem_id", str)
    _same_attempt(raw)


def _validate_monitor_started(raw: Mapping[str, Any]) -> None:
    """The monitoring window opens here, and BOTH added fields are required rather than
    optional (spec 025 rev 24).

    ``merged_at`` is the instant the promotion being monitored was observed — what
    ``last_autonomous_merge_at`` folds to. ``problem_id`` is what lets the fold's ownership
    check compare the PAIR; without it the check falls back to matching an ``attempt_id``
    alone, which is the 1A F6 mistake. ``MonitorStarted`` has exactly ONE producer (the
    transition effect builder) and it always knows both, so an optional field would exist
    solely so a record could be written without the value the coordinator then needs — which
    is how ``last_autonomous_merge_at`` ends up ``None`` for a merge that demonstrably
    happened."""
    payload = raw["payload"]
    _exact_keys(payload, _MONITOR_KEYS, "MonitorStarted payload")
    _require(payload, "problem_id", str)
    _same_attempt(raw)
    _payload_instant(payload, "merged_at")


def _validate_monitor_ended(raw: Mapping[str, Any]) -> None:
    """The close-out of a monitoring window. ``outcome`` records WHICH terminal ended it,
    so the coordinator's removal from ``monitored_attempts`` is self-describing rather than
    something a reader has to go find on the Attempt's stream."""
    payload = raw["payload"]
    _exact_keys(payload, _MONITOR_ENDED_KEYS, "MonitorEnded payload")
    _require(payload, "problem_id", str)
    _same_attempt(raw)
    _one_of(payload, "outcome", _MONITOR_OUTCOMES, "MonitorEnded")


def _validate_promotion_enabled_set(raw: Mapping[str, Any]) -> None:
    """The autonomous-merge gate. ``promotion_enabled`` must be an ACTUAL bool: the
    projection would otherwise coerce it, and ``bool("false")`` is ``True`` — a record
    meant to disable autonomous promotion would enable it. ``policy_version`` is optional
    (a flip that does not change policy carries the previous version forward) but is
    type-checked when present."""
    payload = raw["payload"]
    _exact_keys(payload, _PROMOTION_KEYS, "PromotionEnabledSet payload")
    if "promotion_enabled" not in payload:
        raise ValueError("payload missing required key 'promotion_enabled'")
    if not isinstance(payload["promotion_enabled"], bool):
        raise ValueError(
            f"payload key 'promotion_enabled' must be a bool, got "
            f"{payload['promotion_enabled']!r} — a truthy string would ENABLE a gate the "
            "record was written to close"
        )
    if "policy_version" in payload:
        version = payload["policy_version"]
        if isinstance(version, bool) or not isinstance(version, int) or version < 0:
            raise ValueError(
                f"payload key 'policy_version' must be a non-negative int, got {version!r}"
            )


# --- Slice 2: the Attempt lifecycle ---------------------------------------------------

#: Public because `lifecycle` reads it: the `ReviewAborted` state witness maps each source
#: state to the stage term it may carry, and its import-time check asserts the map's values
#: are exactly this set. Two hand-written copies of a vocabulary that must agree is how a
#: `stage` the write boundary accepts becomes a `stage` the fold refuses — which does not
#: reject the append, it wedges every later projection of the Attempt it landed on.
REVIEW_STAGES = frozenset({"proposal", "patch"})
#: FR-034's seven causes. An abort is UNCOUNTED against the quality cap, so what it says
#: about itself is the only record of why a Problem's operational streak advanced.
_REVIEW_ABORT_CAUSES = frozenset({
    "model_unavailable", "chain_exhausted", "route_audit_fatal", "route_replay",
    "unresolved_dispatch", "budget_ceiling", "wall_clock",
})
_CLAIM_EXPIRY_REASONS = frozenset({"heartbeat_lapsed", "hold_time_exceeded"})
_SIDE_EFFECTS = frozenset({"publish", "merge", "revert"})
_INTENT_DISPOSITIONS = frozenset({"landed", "rejected", "contained", "ambiguous"})
_COOLDOWN_CAUSES = frozenset({"quality", "operational"})
_MONITOR_OUTCOMES = frozenset({"retained", "reverted"})

_HEARTBEAT_KEYS = frozenset({"problem_id", "attempt_id", "claim_generation", "tick"})
_CLAIM_EXPIRED_KEYS = frozenset({"problem_id", "attempt_id", "claim_generation", "reason"})
_REVIEW_ABORTED_KEYS = frozenset({
    "problem_id", "attempt_id", "stage", "cause", "unresolved_dispatches"})
_SIDE_EFFECT_KEYS = frozenset({
    "problem_id", "attempt_id", "claim_generation", "effect", "idempotency_key"})
_SIDE_EFFECT_OBSERVED_KEYS = _SIDE_EFFECT_KEYS | {"disposition"}
_COOLDOWN_KEYS = frozenset({"problem_id", "cause", "epoch", "cooldown_until"})


def _validate_attempt_transition(raw: Mapping[str, Any]) -> None:
    """The contract EVERY Attempt transition shares: it names its Problem and its Attempt,
    and the payload agrees with the envelope on both.

    Deliberately NOT :func:`_exact_keys`. The house rule is that an event binding a LIMIT or
    a ROUTING IDENTITY has an exact schema; a transition binds neither, and its
    per-transition fields (the ``head_sha`` in ``EvaluationPassed``'s idempotency key, the
    ``reason`` in ``RevertRequested``'s, …) are declared by the tasks that write them.
    Fixing an exact key set here would mean guessing those, and a guess would reject records
    the spec's own table requires.

    What IS universal is the identity pair, and it is universal because every reader depends
    on it: ``project_attempt`` selects a history by the envelope ``attempt_id`` and the
    coordinator pairing walks compare ``(problem_id, attempt_id)`` across streams. A
    transition whose ids disagree is filed against the wrong Attempt's timeline — silently,
    and durably."""
    _same_problem(raw)
    _same_attempt(raw)


def _validate_claim_granted(raw: Mapping[str, Any]) -> None:
    """The ATTEMPT-side half of a claim grant (the coordinator-side half is
    ``ClaimAcquired``, written in the same transaction).

    ``claim_generation`` is required because ``walk_attempt`` READS it: a grant without one
    is a history the fold refuses, and refusing it here — at the write boundary — is the
    difference between a rejected append and an Attempt whose every future projection
    raises. Task 8 adds the four claim-bound policy terms (``claim_expiry_s``,
    ``max_claim_hold_time_s``, ``max_clock_skew_s``, ``policy_version``) and makes this
    schema exact once the full key set is known."""
    _validate_attempt_transition(raw)
    _positive_int(raw["payload"], "claim_generation")


def _validate_claim_heartbeat(raw: Mapping[str, Any]) -> None:
    """Proof of life for ONE claim, and only for the claim it names.

    The generation is the fencing token: a beat stamped with a generation the Attempt no
    longer holds is a crashed runner's beat arriving after a reclaim, and accepting it would
    defeat the token. ``tick`` starts at zero, so it is non-negative rather than positive —
    the first beat of a claim is a legitimate record."""
    payload = raw["payload"]
    _exact_keys(payload, _HEARTBEAT_KEYS, "ClaimHeartbeat payload")
    _validate_attempt_transition(raw)
    _positive_int(payload, "claim_generation")
    _non_negative_int(payload, "tick")


def _validate_claim_expired(raw: Mapping[str, Any]) -> None:
    """The one terminal written by a DIFFERENT run than the one that abandoned the Attempt
    (FR-035). ``claim_generation`` names the claim being expired — the reclaimer re-verifies
    it INSIDE the CAS, so a record naming the wrong one would let a stale observation evict
    a live holder. ``reason`` distinguishes the two independent preconditions, which have
    different repair paths."""
    payload = raw["payload"]
    _exact_keys(payload, _CLAIM_EXPIRED_KEYS, "ClaimExpired payload")
    _validate_attempt_transition(raw)
    _positive_int(payload, "claim_generation")
    _one_of(payload, "reason", _CLAIM_EXPIRY_REASONS, "ClaimExpired")


def _validate_review_aborted(raw: Mapping[str, Any]) -> None:
    """An operational abort, NOT a verdict (spec rev 17): the lane could not reach an
    answer, so this is uncounted against the Problem's quality cap and counted against its
    operational streak instead.

    ``stage`` is required because ``ReviewAborted`` is legal from two states where two
    different reviews run, and "which review" is not recoverable from the transition alone.
    ``unresolved_dispatches`` lists the route ids resolved to ``dispatch_unknown`` before
    the decision (FR-034); it is a list because the honest answer is often "none", and an
    empty list says that where a missing key would say nothing at all."""
    payload = raw["payload"]
    _exact_keys(payload, _REVIEW_ABORTED_KEYS, "ReviewAborted payload")
    _validate_attempt_transition(raw)
    _one_of(payload, "stage", REVIEW_STAGES, "ReviewAborted")
    _one_of(payload, "cause", _REVIEW_ABORT_CAUSES, "ReviewAborted")
    _string_list(payload, "unresolved_dispatches", "ReviewAborted")


def _validate_side_effect(raw: Mapping[str, Any]) -> None:
    """The saga's two records: an intent, and the observation that closes it.

    They are NOT Attempt transitions — ``PromotionRequested`` moves the Attempt, this is the
    fencing record that blocks a reclaim until reconciled — so they carry no envelope
    ``attempt_id`` (see :func:`_no_envelope_attempt`). ``idempotency_key`` is what makes the
    external effect re-observable after a crash instead of re-attempted."""
    payload = raw["payload"]
    observed = raw["event_type"] == "SideEffectObserved"
    _exact_keys(payload, _SIDE_EFFECT_OBSERVED_KEYS if observed else _SIDE_EFFECT_KEYS,
                f"{raw['event_type']} payload")
    _no_envelope_attempt(raw)
    _same_problem(raw)
    _require(payload, "attempt_id", str)
    _positive_int(payload, "claim_generation")
    _one_of(payload, "effect", _SIDE_EFFECTS, raw["event_type"])
    _require(payload, "idempotency_key", str)
    if observed:
        # FOUR dispositions, not two: `contained` (may still land, but only where it is
        # harmless) and `rejected` (landing is now impossible) are different facts, and
        # collapsing them is the rev-22 error.
        _one_of(payload, "disposition", _INTENT_DISPOSITIONS, "SideEffectObserved")


def _validate_cooldown(raw: Mapping[str, Any]) -> None:
    """A PROBLEM's rest, not an Attempt's outcome — so no envelope ``attempt_id``, and no
    ``attempt_id`` in the payload either.

    ``cause`` and ``epoch`` are both required because the idempotency key is
    ``(problem_id, "cooldown", cause, epoch)``: without the cause the two counters share one
    slot, and without the epoch a Problem that cooled down once could never cool down
    again (the rev-18 defect)."""
    payload = raw["payload"]
    _exact_keys(payload, _COOLDOWN_KEYS, "Cooldown payload")
    _no_envelope_attempt(raw)
    _same_problem(raw)
    _one_of(payload, "cause", _COOLDOWN_CAUSES, "Cooldown")
    _non_negative_int(payload, "epoch")
    _payload_instant(payload, "cooldown_until")


#: The transitions whose payload is the identity pair plus whatever the writing task adds.
#: Listed rather than derived from `lifecycle.TRANSITIONS` on purpose: importing `lifecycle`
#: here would be a cycle (it imports this module), and the two sets agreeing is asserted by
#: `test_every_declared_transition_has_a_writable_event_type` — a check, not a hope.
_PLAIN_ATTEMPT_TRANSITIONS = frozenset({
    "Proposed", "ProposalVerified", "Rejected", "Implementing", "ImplementationFailed",
    "PublishFailed", "TestingFailed", "EvaluationFailed", "ScopeUnsupported",
    "FreshnessStale", "EvaluationPassed", "PromotionRequested", "PromotionObserved",
    "PromotionAborted", "RevertRequested", "RevertObserved", "RevertAborted", "Retained",
    "BreakerTripped",
})


#: Per-type schemas. Each validator receives the WHOLE raw event, not just the payload:
#: several invariants are cross-field (``payload["attempt_id"]`` must equal the
#: envelope's), and a payload-only signature cannot express that.
TYPE_VALIDATORS: dict[str, Callable[[Mapping[str, Any]], None]] = {
    "AttemptConfigured": _validate_attempt_configured,
    "AttemptCreditReserved": _validate_attempt_credit_reserved,
    "AttemptCreditRetained": _validate_reservation_transition,
    "AttemptCreditReleased": _validate_reservation_transition,
    "AttemptCreditReconciled": _validate_reservation_transition,
    "LaneCallClaimed": _validate_lane_call_claimed,
    # The coordinator stream: these four are what `project_coordinator` folds, and the
    # projection is the lane's recovery authority — a malformed payload must be refused at
    # the WRITE boundary, not surface as a KeyError inside the fold once it is durable.
    "ClaimAcquired": _validate_claim,
    "ClaimReleased": _validate_claim,
    "MonitorStarted": _validate_monitor_started,
    "PromotionEnabledSet": _validate_promotion_enabled_set,
    # Slice 1B: vocabulary membership alone would leave this payload unchecked, and it is
    # not a passive record — the invocation-identity projection reads it field by field.
    "ReviewRerouted": _validate_review_rerouted,
    # Slice 2. Every Attempt transition is validated — the plain ones share the identity
    # contract, the rest add their own fields. A type in the vocabulary with NO validator
    # would be a payload nobody checks, and `walk_attempt` reads these payloads.
    **dict.fromkeys(_PLAIN_ATTEMPT_TRANSITIONS, _validate_attempt_transition),
    "ClaimGranted": _validate_claim_granted,
    "ClaimHeartbeat": _validate_claim_heartbeat,
    "ClaimExpired": _validate_claim_expired,
    "ReviewAborted": _validate_review_aborted,
    "MonitorEnded": _validate_monitor_ended,
    "SideEffectRequested": _validate_side_effect,
    "SideEffectObserved": _validate_side_effect,
    "Cooldown": _validate_cooldown,
}


def _envelope_str(raw: Mapping[str, Any], key: str) -> str:
    """An authoritative envelope field must be a NON-EMPTY string.

    Presence alone is not a schema. An empty ``problem_id`` names no stream, an empty
    ``actor`` attributes a provenance record to nobody, and either would be written
    into immutable history that later readers must trust (issue #1242).
    """
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"lane event {key}={value!r} must be a non-empty string")
    return value


def _envelope_int(raw: Mapping[str, Any], key: str, value: Any, *, minimum: int = 0) -> int:
    """An authoritative envelope integer — and NOT a bool.

    ``True`` is an ``int`` to Python (``True == 1``, and it hashes as 1), so a boolean
    ``seq`` or revision anchor sails through every arithmetic check and then orders the
    projection as position 1. ``seq`` is the lane's ORDERING authority, so that is a
    corruption of the sequence itself, not a cosmetic type sloppiness.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"lane event {key}={value!r} must be an int (bool is not an int here)")
    if value < minimum:
        raise ValueError(f"lane event {key}={value!r} must be >= {minimum}")
    return value


def validate_lane_event(raw: dict) -> None:
    """Fail-closed schema validation, run at the write boundary (after the store stamps
    seq + the revision fields) AND on every read. Rejects any event that could corrupt a
    projection.

    Note: this validates ONE event's shape. LEGAL STATE TRANSITIONS across events are
    enforced by the projections (they are the recovery authority) — see
    ``project_coordinator`` / ``project_reservations``.
    """
    for key in ("event_id", "event_type", "problem_id", "actor", "payload", "timestamp",
                "schema_version"):
        if key not in raw:
            raise ValueError(f"lane event missing required field {key!r}")
    # TYPES, not just presence. Every field below lands in immutable history that later
    # readers must trust, so each is checked for the type it actually needs to be.
    for key in ("event_id", "event_type", "problem_id", "actor"):
        _envelope_str(raw, key)
    _envelope_int(raw, "schema_version", raw["schema_version"], minimum=1)
    if raw["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:  # never reject prior history
        raise ValueError(
            f"lane event schema_version {raw['schema_version']!r} not in {SUPPORTED_SCHEMA_VERSIONS}"
        )
    if raw["event_type"] not in KNOWN_EVENT_TYPES_V1:
        raise ValueError(f"lane event_type {raw['event_type']!r} not in KNOWN_EVENT_TYPES_V1")
    if not _SAFE_ID.match(raw["event_id"]):
        raise ValueError(f"lane event_id {raw['event_id']!r} must match {_SAFE_ID.pattern}")
    attempt_id = raw.get("attempt_id")
    if attempt_id is not None and (not isinstance(attempt_id, str) or not attempt_id):
        # A non-string attempt_id contaminates attribution for every event type without
        # a specialized validator — the projections filter on this field.
        raise ValueError(f"lane event attempt_id {attempt_id!r} must be None or a non-empty string")
    is_coord = raw["problem_id"] == COORDINATOR_STREAM
    scope = "lane" if is_coord else "problem"
    other = "problem" if is_coord else "lane"
    exp, res = raw.get(f"expected_{scope}_revision"), raw.get(f"resulting_{scope}_revision")
    if exp is None or res is None:
        raise ValueError(f"{scope}-stream event must set expected_/resulting_{scope}_revision")
    if (raw.get(f"expected_{other}_revision") is not None
            or raw.get(f"resulting_{other}_revision") is not None):
        raise ValueError(f"{scope}-stream event must NOT set the {other} revision scope")
    seq = raw.get("seq")
    if seq is None:
        raise ValueError("lane event must carry the store-assigned seq")
    _envelope_int(raw, "seq", seq)
    _envelope_int(raw, f"expected_{scope}_revision", exp)
    _envelope_int(raw, f"resulting_{scope}_revision", res, minimum=1)
    if exp != seq or res != seq + 1:
        raise ValueError(
            f"revision anchors inconsistent: seq={seq}, expected={exp}, resulting={res} "
            "(require expected==seq and resulting==seq+1)"
        )
    # FR-011 records an INSTANT, not a calendar day: "2026-07-24" parses fine and would
    # order events from different runners by an offset nobody recorded. A timezone-aware
    # value is also what makes the conservative reconciliation timeout (Task 12) comparable
    # across processes. Same rule as every payload field that records a moment, hence the
    # shared `_instant` — the message is unchanged.
    _instant(_envelope_str(raw, "timestamp"), "lane event timestamp")
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError(f"lane event payload must be a mapping, got {type(payload).__name__}")
    validator = TYPE_VALIDATORS.get(raw["event_type"])
    if validator is not None:
        try:
            validator(raw)          # the WHOLE event — payload/envelope cross-checks
        except ValueError as exc:
            raise ValueError(f"{raw['event_type']} payload invalid: {exc}") from exc


def payload_field(event: Event, key: str) -> Any:
    """A payload field a PROJECTION acts on, as a ValueError rather than a KeyError.

    :func:`validate_lane_event` already rejects a malformed payload at the write boundary;
    this is what keeps a hand-built or otherwise unvalidated ``Event`` from reaching a fold
    as a crash instead of a refusal. Shared by every projection so the fail-closed shape is
    written once."""
    try:
        return event.payload[key]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"{event.event_type} event {event.event_id!r} payload lacks {key!r} — fail closed"
        ) from exc


def event_to_json(event: Event) -> str:
    """The canonical serialization.

    ``allow_nan=False``: Python's json emits bare ``NaN``/``Infinity``, which is not
    valid JSON — it round-trips only in Python and breaks every other reader of this
    append-only log. A non-finite number must never reach the ref.
    """
    return json.dumps(
        _as_dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def event_from_json(text: str) -> Event:
    d = json.loads(text)
    return Event(
        event_id=d["event_id"],
        event_type=d["event_type"],
        problem_id=d["problem_id"],
        actor=d["actor"],
        payload=d["payload"],
        timestamp=d["timestamp"],
        schema_version=d["schema_version"],
        attempt_id=d.get("attempt_id"),
        expected_lane_revision=d.get("expected_lane_revision"),
        resulting_lane_revision=d.get("resulting_lane_revision"),
        expected_problem_revision=d.get("expected_problem_revision"),
        resulting_problem_revision=d.get("resulting_problem_revision"),
        seq=d.get("seq"),
    )


__all__ = [
    "COORDINATOR_KEYS",
    "COORDINATOR_STREAM",
    "KNOWN_EVENT_TYPES_V1",
    "LEGS",
    "REROUTE_FALLBACK_PROFILE",
    "REROUTE_PRIMARY_PROFILE",
    "REROUTE_RELAXED_CONSTRAINTS",
    "REROUTE_TRIGGER",
    "SCHEMA_VERSION",
    "SEQ_FIELD",
    "SUPPORTED_SCHEMA_VERSIONS",
    "TYPE_VALIDATORS",
    "Event",
    "coord_event",
    "coordinator_event_id",
    "derive_event_id",
    "derive_route_id",
    "event_from_json",
    "event_to_json",
    "validate_lane_event",
]
