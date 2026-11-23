"""
Constraint Resolver Module.

This module orchestrates the resolution of constraints by delegating
intent parsing and constraint matching to dedicated utility modules.
It also implements the state transition and logging logic for FR-008 and FR-009.
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
    # FR-008 / FR-009 Status fields
    violation_status: Optional[str] = None  # "false_negative", "implicit_unverified", or null


class ConstraintResolver:
    """
    Resolves constraints against generated plan steps.

    This class acts as the orchestrator for constraint checking. It uses
    `parse_intent` to extract potential constraint targets from a plan step
    and `match_constraint` to verify if the step satisfies the active constraints.

    It implements FR-007 (matching logic), FR-008 (False Negative handling),
    and FR-009 (Implicit/Unverified handling).
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

        Logic:
        1. Attempt to parse intent. If parsing fails (returns None or empty),
           log as FR-008 (false_negative) and retain original plan (do not flag violation).
        2. If parsing succeeds, attempt to match constraints.
        3. If a constraint is not matched, check if it is implicit (FR-009).
           If implicit, log as "implicit_unverified" and set violation_boolean=false.
        4. Otherwise, log as standard CONSTRAINT_VIOLATION.

        Args:
            step: The generated plan step string.
            active_constraints: List of constraints currently active for the task.
            task_id: The ID of the current task.

        Returns:
            A list of ResolutionLog entries for each constraint checked.
        """
        step_logs = []

        # FR-008: Check for parsing failure
        intent = parse_intent(step)
        if intent is None or (isinstance(intent, dict) and len(intent) == 0):
            # Parsing failed. Log as false_negative.
            # We do not check constraints because we cannot identify targets.
            # Per FR-008: "retain the original plan" -> do not mark violation.
            log_entry = ResolutionLog(
                task_id=task_id,
                constraint_id="N/A",
                plan_step=step,
                matched=False,
                reason="Intent parsing failed",
                violation_type=None,  # Not a violation per FR-008
                violation_status="false_negative"
            )
            step_logs.append(log_entry)
            self.logs.append(log_entry)
            return step_logs

        # If intent parsing succeeded, proceed with matching
        for constraint in active_constraints:
            is_matched, reason = match_constraint(
                constraint,
                step,
                self.negation_patterns
            )

            violation_type = None
            violation_status = None

            if not is_matched:
                # Check for implicit constraint (FR-009)
                # We consider it implicit if the constraint text contains keywords
                # suggesting it's not a direct action or if the reason suggests ambiguity.
                # For now, we rely on the match_constraint reason or a heuristic on the constraint text.
                is_implicit = self._is_likely_implicit(constraint, reason)

                if is_implicit:
                    # FR-009: Implicit or pattern fails to match -> log "implicit_unverified"
                    violation_type = ViolationType.CONSTRAINT_VIOLATION # Technically a potential violation
                    violation_status = "implicit_unverified"
                    # Per FR-009: "set violation_boolean to false" (matched=False)
                    # and "flag for human review" (handled by status field)
                else:
                    # Standard violation
                    violation_type = ViolationType.CONSTRAINT_VIOLATION
                    violation_status = None
            else:
                # Matched successfully
                violation_type = None
                violation_status = None

            log_entry = ResolutionLog(
                task_id=task_id,
                constraint_id=constraint.id,
                plan_step=step,
                matched=is_matched,
                reason=reason,
                violation_type=violation_type,
                violation_status=violation_status
            )

            step_logs.append(log_entry)
            self.logs.append(log_entry)

        return step_logs

    def _is_likely_implicit(self, constraint: Constraint, reason: Optional[str]) -> bool:
        """
        Heuristic to determine if a constraint is implicit or unverified.
        Returns True if the constraint seems to require external context or
        if the matching reason suggests ambiguity.
        """
        # Heuristic 1: Check constraint text for "should", "might", "consider"
        text = constraint.text.lower()
        if any(word in text for word in ["should", "might", "consider", "prefer", "ideally"]):
            return True

        # Heuristic 2: Check if reason indicates ambiguity
        if reason and any(word in reason.lower() for word in ["ambiguous", "partial", "unclear"]):
            return True

        return False

    def get_violations(self) -> List[ResolutionLog]:
        """Return all logs that represent violations (excluding implicit_unverified)."""
        return [log for log in self.logs if log.violation_type is not None and log.violation_status != "implicit_unverified"]

    def get_implicit_logs(self) -> List[ResolutionLog]:
        """Return all logs flagged as implicit/unverified."""
        return [log for log in self.logs if log.violation_status == "implicit_unverified"]

    def get_false_negative_logs(self) -> List[ResolutionLog]:
        """Return all logs flagged as false_negative (parsing failure)."""
        return [log for log in self.logs if log.violation_status == "false_negative"]


def main():
    """CLI entry point for testing the resolver."""
    print("Constraint Resolver Module loaded successfully.")
    print("Use ConstraintResolver class to resolve steps against constraints.")

    # Example usage
    store = ConstraintStore()
    store.add_constraint("Do not touch the red button", "c1")
    store.add_constraint("Pick up the blue key", "c2")
    store.add_constraint("The door should be locked", "c3") # Implicit example

    resolver = ConstraintResolver()
    step = "I will pick up the blue key carefully."
    logs = resolver.resolve_step(step, list(store.constraints.values()), "task-001")

    for log in logs:
        print(f"Constraint: {log.constraint_id} -> Matched: {log.matched}, "
              f"Status: {log.violation_status}, Type: {log.violation_type}")


if __name__ == "__main__":
    main()