"""The lane's durable ``RouteAudit`` (FR-033a) plus its unknown-dispatch reconciliation.

Every audit event lands on the protected lane ref through the same CAS as everything else.
That matters for ``claim_dispatch``: a bare local file that never reached the ref is NOT
durable evidence — a later commit failure would orphan it, and a replay would treat the
orphan as committed and refuse a dispatch whose evidence never persisted. Going through
``append_to_log`` means the outcome is returned ONLY after the ref moved.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
from pathlib import Path

from llmxive.model_selection.attempt_hooks import (
    DispatchStarted,
    DispatchUnknown,
    RouteAuditEvent,
)
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lane_log import (
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    read,
)

#: A candidate whose dispatch reached one of these outcomes has a KNOWN result. A failed
#: candidate is not an unknown one — only the absence of any resolution is.
_TERMINAL_OUTCOMES = frozenset({"advance", "abort", "skip"})


def _terminal_key(event: Event) -> tuple[object, object, object] | None:
    """The ``(attempt, route, candidate)`` a TERMINAL record claims, or ``None`` when the
    event claims no final disposition.

    ONE definition serves both the dangling scan and the CAS precondition, so the rule that
    decides "this dispatch is resolved" cannot drift from the rule that decides "a second
    resolution is refused".

    The key is Attempt-scoped. Route ids are caller-supplied at this layer, so without the
    Attempt in the key a completion under A2 would suppress reconciliation of an identically
    keyed dangling dispatch under A1 — and 1B classifies failed Attempts from exactly this
    history."""
    if event.event_type not in ("DispatchCompleted", "DispatchUnknown") and not (
        event.event_type == "CandidateOutcome"
        and event.payload.get("outcome") in _TERMINAL_OUTCOMES
    ):
        return None
    return (event.attempt_id, event.payload.get("route_id"),
            event.payload.get("candidate_index"))


def _started_key(event: Event) -> tuple[object, object, object]:
    return (event.attempt_id, event.payload.get("route_id"),
            event.payload.get("candidate_index"))


def _jsonable(value: object) -> object:
    """A JSON-safe projection of one audit field.

    Unknown types RAISE rather than being coerced with ``str()``: this payload becomes
    immutable history, and a stringified repr nobody can parse is worse than a refusal.
    ``emit_audit`` turns that refusal into a route-fatal ``RouteAuditError``, which is the
    correct outcome for a mandatory sink that cannot faithfully record what it was given."""
    if isinstance(value, ModelRef):
        return {"backend": value.backend, "serving_endpoint": value.serving_endpoint,
                "model_id": value.model_id, "model_family": value.model_family,
                "vendor": value.vendor}
    if isinstance(value, SnapshotProvenance):
        return {"source": value.source, "observed_at": value.observed_at, "age_s": value.age_s}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError(
        f"audit field of type {type(value).__name__} has no JSON projection — refusing to "
        "write an unparseable value into append-only history"
    )


def _audit_payload(event: RouteAuditEvent) -> dict:
    """The event's fields, JSON-safe. The slice-0 ``event_id`` is carried as
    ``audit_event_id``: the lane envelope has its own ``event_id`` (a hash of this one),
    and two differently-scoped keys with the same name would be a trap for every reader."""
    if not is_dataclass(event):
        raise ValueError(f"audit event {type(event).__name__} is not a dataclass")
    payload = {f.name: _jsonable(getattr(event, f.name))
               for f in fields(event) if f.name != "event_id"}
    payload["audit_event_id"] = event.event_id
    return payload


def _refuse_second_terminal(
    lane_event: Event, key: tuple[object, object, object]
) -> Callable[[list[Event]], tuple[bool, str]]:
    """Admit a terminal record only if nothing else has already resolved this dispatch."""

    def _predicate(existing: list[Event]) -> tuple[bool, str]:
        # OUR OWN record first, across the whole stream: a byte-identical replay must stay
        # idempotent, and its own committed copy is itself a terminal record with this key,
        # so a naive clash scan would refuse the replay it is meant to allow.
        if any(e.event_id == lane_event.event_id for e in existing):
            return (True, "")
        clash = next((e for e in existing if _terminal_key(e) == key), None)
        if clash is not None:
            return (False, f"dispatch {key} is already resolved by {clash.event_type} "
                           f"{clash.event_id!r} — refusing a second terminal disposition")
        return (True, "")

    return _predicate


class EventStoreRouteAudit:
    """The lane's ``RouteAudit``: durable-on-commit, idempotent on a byte-identical replay,
    and fail-closed on a conflicting payload under the same audit ``event_id``."""

    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str, actor: str,
                 clock: Callable[[], str], config: LaneLogConfig | None = None) -> None:
        self._repo = repo
        self._problem_id = problem_id
        self._attempt_id = attempt_id
        self._actor = actor
        self._clock = clock
        self._config = config

    def _lane_event(self, event: RouteAuditEvent) -> Event:
        # The slice-0 event_id contains ':' and is not a safe path segment, so the lane id
        # is a hash of it. The ATTEMPT is part of that hash: the slice-0 id is
        # `route_id:candidate_index:kind` and route ids are caller-supplied at this layer,
        # so without it two Attempts sharing a route key would derive the SAME lane id with
        # different payloads — and the append-only guard would reject the second Attempt's
        # record outright. Attempt scoping has to hold in the STORAGE key, not only in the
        # queries over it. Revision anchors and seq are left unset — the store stamps them.
        return Event(
            event_id=derive_event_id(
                self._problem_id, f"audit\x00{self._attempt_id}\x00{event.event_id}"
            ),
            event_type=type(event).__name__, problem_id=self._problem_id, actor=self._actor,
            payload=_audit_payload(event), timestamp=self._clock(), attempt_id=self._attempt_id,
        )

    def record(self, event: RouteAuditEvent) -> None:
        """Persist one audit event. Returns only after the ref-CAS commit lands — that IS
        the durability point. A byte-identical replay is an idempotent success; a different
        payload under the same audit ``event_id`` raises (append-only violation), which
        ``emit_audit`` normalizes to a route-fatal ``RouteAuditError``.

        A TERMINAL record (``DispatchCompleted``, ``DispatchUnknown``, or a terminal
        ``CandidateOutcome``) additionally carries a precondition: it may land only if no
        OTHER terminal record already claims its ``(attempt, route, candidate)`` against the
        fresh CAS parent. Without it, a completion and a reconciliation reading the same
        parent would both append and leave two contradictory final dispositions for one
        dispatch — and 1B decides Attempt lifecycle from this history. Losing that race
        raises, which ``emit_audit`` makes route-fatal: a caller whose completion was
        refused must not proceed as though it had been recorded.

        Non-terminal records keep the plain unconditional append."""
        lane_event = self._lane_event(event)
        key = _terminal_key(lane_event)
        precondition = None if key is None else _refuse_second_terminal(lane_event, key)
        append(self._repo, lane_event, expected_revision=None, precondition=precondition,
               config=self._config)

    def claim_dispatch(self, event: DispatchStarted) -> bool:
        """Claim the dispatch boundary AND record the ``DispatchStarted`` in one CAS.

        ``True`` means this caller committed the record and owns the dispatch; ``False``
        means a byte-identical one was already committed, so the backend MUST NOT be
        invoked again. The ref-CAS makes exactly one claimant win ACROSS PROCESSES, not
        merely across threads — strictly stronger than an O_EXCL file boundary, and durable
        by construction. A conflicting payload under the same audit ``event_id`` raises."""
        return append(self._repo, self._lane_event(event), expected_revision=None,
                      config=self._config).created


def _require_instant(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{label} {value!r} must carry a timezone (an instant, not a date)")
    return parsed


#: Multiplies the worst-case call envelope before a dispatch may be called unknown. The
#: envelope covers the call itself; the margin covers queueing, process scheduling, and
#: clock skew between the runner that dispatched and the one reconciling.
RECONCILE_SAFETY_FACTOR = 2.0


def reconcile_timeout_s(*, deadline_s: float | None, retries: int) -> float:
    """THE reviewed way to derive a reconciliation timeout, from the envelope the lane's
    calls actually run under.

    A free-form number cannot establish "never before it could have finished" — that claim
    is only as good as its relationship to the real deadline and retry count, so the
    derivation lives here rather than at each call site.

    ``deadline_s=None`` RAISES: an unbounded call has no worst case, so no timeout can
    honestly assert the dispatch could not still be running. A caller in that position must
    decide what envelope its calls actually run under and pass it — the alternative would be
    a number that merely looks conservative."""
    if deadline_s is None:
        raise ValueError(
            "cannot derive a conservative reconciliation timeout from an unbounded call: "
            "deadline_s=None has no worst case, so no timeout establishes that a dispatch "
            "could not still be running. Pass the deadline the lane's calls actually use."
        )
    if isinstance(deadline_s, bool) or not isinstance(deadline_s, (int, float)):
        raise ValueError(f"deadline_s must be a number, got {deadline_s!r}")
    if not math.isfinite(deadline_s) or deadline_s <= 0:
        raise ValueError(f"deadline_s must be finite and > 0, got {deadline_s!r}")
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ValueError(f"retries must be a non-negative int, got {retries!r}")
    return deadline_s * (retries + 1) * RECONCILE_SAFETY_FACTOR


def _validated_timeout(timeout_s: float) -> float:
    """A timeout that can actually bound anything.

    Zero or negative would mark a dispatch unknown the instant it started — the exact
    opposite of the conservative guarantee the docstring promises — and a non-finite one
    makes every comparison against the cutoff meaningless. Prefer
    :func:`reconcile_timeout_s`, which derives the value from the real call envelope; this
    is the floor under any caller-supplied number."""
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise ValueError(f"timeout_s must be a number, got {timeout_s!r}")
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError(
            f"timeout_s must be finite and > 0, got {timeout_s!r} — a non-positive timeout "
            "marks a still-running dispatch unknown immediately"
        )
    return float(timeout_s)


def dangling_dispatches(events: list[Event], *, attempt_id: str, now: str,
                        timeout_s: float) -> list[dict]:
    """Dispatches for ``attempt_id`` with no recorded resolution, older than the timeout.

    ``timeout_s`` is a CONSERVATIVE TIMEOUT, not proof the owner is dead — derive it with
    :func:`reconcile_timeout_s` so it is tied to the real worst-case call envelope and a
    still-running valid call can never be marked before it could possibly have finished.
    Durable liveness would need an owner/run id and a lease-expiry on ``DispatchStarted`` —
    a protected-surface change, out of this slice's scope.

    A candidate is NOT dangling if it has a ``DispatchCompleted``, a terminal
    ``CandidateOutcome`` (a failed candidate is a KNOWN outcome), or an existing
    ``DispatchUnknown`` — each matched within THIS Attempt, never across Attempts."""
    cutoff = _require_instant(now, "now") - timedelta(seconds=_validated_timeout(timeout_s))
    # Terminal keys carry their own attempt_id, so membership below is Attempt-scoped by
    # construction: another Attempt's completion has a different key and cannot resolve
    # this Attempt's dispatch.
    resolved = {k for k in map(_terminal_key, events) if k is not None}
    return [
        dict(e.payload) for e in events
        if e.event_type == "DispatchStarted"
        and e.attempt_id == attempt_id
        and _started_key(e) not in resolved
        and _require_instant(e.timestamp, "dispatch timestamp") < cutoff
    ]


def reconcile_unknown(repo: Path, *, problem_id: str, attempt_id: str, actor: str,
                      clock: Callable[[], str], now: str, timeout_s: float,
                      config: LaneLogConfig | None = None) -> list[str]:
    """Mark every dangling dispatch unknown, returning the ``route_id``s reconciled.

    ONE event does both jobs: the audit projection sees the dispatch resolved as
    ``DispatchUnknown``, and ``project_reservations`` moves its reservation ``open →
    retained`` off the same record. Because it is a single append there is no crash window
    in which a dispatch is marked unknown but its credits were quietly released — the state
    where one exists without the other is unreachable, not merely unlikely.

    Idempotent: a byte-identical re-append is a no-op, and a second run finds nothing
    dangling.

    Losing the terminal CAS is a NORMAL outcome here, not an error: the dangling scan runs
    against one read, and a real completion can land before the mark does. That dispatch is
    then resolved — by the completion, correctly — so it is skipped and left out of the
    returned ids rather than forced or raised."""
    sink = EventStoreRouteAudit(repo=repo, problem_id=problem_id, attempt_id=attempt_id,
                                actor=actor, clock=clock, config=config)
    events = read(repo, problem_id, config=config)
    reconciled: list[str] = []
    for payload in dangling_dispatches(events, attempt_id=attempt_id, now=now,
                                       timeout_s=timeout_s):
        try:
            sink.record(DispatchUnknown(
                route_id=payload["route_id"], candidate_index=payload["candidate_index"],
                candidate=ModelRef(**payload["candidate"]),
                reservation_id=payload.get("reservation_id"),
            ))
        except LaneRevisionConflict:
            continue  # a real resolution won the race — it owns the disposition
        reconciled.append(payload["route_id"])
    return reconciled


__all__ = [
    "RECONCILE_SAFETY_FACTOR",
    "EventStoreRouteAudit",
    "dangling_dispatches",
    "reconcile_timeout_s",
    "reconcile_unknown",
]
