"""Real in-memory ``RouteAudit`` sinks shared by the model-selection tests."""

from __future__ import annotations


class FailingRecorder:
    """A REAL in-memory RouteAudit sink that raises on a chosen set of event
    types (matched by class name) and records every other event — used to
    exercise the mandatory outbox's route-fatal (pre-dispatch) / fail-closed
    (post-dispatch) rules without mocking the sink itself."""
    def __init__(self, fail_on: set[str]):
        self.fail_on = fail_on
        self.events: list = []

    def record(self, event) -> None:
        if type(event).__name__ in self.fail_on:
            raise RuntimeError(f"simulated route_audit sink failure on {type(event).__name__}")
        self.events.append(event)

    def dispatch_claimed(self, event) -> bool:
        """Read-only: a DispatchStarted with this event id was already recorded."""
        return any(type(e).__name__ == "DispatchStarted" and e.event_id == event.event_id
                   for e in self.events)

    def claim_dispatch(self, event) -> bool:
        if "DispatchStarted" in self.fail_on:
            raise RuntimeError("simulated route_audit sink failure on DispatchStarted")
        self.events.append(event)
        return True


class ClaimOnceRecorder:
    """A REAL in-memory RouteAudit sink keyed by event id alone: ``record`` keeps every
    event, ``claim_dispatch`` returns ``True`` the first time an event id is claimed and
    ``False`` after (whatever the payload) — the shape of a sink that detects a replayed
    route by its dispatch boundary."""

    def __init__(self):
        self.events: list = []
        self._claimed: set[str] = set()

    def record(self, event) -> None:
        self.events.append(event)

    def dispatch_claimed(self, event) -> bool:
        return event.event_id in self._claimed

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        if event.event_id in self._claimed:
            return False
        self._claimed.add(event.event_id)
        return True
