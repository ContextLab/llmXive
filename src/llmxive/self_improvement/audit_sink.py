"""The lane's durable ``RouteAudit`` (FR-033a) plus its unknown-dispatch reconciliation.

Every audit event lands on the protected lane ref through the same CAS as everything else.
That matters for ``claim_dispatch``: a bare local file that never reached the ref is NOT
durable evidence — a later commit failure would orphan it, and a replay would treat the
orphan as committed and refuse a dispatch whose evidence never persisted. Going through
``append_to_log`` means the outcome is returned ONLY after the ref moved.
"""

from __future__ import annotations

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
from llmxive.self_improvement.lane_log import LaneLogConfig, append, read

#: A candidate whose dispatch reached one of these outcomes has a KNOWN result. A failed
#: candidate is not an unknown one — only the absence of any resolution is.
_TERMINAL_OUTCOMES = frozenset({"advance", "abort", "skip"})


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
        # is a hash of it. Revision anchors and seq are left unset — the store stamps them.
        return Event(
            event_id=derive_event_id(self._problem_id, "audit\x00" + event.event_id),
            event_type=type(event).__name__, problem_id=self._problem_id, actor=self._actor,
            payload=_audit_payload(event), timestamp=self._clock(), attempt_id=self._attempt_id,
        )

    def record(self, event: RouteAuditEvent) -> None:
        """Persist one audit event. Returns only after the ref-CAS commit lands — that IS
        the durability point. A byte-identical replay is an idempotent success; a different
        payload under the same audit ``event_id`` raises (append-only violation), which
        ``emit_audit`` normalizes to a route-fatal ``RouteAuditError``.

        No retry loop: with ``expected_revision=None`` and no precondition the append has
        nothing that can be denied, so a ``LaneRevisionConflict`` is unreachable here.
        Sustained contention surfaces as ``GitLogContention`` from the core's own bounded
        retry, which is also route-fatal through ``emit_audit``."""
        append(self._repo, self._lane_event(event), expected_revision=None, config=self._config)

    def claim_dispatch(self, event: DispatchStarted) -> bool:
        """Claim the dispatch boundary AND record the ``DispatchStarted`` in one CAS.

        ``True`` means this caller committed the record and owns the dispatch; ``False``
        means a byte-identical one was already committed, so the backend MUST NOT be
        invoked again. The ref-CAS makes exactly one claimant win ACROSS PROCESSES, not
        merely across threads — strictly stronger than an O_EXCL file boundary, and durable
        by construction. A conflicting payload under the same audit ``event_id`` raises."""
        return append(self._repo, self._lane_event(event), expected_revision=None,
                      config=self._config).created


def _key(event: Event) -> tuple[object, object]:
    return (event.payload.get("route_id"), event.payload.get("candidate_index"))


def _require_instant(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{label} {value!r} must carry a timezone (an instant, not a date)")
    return parsed


def dangling_dispatches(events: list[Event], *, attempt_id: str, now: str,
                        timeout_s: float) -> list[dict]:
    """Dispatches for ``attempt_id`` with no recorded resolution, older than the timeout.

    ``timeout_s`` is a CONSERVATIVE TIMEOUT, not proof the owner is dead. Bound it by the
    real worst-case call envelope (``options.deadline_s * (retries + 1)`` plus a margin) so
    a still-running valid call can never be marked before it could possibly have finished.
    Durable liveness would need an owner/run id and a lease-expiry on ``DispatchStarted`` —
    a protected-surface change, out of this slice's scope.

    A candidate is NOT dangling if it has a ``DispatchCompleted``, a terminal
    ``CandidateOutcome`` (a failed candidate is a KNOWN outcome), or an existing
    ``DispatchUnknown``."""
    cutoff = _require_instant(now, "now") - timedelta(seconds=timeout_s)
    resolved: set[tuple[object, object]] = set()
    for e in events:
        if e.event_type in ("DispatchCompleted", "DispatchUnknown"):
            resolved.add(_key(e))
        elif e.event_type == "CandidateOutcome" and e.payload.get("outcome") in _TERMINAL_OUTCOMES:
            resolved.add(_key(e))
    return [
        dict(e.payload) for e in events
        if e.event_type == "DispatchStarted"
        and e.attempt_id == attempt_id
        and _key(e) not in resolved
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
    dangling."""
    sink = EventStoreRouteAudit(repo=repo, problem_id=problem_id, attempt_id=attempt_id,
                                actor=actor, clock=clock, config=config)
    events = read(repo, problem_id, config=config)
    reconciled: list[str] = []
    for payload in dangling_dispatches(events, attempt_id=attempt_id, now=now,
                                       timeout_s=timeout_s):
        sink.record(DispatchUnknown(
            route_id=payload["route_id"], candidate_index=payload["candidate_index"],
            candidate=ModelRef(**payload["candidate"]),
            reservation_id=payload.get("reservation_id"),
        ))
        reconciled.append(payload["route_id"])
    return reconciled


__all__ = [
    "EventStoreRouteAudit",
    "dangling_dispatches",
    "reconcile_unknown",
]
