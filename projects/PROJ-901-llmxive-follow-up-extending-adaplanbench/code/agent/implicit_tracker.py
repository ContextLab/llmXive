"""
Implicit Constraint Tracker (FR-009)

Implements logic to identify constraints requiring common-sense reasoning,
logging them as 'implicit_unverified' and excluding them from the primary
violation rate calculation.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore


@dataclass
class ImplicitLog:
    """Log entry for an implicit/unverified constraint."""
    id: str
    task_id: str
    constraint_text: str
    reasoning_category: str  # e.g., 'common_sense', 'physical_law', 'social_norm'
    timestamp: str
    excluded_from_violation_rate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "constraint_text": self.constraint_text,
            "reasoning_category": self.reasoning_category,
            "timestamp": self.timestamp,
            "excluded_from_violation_rate": self.excluded_from_violation_rate
        }


class ImplicitConstraintTracker:
    """
    Tracks constraints that require common-sense reasoning.
    
    FR-009: Constraints requiring common-sense reasoning are logged as
    'implicit_unverified' and excluded from the primary violation rate.
    """
    
    # Heuristic keywords that often indicate common-sense reasoning
    # These are not exhaustive but serve as initial indicators
    COMMONSENSE_INDICATORS = [
        "obviously", "naturally", "typically", "usually", "generally",
        "common sense", "intuitively", "standard practice", "normal",
        "expected", "assumed", "implied", "understood", "without saying"
    ]
    
    # Context patterns that suggest implicit constraints
    IMPLICIT_PATTERNS = [
        "without explicitly stating", "assuming", "given that", "since",
        "because", "as a result of", "in order to", "so that", "therefore"
    ]

    def __init__(self):
        self.implicit_logs: List[ImplicitLog] = []
        self.processed_constraints: set = set()

    def _detect_commonsense_requirement(self, constraint: Constraint, context: Optional[TaskContext]) -> Tuple[bool, str]:
        """
        Detects if a constraint likely requires common-sense reasoning.
        
        Returns:
            Tuple of (is_implicit, reasoning_category)
        """
        text = constraint.text.lower()
        category = "unknown"
        
        # Check for explicit common-sense indicators
        for indicator in self.COMMONSENSE_INDICATORS:
            if indicator in text:
                category = "explicit_commonsense"
                return True, category
        
        # Check for implicit patterns that suggest unstated assumptions
        for pattern in self.IMPLICIT_PATTERNS:
            if pattern in text:
                category = "implicit_assumption"
                return True, category
        
        # Check for physical world constraints that might be common-sense
        physical_keywords = ["heavy", "fragile", "break", "spill", "drop", "heat", "cold", "wet", "dry"]
        if any(kw in text for kw in physical_keywords):
            category = "physical_commonsense"
            return True, category
        
        # Check for social norms
        social_keywords = ["polite", "rude", "appropriate", "inappropriate", "acceptable", "unacceptable", "respect", "privacy"]
        if any(kw in text for kw in social_keywords):
            category = "social_commonsense"
            return True, category
        
        # Check for temporal reasoning that might be implicit
        temporal_keywords = ["before", "after", "during", "while", "until", "by the time", "once"]
        if any(kw in text for kw in temporal_keywords) and "explicitly" not in text:
            category = "temporal_commonsense"
            return True, category
        
        return False, category

    def track_constraint(self, constraint: Constraint, task_context: TaskContext) -> Optional[ImplicitLog]:
        """
        Evaluate a constraint and log it if it requires common-sense reasoning.
        
        Args:
            constraint: The constraint to evaluate
            task_context: Context of the current task execution
        
        Returns:
            ImplicitLog if the constraint is implicit, None otherwise
        """
        # Avoid duplicate logging
        constraint_id = f"{task_context.task_id}_{constraint.id}"
        if constraint_id in self.processed_constraints:
            return None
        
        self.processed_constraints.add(constraint_id)
        
        is_implicit, category = self._detect_commonsense_requirement(constraint, task_context)
        
        if is_implicit:
            log_entry = ImplicitLog(
                id=str(uuid.uuid4()),
                task_id=task_context.task_id,
                constraint_text=constraint.text,
                reasoning_category=category,
                timestamp=datetime.now().isoformat(),
                excluded_from_violation_rate=True
            )
            self.implicit_logs.append(log_entry)
            return log_entry
        
        return None

    def get_implicit_count(self) -> int:
        """Return the count of implicit constraints identified."""
        return len(self.implicit_logs)

    def get_implicit_logs(self) -> List[Dict[str, Any]]:
        """Return all implicit constraint logs as dictionaries."""
        return [log.to_dict() for log in self.implicit_logs]

    def clear_logs(self):
        """Clear all logs and reset state."""
        self.implicit_logs = []
        self.processed_constraints = set()

    def calculate_adjusted_violation_rate(
        self, 
        total_constraints: int, 
        violation_count: int,
        implicit_count: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate violation rates with and without implicit constraints.
        
        Args:
            total_constraints: Total number of constraints evaluated
            violation_count: Number of violations detected
            implicit_count: Number of implicit constraints (if None, uses internal count)
        
        Returns:
            Dictionary with both raw and adjusted violation rates
        """
        if implicit_count is None:
            implicit_count = self.get_implicit_count()
        
        # Raw rate includes all constraints
        raw_rate = violation_count / total_constraints if total_constraints > 0 else 0.0
        
        # Adjusted rate excludes implicit constraints from the denominator
        # and assumes implicit constraints don't count as violations for the primary metric
        adjusted_denominator = total_constraints - implicit_count
        adjusted_rate = violation_count / adjusted_denominator if adjusted_denominator > 0 else 0.0
        
        return {
            "raw_violation_rate": raw_rate,
            "adjusted_violation_rate": adjusted_rate,
            "implicit_constraints_excluded": implicit_count,
            "total_constraints": total_constraints,
            "violations": violation_count
        }

