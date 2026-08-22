"""
Symbolic Planner for BES (Bidirectional Evolutionary Search).

This module implements the backward step logic, generating sub-goal decompositions
from target states while detecting logical contradictions and parse failures.
It integrates with the exclusion logger to record failed attempts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import exceptions from the project root
from code.exceptions import CONTRADICTION_DETECTED, PARSE_FAILURE, raise_contradiction, raise_parse_failure

# Import the exclusion logger helper
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent

logger = logging.getLogger(__name__)


class SubGoalStatus(Enum):
    """Status of a generated sub-goal."""
    PENDING = "pending"
    VALIDATED = "validated"
    CONTRADICTION = "contradiction"
    FAILED = "failed"


@dataclass
class SubGoal:
    """Represents a single sub-goal in the decomposition."""
    id: str
    description: str
    target_state_fragment: Dict[str, Any]
    prerequisites: List[str] = field(default_factory=list)
    status: SubGoalStatus = SubGoalStatus.PENDING
    validation_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "target_state_fragment": self.target_state_fragment,
            "prerequisites": self.prerequisites,
            "status": self.status.value,
            "validation_message": self.validation_message
        }


@dataclass
class DecompositionResult:
    """Result of the sub-goal decomposition process."""
    success: bool
    sub_goals: List[SubGoal]
    initial_state: Dict[str, Any]
    target_state: Dict[str, Any]
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    exclusion_logged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "sub_goals": [sg.to_dict() for sg in self.sub_goals],
            "initial_state": self.initial_state,
            "target_state": self.target_state,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "exclusion_logged": self.exclusion_logged
        }


class SymbolicPlanner:
    """
    Generates sub-goal decompositions for puzzle solving.

    Implements logic to:
    1. Parse constraints from the target state.
    2. Generate a sequence of sub-goals to bridge initial and target states.
    3. Detect logical contradictions (e.g., mutually exclusive constraints).
    4. Flag parse failures if the input structure is invalid.
    5. Log exclusions via ExclusionLogger when decomposition fails.
    """

    def __init__(self, exclusion_log_path: Optional[Path] = None):
        """
        Initialize the planner.

        Args:
            exclusion_log_path: Path to the exclusion log file. If None, uses default.
        """
        self.exclusion_logger = ExclusionLogger(log_path=exclusion_log_path)
        logger.info("SymbolicPlanner initialized.")

    def _detect_contradiction(self, sub_goals: List[SubGoal], initial_state: Dict[str, Any]) -> Optional[str]:
        """
        Detect logical contradictions in the generated sub-goals.

        Checks if the union of sub-goals contradicts the initial state or
        if sub-goals contradict each other.

        Args:
            sub_goals: List of generated sub-goals.
            initial_state: The starting state of the puzzle.

        Returns:
            A string describing the contradiction if found, None otherwise.
        """
        # Check for direct contradictions with initial state
        # Example: If initial state has cell (0,0) = 1, and a sub-goal requires (0,0) = 2
        initial_constraints = {}
        if "grid" in initial_state:
            for r, row in enumerate(initial_state["grid"]):
                for c, val in enumerate(row):
                    if val != 0: # Assuming 0 is empty
                        initial_constraints[(r, c)] = val

        for sg in sub_goals:
            target_frag = sg.target_state_fragment
            if "grid" in target_frag:
                for r, row in enumerate(target_frag["grid"]):
                    for c, val in enumerate(row):
                        if val != 0:
                            key = (r, c)
                            if key in initial_constraints and initial_constraints[key] != val:
                                return f"Contradiction: Sub-goal {sg.id} requires ({r},{c})={val}, but initial state has {initial_constraints[key]}."
                            initial_constraints[key] = val # Update for subsequent checks

        # Check for internal contradictions between sub-goals
        # (Simplified check: if two sub-goals require different values for same cell)
        seen_constraints = {}
        for sg in sub_goals:
            target_frag = sg.target_state_fragment
            if "grid" in target_frag:
                for r, row in enumerate(target_frag["grid"]):
                    for c, val in enumerate(row):
                        if val != 0:
                            key = (r, c)
                            if key in seen_constraints and seen_constraints[key] != val:
                                return f"Internal Contradiction: Sub-goal {sg.id} and previous goals conflict on ({r},{c})."
                            seen_constraints[key] = val

        return None

    def _detect_parse_failure(self, target_state: Dict[str, Any]) -> Optional[str]:
        """
        Validate the structure of the target state.

        Args:
            target_state: The target state dictionary.

        Returns:
            Error message if structure is invalid, None otherwise.
        """
        if not isinstance(target_state, dict):
            return "Target state must be a dictionary."
        
        # Basic schema validation
        if "grid" not in target_state:
            return "Target state missing 'grid' key."
        
        grid = target_state["grid"]
        if not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
            return "Target state 'grid' must be a list of lists."
        
        # Check for uniform dimensions
        if grid:
            row_len = len(grid[0])
            if not all(len(row) == row_len for row in grid):
                return "Target state 'grid' rows have inconsistent lengths."

        return None

    def decompose(self, initial_state: Dict[str, Any], target_state: Dict[str, Any], puzzle_id: str) -> DecompositionResult:
        """
        Generate a decomposition of the target state into sub-goals.

        Args:
            initial_state: The starting configuration.
            target_state: The desired end configuration.
            puzzle_id: Unique identifier for the puzzle.

        Returns:
            DecompositionResult containing sub-goals or error details.
        """
        logger.info(f"Decomposing puzzle {puzzle_id}")

        # 1. Check for Parse Failures
        parse_error = self._detect_parse_failure(target_state)
        if parse_error:
            error_msg = f"PARSE_FAILURE: {parse_error}"
            logger.error(error_msg)
            
            # Log exclusion
            event = ExclusionEvent(
                puzzle_id=puzzle_id,
                reason="PARSE_FAILURE",
                details=parse_error,
                stage="symbolic_planner"
            )
            self.exclusion_logger.log(event)

            return DecompositionResult(
                success=False,
                sub_goals=[],
                initial_state=initial_state,
                target_state=target_state,
                error_type="PARSE_FAILURE",
                error_message=parse_error,
                exclusion_logged=True
            )

        # 2. Generate Sub-goals (Heuristic: Cell-by-cell or Region-by-region)
        # For Sudoku/Pathfinding, we break it down into filling specific cells or reaching specific nodes.
        sub_goals: List[SubGoal] = []
        grid_size = len(target_state.get("grid", []))
        
        # Simple heuristic: Generate a sub-goal for each non-zero cell in the target
        # In a real implementation, this would be more intelligent (e.g., grouping by row/col)
        goal_counter = 0
        target_grid = target_state.get("grid", [])
        initial_grid = initial_state.get("grid", [])

        for r in range(grid_size):
            for c in range(len(target_grid[r])):
                target_val = target_grid[r][c]
                initial_val = initial_grid[r][c] if r < len(initial_grid) and c < len(initial_grid[r]) else 0

                if target_val != initial_val:
                    goal_id = f"sg_{puzzle_id}_{r}_{c}"
                    sub_goal = SubGoal(
                        id=goal_id,
                        description=f"Set cell ({r}, {c}) to {target_val}",
                        target_state_fragment={"grid": [[0]*len(target_grid[0]) for _ in range(grid_size)]}, # Minimal fragment
                        status=SubGoalStatus.PENDING
                    )
                    # Populate the fragment with the specific change
                    sub_goal.target_state_fragment["grid"][r][c] = target_val
                    sub_goals.append(sub_goal)
                    goal_counter += 1

        # 3. Detect Contradictions
        contradiction_msg = self._detect_contradiction(sub_goals, initial_state)
        if contradiction_msg:
            error_msg = f"CONTRADICTION_DETECTED: {contradiction_msg}"
            logger.error(error_msg)

            # Log exclusion
            event = ExclusionEvent(
                puzzle_id=puzzle_id,
                reason="CONTRADICTION_DETECTED",
                details=contradiction_msg,
                stage="symbolic_planner"
            )
            self.exclusion_logger.log(event)

            return DecompositionResult(
                success=False,
                sub_goals=[],
                initial_state=initial_state,
                target_state=target_state,
                error_type="CONTRADICTION_DETECTED",
                error_message=contradiction_msg,
                exclusion_logged=True
            )

        # 4. Mark as Validated
        for sg in sub_goals:
            sg.status = SubGoalStatus.VALIDATED

        logger.info(f"Successfully decomposed puzzle {puzzle_id} into {len(sub_goals)} sub-goals.")
        return DecompositionResult(
            success=True,
            sub_goals=sub_goals,
            initial_state=initial_state,
            target_state=target_state,
            exclusion_logged=False
        )

    def log_contradiction(self, puzzle_id: str, details: str) -> None:
        """
        Helper to explicitly log a contradiction event.

        Args:
            puzzle_id: The puzzle identifier.
            details: Description of the contradiction.
        """
        event = ExclusionEvent(
            puzzle_id=puzzle_id,
            reason="CONTRADICTION_DETECTED",
            details=details,
            stage="symbolic_planner"
        )
        self.exclusion_logger.log(event)
        logger.warning(f"Logged contradiction for {puzzle_id}: {details}")


def main():
    """Entry point for testing the planner independently."""
    import argparse
    parser = argparse.ArgumentParser(description="Test Symbolic Planner")
    parser.add_argument("--puzzle", type=str, help="Path to a puzzle JSON file")
    args = parser.parse_args()

    if args.puzzle:
        with open(args.puzzle, 'r') as f:
            puzzle_data = json.load(f)
        
        planner = SymbolicPlanner()
        result = planner.decompose(
            initial_state=puzzle_data.get("initial_state", {}),
            target_state=puzzle_data.get("target_state", {}),
            puzzle_id=puzzle_data.get("id", "unknown")
        )
        
        print(json.dumps(result.to_dict(), indent=2))
    else:
        # Run a simple mock test
        planner = SymbolicPlanner()
        mock_initial = {"grid": [[0, 0], [0, 0]]}
        mock_target = {"grid": [[1, 0], [0, 1]]}
        result = planner.decompose(mock_initial, mock_target, "test_001")
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()