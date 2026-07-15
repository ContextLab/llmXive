import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver_utils import parse_intent, match_constraint


@dataclass
class ResolutionLog:
    """Log entry for a constraint resolution attempt."""
    constraint_id: str
    intent_text: str
    matched_constraint: Optional[str]
    is_violation: bool
    resolution_type: str  # "exact", "substring", "negation", "miss"
    confidence: float = 1.0


class ConstraintResolver:
    """
    Resolves generated intent text against active constraints in the store.
    Detects violations and logs resolution attempts.
    """

    def __init__(self, store: ConstraintStore):
        self.store = store
        self.logs: List[ResolutionLog] = []

    def resolve(self, intent_text: str, context: TaskContext) -> Tuple[bool, List[ResolutionLog]]:
        """
        Resolve an intent string against the current constraint store.

        Returns:
            Tuple of (is_violation_detected, list_of_resolution_logs)
        """
        logs = []
        is_violation = False

        # Parse the intent to extract structured components
        parsed = parse_intent(intent_text)

        if not parsed:
            # Failed to parse intent - log as false_negative per FR-008
            logs.append(ResolutionLog(
                constraint_id="UNKNOWN",
                intent_text=intent_text,
                matched_constraint=None,
                is_violation=False,
                resolution_type="parse_failure",
                confidence=0.0
            ))
            return False, logs

        # Check against all active constraints
        for constraint in self.store.get_active_constraints():
            match_result = match_constraint(parsed, constraint)
            
            if match_result["matched"]:
                logs.append(ResolutionLog(
                    constraint_id=constraint.id,
                    intent_text=intent_text,
                    matched_constraint=constraint.text,
                    is_violation=match_result["is_violation"],
                    resolution_type=match_result["match_type"],
                    confidence=match_result["confidence"]
                ))
                
                if match_result["is_violation"]:
                    is_violation = True
                    # Log the violation to the store
                    self.store.log_violation(
                        constraint_id=constraint.id,
                        intent_text=intent_text,
                        resolution_type=match_result["match_type"]
                    )
            else:
                # No match for this constraint
                logs.append(ResolutionLog(
                    constraint_id=constraint.id,
                    intent_text=intent_text,
                    matched_constraint=None,
                    is_violation=False,
                    resolution_type="no_match",
                    confidence=0.0
                ))

        self.logs.extend(logs)
        return is_violation, logs

    def get_logs(self) -> List[ResolutionLog]:
        """Return all resolution logs collected so far."""
        return self.logs


def main():
    """
    Standalone entry point for testing the resolver.
    Reads a sample task and constraint set, runs resolution, prints results.
    """
    import json
    import sys
    from pathlib import Path

    # Simple test harness
    test_data = {
        "intent": "Place the red block on the blue table",
        "constraints": [
            {"id": "c1", "text": "Do not place red objects on blue surfaces", "active": True},
            {"id": "c2", "text": "Only use green objects", "active": True}
        ]
    }

    store = ConstraintStore()
    for c in test_data["constraints"]:
        store.add_constraint(
            id=c["id"],
            text=c["text"],
            is_active=c["active"]
        )

    resolver = ConstraintResolver(store)
    context = TaskContext(task_id="test-001", current_step=1)
    
    is_violation, logs = resolver.resolve(test_data["intent"], context)
    
    print(f"Intent: {test_data['intent']}")
    print(f"Violation Detected: {is_violation}")
    print("Resolution Logs:")
    for log in logs:
        print(f"  - Constraint {log.constraint_id}: {log.resolution_type} "
              f"(violation: {log.is_violation}, confidence: {log.confidence:.2f})")

    if is_violation:
        print("\n[OK] Violation correctly detected for constraint c1.")
        sys.exit(0)
    else:
        print("\n[FAIL] Violation not detected as expected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
