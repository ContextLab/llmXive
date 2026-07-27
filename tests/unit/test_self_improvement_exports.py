"""Slice 1A package exports (the plan's final-verification item)."""
import llmxive.self_improvement as si

EXPECTED = [
    "Event", "derive_event_id", "validate_lane_event", "LANE_REF", "append", "read",
    "LaneRevisionConflict", "LaneContention", "LaneCoordinator", "project_coordinator",
    "cas_claim", "cas_release", "AttemptCreditLedger", "AttemptConfig",
    "AttemptConfigMismatch", "bind_attempt_config", "load_attempt_config",
    "require_attempt_config", "LaneCallLedger", "LaneCallCeilingExceeded",
    "derive_route_id", "project_call_claims", "EventStoreRouteAudit", "reconcile_unknown",
]

def test_every_planned_export_is_importable():
    missing = [n for n in EXPECTED if not hasattr(si, n)]
    assert not missing, f"missing exports: {missing}"

def test_all_matches_the_module_namespace():
    assert not [n for n in si.__all__ if not hasattr(si, n)]
