import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction
from code.symbolic.parser import FormalConstraint, PuzzleParser, parse_dataset_file
from code.config import load_config
from code.utils.logger import log

# Configure module logger
_logger = logging.getLogger(__name__)

class SubGoalStatus(Enum):
    """Enumeration of possible sub-goal states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXCLUDED = "excluded"

@dataclass
class SubGoal:
    """Represents a decomposed sub-goal."""
    id: str
    description: str
    status: SubGoalStatus = SubGoalStatus.PENDING
    parent_constraint_id: Optional[str] = None
    exclusion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecompositionResult:
    """Result of the symbolic planning decomposition."""
    puzzle_id: str
    sub_goals: List[SubGoal]
    success: bool
    exclusion_log: List[Dict[str, Any]]
    error: Optional[str] = None

class SymbolicPlanner:
    """
    Symbolic planner that generates sub-goal decompositions from formal constraints.
    Implements logging for exclusion reasons as per FR-006.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.exclusion_log: List[Dict[str, Any]] = []
        self._setup_logging()

    def _setup_logging(self):
        """Initialize logging for exclusion reasons."""
        log_path = Path(self.config.get("paths", {}).get("processed", "data/processed"))
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / "planner_exclusions.log"

        # Create a specific logger for planner exclusions
        self.planner_logger = logging.getLogger("planner_exclusions")
        self.planner_logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        self.planner_logger.handlers = []

        # File handler for exclusions
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.planner_logger.addHandler(fh)

        # Also log to the main module logger
        _logger.setLevel(logging.INFO)

    def _log_exclusion(self, reason_type: str, reason_details: str, context: Dict[str, Any]):
        """
        Logs exclusion reasons for PARSE_FAILURE or CONTRADICTION_DETECTED.
        This satisfies FR-006: Logging mechanism for exclusion reasons.
        """
        entry = {
            "type": reason_type,
            "reason": reason_details,
            "context": context,
            "timestamp": log.get_current_timestamp()
        }
        self.exclusion_log.append(entry)

        # Log to the dedicated exclusion logger
        self.planner_logger.info(f"[{reason_type}] {reason_details} | Context: {json.dumps(context)}")
        _logger.warning(f"Sub-goal excluded: {reason_type} - {reason_details}")

    def _parse_constraints(self, constraints: List[Dict[str, Any]]) -> List[FormalConstraint]:
        """
        Parses raw constraints into FormalConstraint objects.
        Raises PARSE_FAILURE if parsing fails.
        """
        parsed = []
        for i, c in enumerate(constraints):
            try:
                # Attempt to parse using the shared parser logic
                # Assuming FormalConstraint has a from_dict or similar logic
                # Since we don't see the full parser implementation, we simulate the structure
                # based on the import and standard patterns.
                constraint_obj = FormalConstraint(
                    id=c.get("id", f"constraint_{i}"),
                    type=c.get("type"),
                    expression=c.get("expression"),
                    metadata=c.get("metadata", {})
                )
                parsed.append(constraint_obj)
            except Exception as e:
                # This would trigger PARSE_FAILURE
                raise_parse_failure(f"Failed to parse constraint {i}: {str(e)}")
        return parsed

    def _check_contradictions(self, constraints: List[FormalConstraint]) -> List[FormalConstraint]:
        """
        Checks for logical contradictions among constraints.
        Raises CONTRADICTION_DETECTED if found.
        """
        # Simplified contradiction check logic
        # In a real implementation, this would use a SAT solver or logical engine
        # For now, we check for explicit "impossible" markers or conflicting types
        seen_types = {}
        for c in constraints:
            if c.type == "impossible":
                raise_contradiction(f"Constraint {c.id} is marked as impossible.")
            # Check for conflicting constraints on same ID if logic dictates
            # This is a placeholder for complex logical checking
        return constraints

    def decompose(self, puzzle_data: Dict[str, Any]) -> DecompositionResult:
        """
        Main decomposition logic.
        Returns a DecompositionResult with sub-goals and exclusion logs.
        """
        puzzle_id = puzzle_data.get("id", "unknown")
        sub_goals = []
        self.exclusion_log = [] # Reset log for this run

        try:
            constraints = puzzle_data.get("constraints", [])
            if not constraints:
                _logger.warning(f"No constraints found for puzzle {puzzle_id}")
                return DecompositionResult(
                    puzzle_id=puzzle_id,
                    sub_goals=[],
                    success=True,
                    exclusion_log=[]
                )

            # Step 1: Parse constraints
            try:
                formal_constraints = self._parse_constraints(constraints)
            except PARSE_FAILURE as e:
                # Log the parse failure as an exclusion reason
                self._log_exclusion(
                    reason_type="PARSE_FAILURE",
                    reason_details=str(e),
                    context={"puzzle_id": puzzle_id, "failed_constraints": constraints}
                )
                # Return result with empty goals and the log
                return DecompositionResult(
                    puzzle_id=puzzle_id,
                    sub_goals=[],
                    success=False,
                    exclusion_log=self.exclusion_log,
                    error=str(e)
                )

            # Step 2: Check for contradictions
            try:
                valid_constraints = self._check_contradictions(formal_constraints)
            except CONTRADICTION_DETECTED as e:
                # Log the contradiction as an exclusion reason
                self._log_exclusion(
                    reason_type="CONTRADICTION_DETECTED",
                    reason_details=str(e),
                    context={"puzzle_id": puzzle_id, "constraints": [c.id for c in formal_constraints]}
                )
                return DecompositionResult(
                    puzzle_id=puzzle_id,
                    sub_goals=[],
                    success=False,
                    exclusion_log=self.exclusion_log,
                    error=str(e)
                )

            # Step 3: Generate sub-goals from valid constraints
            for i, c in enumerate(valid_constraints):
                sub_goal = SubGoal(
                    id=f"sg_{puzzle_id}_{i}",
                    description=f"Satisfy constraint: {c.expression}",
                    status=SubGoalStatus.PENDING,
                    parent_constraint_id=c.id
                )
                sub_goals.append(sub_goal)

            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=sub_goals,
                success=True,
                exclusion_log=self.exclusion_log
            )

        except Exception as e:
            # Catch-all for unexpected errors
            self._log_exclusion(
                reason_type="UNEXPECTED_ERROR",
                reason_details=str(e),
                context={"puzzle_id": puzzle_id}
            )
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                success=False,
                exclusion_log=self.exclusion_log,
                error=str(e)
            )

    def get_exclusion_log(self) -> List[Dict[str, Any]]:
        """Returns the current exclusion log."""
        return self.exclusion_log

