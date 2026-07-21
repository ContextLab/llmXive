"""
Constraint Resolver Module.

This module orchestrates the resolution of constraints by delegating
intent parsing and constraint matching to dedicated utility modules.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver_utils import parse_intent, match_constraint


@dataclass
class ResolutionLog:
    """Log entry for a constraint resolution attempt."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    task_id: str = ""
    constraint_id: str = ""
    plan_step: str = ""
    matched: bool = False
    reason: Optional[str] = None
    violation_type: Optional[ViolationType] = None


class ConstraintResolver:
    """
    Resolves constraints against generated plan steps.

    This class acts as the orchestrator for constraint checking. It uses
    `parse_intent` to extract potential constraint targets from a plan step
    and `match_constraint` to verify if the step satisfies the active constraints.
    """

    def __init__(self, negation_patterns: Optional[List[str]] = None):
        """
        Initialize the resolver.

        Args:
            negation_patterns: List of regex patterns or strings indicating negation.
        """
        self.negation_patterns = negation_patterns or [
            r"\bnot\b", r"\bno\b", r"\bnever\b", r"\bdon't\b",
            r"\bdo not\b", r"\bavoid\b", r"\bwithout\b"
        ]
        self.logs: List[ResolutionLog] = []

    def resolve_step(
        self,
        step: str,
        active_constraints: List[Constraint],
        task_id: str
    ) -> List[ResolutionLog]:
        """
        Resolve a single plan step against a list of active constraints.

        Args:
            step: The generated plan step string.
            active_constraints: List of constraints currently active for the task.
            task_id: The ID of the current task.

        Returns:
            A list of ResolutionLog entries for each constraint checked.
        """
        step_logs = []

        # Parse intent to see if we can identify specific constraint targets
        intent = parse_intent(step)

        for constraint in active_constraints:
            is_matched, reason = match_constraint(
                constraint,
                step,
                self.negation_patterns
            )

            log_entry = ResolutionLog(
                task_id=task_id,
                constraint_id=constraint.id,
                plan_step=step,
                matched=is_matched,
                reason=reason
            )

            if not is_matched:
                log_entry.violation_type = ViolationType.CONSTRAINT_VIOLATION

            step_logs.append(log_entry)
            self.logs.append(log_entry)

        return step_logs

    def get_violations(self) -> List[ResolutionLog]:
        """Return all logs that represent violations."""
        return [log for log in self.logs if log.violation_type is not None]


def main():
    """CLI entry point for testing the resolver."""
    print("Constraint Resolver Module loaded successfully.")
    print("Use ConstraintResolver class to resolve steps against constraints.")

    # Example usage
    store = ConstraintStore()
    store.add_constraint("Do not touch the red button", "c1")
    store.add_constraint("Pick up the blue key", "c2")

    resolver = ConstraintResolver()
    step = "I will pick up the blue key carefully."
    logs = resolver.resolve_step(step, list(store.constraints.values()), "task-001")

    for log in logs:
        print(f"Constraint: {log.constraint_id} -> Matched: {log.matched}, Reason: {log.reason}")


if __name__ == "__main__":
    main()