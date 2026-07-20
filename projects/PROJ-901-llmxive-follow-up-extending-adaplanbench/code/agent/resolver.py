import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver_utils import parse_intent, match_constraint

@dataclass
class ResolutionLog:
    """Log entry for constraint resolution events."""
    constraint_id: str
    constraint_text: str
    resolution_status: str  # 'resolved', 'violation', 'implicit_unverified'
    reason: str
    timestamp: float = field(default_factory=lambda: 0.0)
    is_implicit: bool = False

class ConstraintResolver:
    """
    Resolves constraints against generated plans.
    
    Implements FR-007: Exact string matching, case-insensitive substring matching,
    and explicit negation patterns.
    
    Implements FR-009: Logs "implicit_unverified" for constraints requiring
    common-sense reasoning, excluding them from primary violation rate.
    """
    
    def __init__(self):
        self.logs: List[ResolutionLog] = []
        # Patterns that indicate common-sense/implicit reasoning requirements
        # These are typically vague, context-dependent, or require world knowledge
        self.implicit_patterns = [
            r'\b(reasonable|appropriate|suitable|suitably)\b',
            r'\b(common\s*sense|practical|logical)\b',
            r'\b(typical|standard|normal)\b',
            r'\b(consider|take\s*into\s*account)\b',
            r'\b(ensure\s*that|make\s*sure)\b',
            r'\b(avoid\s*unnecessary|minimize\s*effort)\b',
        ]
        self.implicit_regex = [re.compile(p, re.IGNORECASE) for p in self.implicit_patterns]

    def _is_implicit_constraint(self, constraint_text: str) -> bool:
        """
        Determine if a constraint requires common-sense reasoning.
        
        Returns True if the constraint text matches patterns indicating
        vague, context-dependent, or world-knowledge requirements.
        """
        for regex in self.implicit_regex:
            if regex.search(constraint_text):
                return True
        return False

    def resolve_constraint(
        self,
        constraint: Constraint,
        plan_text: str,
        context: TaskContext
    ) -> ResolutionLog:
        """
        Resolve a single constraint against a generated plan.
        
        Returns a ResolutionLog indicating:
        - 'resolved': Constraint satisfied
        - 'violation': Constraint explicitly violated
        - 'implicit_unverified': Constraint requires common-sense reasoning,
          excluded from primary violation rate
        """
        constraint_text = constraint.text
        
        # Check if this is an implicit/common-sense constraint (FR-009)
        if self._is_implicit_constraint(constraint_text):
            log_entry = ResolutionLog(
                constraint_id=constraint.id,
                constraint_text=constraint_text,
                resolution_status='implicit_unverified',
                reason='Constraint requires common-sense reasoning or world knowledge',
                is_implicit=True
            )
            self.logs.append(log_entry)
            return log_entry
        
        # Try exact match first (case-sensitive)
        if constraint_text in plan_text:
            log_entry = ResolutionLog(
                constraint_id=constraint.id,
                constraint_text=constraint_text,
                resolution_status='resolved',
                reason='Exact match found in plan'
            )
            self.logs.append(log_entry)
            return log_entry
        
        # Try case-insensitive substring match
        if constraint_text.lower() in plan_text.lower():
            log_entry = ResolutionLog(
                constraint_id=constraint.id,
                constraint_text=constraint_text,
                resolution_status='resolved',
                reason='Case-insensitive match found in plan'
            )
            self.logs.append(log_entry)
            return log_entry
        
        # Check for explicit negation patterns (e.g., "do not", "never", "avoid")
        negation_pattern = r'\b(do\s+not|dont|never|avoid|without)\b'
        if re.search(negation_pattern, constraint_text, re.IGNORECASE):
            # For negation constraints, we look for the ABSENCE of the forbidden element
            # Extract the forbidden element (simplified heuristic)
            forbidden_match = re.search(negation_pattern + r'\s+(.+?)(?:\.|$)', constraint_text, re.IGNORECASE)
            if forbidden_match:
                forbidden_element = forbidden_match.group(1).strip()
                if forbidden_element.lower() not in plan_text.lower():
                    log_entry = ResolutionLog(
                        constraint_id=constraint.id,
                        constraint_text=constraint_text,
                        resolution_status='resolved',
                        reason='Negation constraint satisfied (forbidden element absent)'
                    )
                    self.logs.append(log_entry)
                    return log_entry
        
        # If no match found, it's a violation
        log_entry = ResolutionLog(
            constraint_id=constraint.id,
            constraint_text=constraint_text,
            resolution_status='violation',
            reason='Constraint not found in plan'
        )
        self.logs.append(log_entry)
        return log_entry

    def resolve_all(
        self,
        constraints: List[Constraint],
        plan_text: str,
        context: TaskContext
    ) -> List[ResolutionLog]:
        """Resolve all constraints against a plan."""
        return [self.resolve_constraint(c, plan_text, context) for c in constraints]

    def get_violation_rate(self) -> float:
        """
        Calculate violation rate excluding implicit_unverified constraints.
        
        Per FR-009, implicit_unverified constraints are excluded from the
        primary violation rate calculation.
        """
        total_resolved = len([l for l in self.logs if l.resolution_status in ('resolved', 'violation')])
        if total_resolved == 0:
            return 0.0
        
        violations = len([l for l in self.logs if l.resolution_status == 'violation'])
        return violations / total_resolved

    def get_implicit_count(self) -> int:
        """Return count of implicit_unverified constraints."""
        return len([l for l in self.logs if l.resolution_status == 'implicit_unverified'])

    def clear_logs(self):
        """Clear all resolution logs."""
        self.logs.clear()

def main():
    """CLI entry point for testing constraint resolver."""
    import sys
    from agent.constraint_store import ConstraintStore
    
    # Create a simple test case
    store = ConstraintStore()
    
    # Add a mix of explicit and implicit constraints
    store.add_constraint("Place the book on the table")  # Explicit
    store.add_constraint("Do not touch the vase")       # Explicit negation
    store.add_constraint("Ensure the room is reasonably tidy")  # Implicit
    store.add_constraint("Make sure the task is completed logically")  # Implicit
    
    # Test plan
    plan = "I will place the book on the table and avoid touching the vase."
    
    resolver = ConstraintResolver()
    context = TaskContext(task_id="test-001", constraints=store.get_active_constraints())
    
    results = resolver.resolve_all(store.get_active_constraints(), plan, context)
    
    print("Resolution Results:")
    for log in results:
        print(f"  [{log.resolution_status}] {log.constraint_text[:40]}...")
    
    print(f"\nViolation Rate (excluding implicit): {resolver.get_violation_rate():.2%}")
    print(f"Implicit/Unverified Constraints: {resolver.get_implicit_count()}")
    
    return results

if __name__ == "__main__":
    main()