def main():
    """
    Standalone test/demo of the ImplicitConstraintTracker.
    This function demonstrates the tracker's functionality with sample data.
    """
    from agent.constraint_store import ConstraintStore
    
    # Create a sample task context
    context = TaskContext(
        task_id="demo_task_001",
        initial_plan="Organize the kitchen",
        constraints=[],
        execution_status="running"
    )
    
    # Create tracker
    tracker = ImplicitConstraintTracker()
    
    # Create sample constraints
    sample_constraints = [
        Constraint(
            id="c1",
            text="Make sure to wash your hands before handling food",
            source="user",
            is_active=True,
            created_at=datetime.now().isoformat()
        ),
        Constraint(
            id="c2",
            text="Don't leave the stove on unattended - it's obviously dangerous",
            source="system",
            is_active=True,
            created_at=datetime.now().isoformat()
        ),
        Constraint(
            id="c3",
            text="Put the milk in the refrigerator",
            source="user",
            is_active=True,
            created_at=datetime.now().isoformat()
        ),
        Constraint(
            id="c4",
            text="Ensure the room is tidy, as is standard practice",
            source="system",
            is_active=True,
            created_at=datetime.now().isoformat()
        ),
        Constraint(
            id="c5",
            text="Break the glass if emergency",
            source="user",
            is_active=True,
            created_at=datetime.now().isoformat()
        )
    ]
    
    # Process each constraint
    for constraint in sample_constraints:
        log = tracker.track_constraint(constraint, context)
        if log:
            print(f"Logged implicit constraint: {log.constraint_text[:50]}... ({log.reasoning_category})")
        else:
            print(f"Regular constraint: {constraint.text[:50]}...")
    
    # Calculate rates
    stats = tracker.calculate_adjusted_violation_rate(
        total_constraints=len(sample_constraints),
        violation_count=1  # Simulate 1 violation
    )
    
    print("\nViolation Rate Analysis:")
    print(f"Raw Rate: {stats['raw_violation_rate']:.2%}")
    print(f"Adjusted Rate (excluding {stats['implicit_constraints_excluded']} implicit): {stats['adjusted_violation_rate']:.2%}")
    
    # Return results for verification
    return {
        "implicit_count": tracker.get_implicit_count(),
        "stats": stats,
        "logs": tracker.get_implicit_logs()
    }

if __name__ == "__main__":
    main()