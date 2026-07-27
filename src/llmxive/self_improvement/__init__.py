"""The autonomous self-improvement lane (spec 025). Slice 1A: durable substrate.

Everything the lane does that must survive a crash — ownership of the singleton
coordinator, the per-Attempt credit budget, the per-Attempt call ceiling, and the route
audit trail — lives in ONE append-only log on a dedicated protected ref, mutated only
through compare-and-swap. Nothing here holds safety state in process memory.
"""

from llmxive.self_improvement.attempt_config import (
    AttemptConfig,
    AttemptConfigMismatch,
    bind_attempt_config,
    load_attempt_config,
    require_attempt_config,
)
from llmxive.self_improvement.audit_sink import (
    EventStoreRouteAudit,
    dangling_dispatches,
    reconcile_unknown,
)
from llmxive.self_improvement.call_ledger import (
    CallClaim,
    LaneCallCeilingExceeded,
    LaneCallLedger,
    project_call_claims,
)
from llmxive.self_improvement.coordinator import (
    EMPTY_COORDINATOR,
    LaneCoordinator,
    cas_claim,
    cas_release,
    project_coordinator,
)
from llmxive.self_improvement.credit_ledger import (
    AttemptCreditLedger,
    AttemptReservation,
    counting_total,
    project_reservations,
)
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    Event,
    derive_event_id,
    derive_route_id,
    validate_lane_event,
)
from llmxive.self_improvement.lane_log import (
    LANE_REF,
    LaneContention,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    bootstrap_lane_log,
    read,
)

__all__ = [
    "COORDINATOR_STREAM",
    "EMPTY_COORDINATOR",
    "LANE_REF",
    "AttemptConfig",
    "AttemptConfigMismatch",
    "AttemptCreditLedger",
    "AttemptReservation",
    "CallClaim",
    "Event",
    "EventStoreRouteAudit",
    "LaneCallCeilingExceeded",
    "LaneCallLedger",
    "LaneContention",
    "LaneCoordinator",
    "LaneLogConfig",
    "LaneRevisionConflict",
    "append",
    "bind_attempt_config",
    "bootstrap_lane_log",
    "cas_claim",
    "cas_release",
    "counting_total",
    "dangling_dispatches",
    "derive_event_id",
    "derive_route_id",
    "load_attempt_config",
    "project_call_claims",
    "project_coordinator",
    "project_reservations",
    "read",
    "reconcile_unknown",
    "require_attempt_config",
    "validate_lane_event",
]