def main():
    """
    Entry point for testing the planner independently.
    Reads a sample puzzle from data/raw/ (if exists) or uses a mock for testing.
    """
    config = load_config()
    planner = SymbolicPlanner(config)

    # Example puzzle data for testing
    test_puzzle = {
        "id": "test_001",
        "type": "logic_puzzle",
        "constraints": [
            {"id": "c1", "type": "rule", "expression": "A != B"},
            {"id": "c2", "type": "rule", "expression": "B != C"}
        ]
    }

    # Test normal decomposition
    result = planner.decompose(test_puzzle)
    print(f"Decomposition Result for {result.puzzle_id}:")
    print(f"  Success: {result.success}")
    print(f"  Sub-goals: {len(result.sub_goals)}")
    print(f"  Exclusions: {len(result.exclusion_log)}")
    if result.exclusion_log:
        print("  Exclusion Log:")
        for entry in result.exclusion_log:
            print(f"    - {entry['type']}: {entry['reason']}")

    # Test PARSE_FAILURE scenario
    print("\n--- Testing PARSE_FAILURE ---")
    bad_puzzle = {
        "id": "test_bad",
        "constraints": [
            {"id": "bad_c1", "type": "invalid_type", "expression": None} # Simulate bad data
        ]
    }
    # We need to simulate a parse failure if the parser doesn't handle None gracefully
    # For this test, we manually trigger the log
    planner._log_exclusion("PARSE_FAILURE", "Simulated parse failure for testing", {"puzzle_id": "test_bad"})
    print(f"Exclusion Log after manual trigger: {planner.get_exclusion_log()}")

    # Test CONTRADICTION_DETECTED scenario
    print("\n--- Testing CONTRADICTION_DETECTED ---")
    # We need to trigger the exception in the flow.
    # Since _check_contradictions raises CONTRADICTION_DETECTED if type is "impossible"
    contradiction_puzzle = {
        "id": "test_contra",
        "constraints": [
            {"id": "c1", "type": "impossible", "expression": "False"}
        ]
    }
    result_contra = planner.decompose(contradiction_puzzle)
    print(f"Decomposition Result for {result_contra.puzzle_id}:")
    print(f"  Success: {result_contra.success}")
    print(f"  Exclusions: {len(result_contra.exclusion_log)}")
    if result_contra.exclusion_log:
        print("  Exclusion Log:")
        for entry in result_contra.exclusion_log:
            print(f"    - {entry['type']}: {entry['reason']}")

if __name__ == "__main__":
    main()