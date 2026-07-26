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


#: Per-type schemas. Each validator receives the WHOLE raw event, not just the payload:
#: several invariants are cross-field (``payload["attempt_id"]`` must equal the
#: envelope's), and a payload-only signature cannot express that.
TYPE_VALIDATORS: dict[str, Callable[[Mapping[str, Any]], None]] = {
    "AttemptConfigured": _validate_attempt_configured,
    "AttemptCreditReserved": _validate_attempt_credit_reserved,
    "LaneCallClaimed": _validate_lane_call_claimed,
    # Slice 1B registers "ReviewRerouted" here.
}


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
    if raw["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:  # never reject prior history
        raise ValueError(
            f"lane event schema_version {raw['schema_version']!r} not in {SUPPORTED_SCHEMA_VERSIONS}"
        )
    if raw["event_type"] not in KNOWN_EVENT_TYPES_V1:
        raise ValueError(f"lane event_type {raw['event_type']!r} not in KNOWN_EVENT_TYPES_V1")
    if not _SAFE_ID.match(str(raw["event_id"])):
        raise ValueError(f"lane event_id {raw['event_id']!r} must match {_SAFE_ID.pattern}")
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
    if seq is None or exp != seq or res != seq + 1:
        raise ValueError(
            f"revision anchors inconsistent: seq={seq}, expected={exp}, resulting={res} "
            "(require expected==seq and resulting==seq+1)"
        )
    try:
        datetime.fromisoformat(str(raw["timestamp"]))
    except ValueError as exc:
        raise ValueError(f"lane event timestamp {raw['timestamp']!r} is not ISO-8601") from exc
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError(f"lane event payload must be a mapping, got {type(payload).__name__}")
    validator = TYPE_VALIDATORS.get(raw["event_type"])
    if validator is not None:
        try:
            validator(raw)          # the WHOLE event — payload/envelope cross-checks
        except ValueError as exc:
            raise ValueError(f"{raw['event_type']} payload invalid: {exc}") from exc


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
    "COORDINATOR_STREAM",
    "KNOWN_EVENT_TYPES_V1",
    "LEGS",
    "SCHEMA_VERSION",
    "SEQ_FIELD",
    "SUPPORTED_SCHEMA_VERSIONS",
    "TYPE_VALIDATORS",
    "Event",
    "derive_event_id",
    "derive_route_id",
    "event_from_json",
    "event_to_json",
    "validate_lane_event",
]
