"""
Symbolic Planner for BES Backward Step.

Generates sub-goal decompositions from parsed formal constraints.
Detects and flags PARSE_FAILURE and CONTRADICTION_DETECTED exceptions.
Logs exclusion reasons as required by FR-006.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import from project API surface
from code.exceptions import (
    BaseResearchException,
    PARSE_FAILURE,
    CONTRADICTION_DETECTED,
    raise_parse_failure,
    raise_contradiction
)
from code.symbolic.parser import FormalConstraint, PuzzleParser
from code.utils.logger import log

logger = logging.getLogger(__name__)

class SubGoalStatus(Enum):
    """Status of a generated sub-goal."""
    VALID = "valid"
    CONTRADICTION = "contradiction"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"

@dataclass
class SubGoal:
    """Represents a single sub-goal in the decomposition."""
    id: str
    description: str
    status: SubGoalStatus
    reason: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class DecompositionResult:
    """Result of the sub-goal decomposition process."""
    puzzle_id: str
    sub_goals: List[SubGoal]
    success: bool
    error_reason: Optional[str] = None
    exclusion_reason: Optional[str] = None

class SymbolicPlanner:
    """
    Symbolic planner that generates sub-goal decompositions.

    Converts formal constraints into a sequence of executable sub-goals.
    Handles constraint contradictions and parse failures gracefully.
    """

    def __init__(self, parser: Optional[PuzzleParser] = None):
        """
        Initialize the planner.

        Args:
            parser: Optional PuzzleParser instance. If None, creates a default.
        """
        self.parser = parser or PuzzleParser()
        self._log_exclusion_reasons = True

    def decompose(self, constraints: List[FormalConstraint], puzzle_id: str) -> DecompositionResult:
        """
        Generate sub-goal decomposition from formal constraints.

        Args:
            constraints: List of parsed formal constraints.
            puzzle_id: Identifier for the puzzle being processed.

        Returns:
            DecompositionResult containing sub-goals and status.
        """
        sub_goals: List[SubGoal] = []
        error_reason: Optional[str] = None
        exclusion_reason: Optional[str] = None
        success = True

        try:
            # Validate constraints for contradictions
            contradictions = self._detect_contradictions(constraints)
            if contradictions:
                error_msg = f"Contradictions detected: {', '.join(contradictions)}"
                raise_contradiction(error_msg)
                success = False
                exclusion_reason = "CONTRADICTION_DETECTED"

            # Generate sub-goals from validated constraints
            if success:
                sub_goals = self._generate_sub_goals(constraints)

                # Check for any parse errors during generation
                parse_errors = [sg for sg in sub_goals if sg.status == SubGoalStatus.PARSE_ERROR]
                if parse_errors:
                    error_msg = f"Parse errors in {len(parse_errors)} sub-goals"
                    raise_parse_failure(error_msg)
                    success = False
                    exclusion_reason = "PARSE_FAILURE"

        except BaseResearchException as e:
            error_reason = str(e)
            success = False
            if isinstance(e, CONTRADICTION_DETECTED):
                exclusion_reason = "CONTRADICTION_DETECTED"
            elif isinstance(e, PARSE_FAILURE):
                exclusion_reason = "PARSE_FAILURE"
            else:
                exclusion_reason = "UNKNOWN_ERROR"
        except Exception as e:
            error_reason = f"Unexpected error: {str(e)}"
            success = False
            exclusion_reason = "UNEXPECTED_ERROR"

        # Log exclusion reason if applicable
        if exclusion_reason and self._log_exclusion_reasons:
            self._log_exclusion(puzzle_id, exclusion_reason, error_reason)

        return DecompositionResult(
            puzzle_id=puzzle_id,
            sub_goals=sub_goals,
            success=success,
            error_reason=error_reason,
            exclusion_reason=exclusion_reason
        )

    def _detect_contradictions(self, constraints: List[FormalConstraint]) -> List[str]:
        """
        Detect logical contradictions between constraints.

        Args:
            constraints: List of formal constraints to check.

        Returns:
            List of contradiction descriptions.
        """
        contradictions = []

        # Group constraints by variable
        var_constraints: Dict[str, List[FormalConstraint]] = {}
        for constraint in constraints:
            var_name = constraint.variable
            if var_name not in var_constraints:
                var_constraints[var_name] = []
            var_constraints[var_name].append(constraint)

        # Check for contradictions within each variable's constraints
        for var_name, var_cons in var_constraints.items():
            # Check for mutually exclusive constraints
            if len(var_cons) > 1:
                # Example: Value cannot be both A and B if A != B
                values = [c.value for c in var_cons if c.operator in ['=', '==']]
                if len(set(values)) > 1 and len(values) > 1:
                    contradictions.append(
                        f"Variable '{var_name}' has conflicting values: {values}"
                    )

                # Check for impossible ranges
                min_val = None
                max_val = None
                for c in var_cons:
                    if c.operator in ['>=', '>', '>=', '>=']:
                        if min_val is None or c.value > min_val:
                            min_val = c.value
                    elif c.operator in ['<=', '<', '<=', '<=']:
                        if max_val is None or c.value < max_val:
                            max_val = c.value

                if min_val is not None and max_val is not None and min_val > max_val:
                    contradictions.append(
                        f"Variable '{var_name}' has impossible range: [{min_val}, {max_val}]"
                    )

        return contradictions

    def _generate_sub_goals(self, constraints: List[FormalConstraint]) -> List[SubGoal]:
        """
        Generate sub-goals from formal constraints.

        Args:
            constraints: List of formal constraints.

        Returns:
            List of SubGoal objects.
        """
        sub_goals = []

        # Sort constraints by complexity (simple assignments first)
        sorted_constraints = sorted(
            constraints,
            key=lambda c: (
                0 if c.operator in ['=', '=='] else 1,
                1 if c.operator in ['!=', '<>', '!='] else 0
            )
        )

        for i, constraint in enumerate(sorted_constraints):
            try:
                # Validate constraint format
                if not constraint.variable or not constraint.value:
                    raise ValueError(f"Invalid constraint format: {constraint}")

                # Create sub-goal
                sub_goal = SubGoal(
                    id=f"sg_{i+1}",
                    description=self._format_constraint(constraint),
                    status=SubGoalStatus.VALID,
                    dependencies=self._get_dependencies(constraint, sorted_constraints[:i])
                )
                sub_goals.append(sub_goal)

            except Exception as e:
                # Mark as parse error
                sub_goal = SubGoal(
                    id=f"sg_{i+1}",
                    description=f"Failed to process: {constraint}",
                    status=SubGoalStatus.PARSE_ERROR,
                    reason=str(e)
                )
                sub_goals.append(sub_goal)

        return sub_goals

    def _format_constraint(self, constraint: FormalConstraint) -> str:
        """Format a constraint as a human-readable description."""
        return f"{constraint.variable} {constraint.operator} {constraint.value}"

    def _get_dependencies(self, constraint: FormalConstraint, previous: List[FormalConstraint]) -> List[str]:
        """Determine dependencies for a constraint based on previous constraints."""
        deps = []
        # Simple dependency logic: if previous constraints affect the same variable, add dependency
        for prev in previous:
            if prev.variable == constraint.variable:
                deps.append(f"sg_{previous.index(prev) + 1}")
        return deps

    def _log_exclusion(self, puzzle_id: str, reason: str, details: Optional[str] = None):
        """
        Log exclusion reasons for failed decompositions.

        Args:
            puzzle_id: Identifier of the excluded puzzle.
            reason: The exclusion reason (PARSE_FAILURE, CONTRADICTION_DETECTED, etc.).
            details: Optional detailed explanation.
        """
        log_entry = {
            "event": "planner_exclusion",
            "puzzle_id": puzzle_id,
            "reason": reason,
            "details": details,
            "timestamp": log.__name__  # Using logger's timestamp mechanism
        }
        logger.warning(f"Planner exclusion: {log_entry}")

    def plan_from_dataset(self, dataset_path: Path) -> List[DecompositionResult]:
        """
        Process a dataset file and generate decompositions for all puzzles.

        Args:
            dataset_path: Path to the JSON dataset file.

        Returns:
            List of DecompositionResult objects.
        """
        results = []

        try:
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)

            for puzzle in dataset:
                puzzle_id = puzzle.get('id', 'unknown')
                try:
                    # Parse constraints
                    constraints = self.parser.parse_puzzle(puzzle)
                    # Decompose
                    result = self.decompose(constraints, puzzle_id)
                    results.append(result)
                except Exception as e:
                    # Handle parse failures at dataset level
                    result = DecompositionResult(
                        puzzle_id=puzzle_id,
                        sub_goals=[],
                        success=False,
                        error_reason=str(e),
                        exclusion_reason="PARSE_FAILURE"
                    )
                    results.append(result)
                    self._log_exclusion(puzzle_id, "PARSE_FAILURE", str(e))

        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_path}: {e}")
            raise

        return results


def main():
    """
    Main entry point for testing the planner.
    Processes a sample dataset and prints results.
    """
    import sys

    # Default dataset path
    dataset_path = Path("data/raw/puzzles.json")
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        print("Usage: python code/symbolic/planner.py [dataset_path]")
        sys.exit(1)

    print(f"Processing dataset: {dataset_path}")

    planner = SymbolicPlanner()
    results = planner.plan_from_dataset(dataset_path)

    success_count = sum(1 for r in results if r.success)
    print(f"\nProcessed {len(results)} puzzles:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {len(results) - success_count}")

    # Print details for failed puzzles
    for result in results:
        if not result.success:
            print(f"\n  Puzzle {result.puzzle_id}:")
            print(f"    Reason: {result.exclusion_reason}")
            print(f"    Details: {result.error_reason}")

    return results


if __name__ == "__main__":
    main()