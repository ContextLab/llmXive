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

    def claim_dispatch(self, event) -> bool:
        if "DispatchStarted" in self.fail_on:
            raise RuntimeError("simulated route_audit sink failure on DispatchStarted")
        self.events.append(event)
        return True
