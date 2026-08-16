"""
Symbolic Planner Implementation for BES Framework.

This module provides the symbolic planner that decomposes puzzle constraints
into sub-goals for the backward step of the evolutionary search.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction
from code.utils.logger import log
from code.utils.seed import set_seed


class SubGoalStatus(Enum):
    """Status of a sub-goal decomposition."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubGoal:
    """Represents a single sub-goal in the decomposition."""
    id: str
    description: str
    constraints: Dict[str, Any]
    status: SubGoalStatus = SubGoalStatus.PENDING
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sub-goal to dictionary representation."""
        return {
            'id': self.id,
            'description': self.description,
            'constraints': self.constraints,
            'status': self.status.value,
            'priority': self.priority,
            'dependencies': self.dependencies
        }


@dataclass
class DecompositionResult:
    """Result of the symbolic decomposition process."""
    sub_goals: List[SubGoal]
    status: SubGoalStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            'sub_goals': [sg.to_dict() for sg in self.sub_goals],
            'status': self.status.value,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms
        }


class SymbolicPlanner:
    """
    Symbolic planner for decomposing puzzle constraints into sub-goals.

    This planner implements a deterministic decomposition strategy that
    breaks down complex puzzle constraints into manageable sub-goals
    for the evolutionary search process.
    """

    def __init__(
        self,
        max_sub_goals: int = 10,
        timeout_ms: int = 1000,
        debug: bool = False
    ):
        """
        Initialize the symbolic planner.

        Args:
            max_sub_goals: Maximum number of sub-goals to generate
            timeout_ms: Timeout for decomposition in milliseconds
            debug: Enable debug logging
        """
        self.max_sub_goals = max_sub_goals
        self.timeout_ms = timeout_ms
        self.debug = debug
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the planner."""
        if self.debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def _validate_constraints(
        self,
        constraints: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate the input constraints for logical consistency.

        Args:
            constraints: Dictionary of puzzle constraints

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not constraints:
            return False, "Empty constraints provided"

        # Check for required fields based on puzzle type
        puzzle_type = constraints.get('type')
        if not puzzle_type:
            return False, "Missing puzzle type in constraints"

        # Validate type-specific constraints
        if puzzle_type == 'pathfinding':
            if 'start' not in constraints or 'end' not in constraints:
                return False, "Pathfinding puzzle missing start or end coordinates"
            if 'grid_size' not in constraints:
                return False, "Pathfinding puzzle missing grid size"

        elif puzzle_type == 'sudoku':
            if 'grid_size' not in constraints:
                return False, "Sudoku puzzle missing grid size"
            if 'initial_grid' not in constraints:
                return False, "Sudoku puzzle missing initial grid"

        elif puzzle_type == 'logic':
            if 'clauses' not in constraints:
                return False, "Logic puzzle missing clauses"

        return True, None

    def _detect_contradictions(
        self,
        constraints: Dict[str, Any]
    ) -> Optional[str]:
        """
        Detect logical contradictions in the constraints.

        Args:
            constraints: Dictionary of puzzle constraints

        Returns:
            Error message if contradiction found, None otherwise
        """
        puzzle_type = constraints.get('type')

        if puzzle_type == 'pathfinding':
            start = constraints.get('start')
            end = constraints.get('end')
            obstacles = constraints.get('obstacles', [])

            # Check if start or end is blocked
            if start in obstacles:
                return f"Start position {start} is blocked by an obstacle"
            if end in obstacles:
                return f"End position {end} is blocked by an obstacle"

            # Check if start and end are the same
            if start == end:
                return "Start and end positions are identical"

        elif puzzle_type == 'sudoku':
            grid = constraints.get('initial_grid', [])
            size = constraints.get('grid_size', 9)

            # Basic validation of grid dimensions
            if len(grid) != size:
                return f"Grid has {len(grid)} rows, expected {size}"

            for i, row in enumerate(grid):
                if len(row) != size:
                    return f"Row {i} has {len(row)} columns, expected {size}"

        elif puzzle_type == 'logic':
            clauses = constraints.get('clauses', [])
            # Check for obviously contradictory clauses
            for clause in clauses:
                if isinstance(clause, dict):
                    if clause.get('type') == 'negation' and clause.get('value') == clause.get('negated_value'):
                        return f"Self-contradictory clause detected: {clause}"

        return None

    def _generate_sub_goals(
        self,
        constraints: Dict[str, Any]
    ) -> List[SubGoal]:
        """
        Generate sub-goals from validated constraints.

        Args:
            constraints: Validated puzzle constraints

        Returns:
            List of SubGoal objects
        """
        sub_goals = []
        puzzle_type = constraints.get('type')

        if puzzle_type == 'pathfinding':
            # Decompose pathfinding into: reach intermediate, avoid obstacles, reach goal
            grid_size = constraints.get('grid_size', 5)
            start = constraints.get('start', (0, 0))
            end = constraints.get('end', (grid_size-1, grid_size-1))

            # Sub-goal 1: Navigate from start to center
            center = (grid_size // 2, grid_size // 2)
            sub_goals.append(SubGoal(
                id="sg_001_reach_center",
                description=f"Navigate from {start} to center {center}",
                constraints={
                    'from': start,
                    'to': center,
                    'avoid_obstacles': True
                },
                priority=1
            ))

            # Sub-goal 2: Avoid known obstacles
            obstacles = constraints.get('obstacles', [])
            if obstacles:
                sub_goals.append(SubGoal(
                    id="sg_002_avoid_obstacles",
                    description=f"Avoid obstacles at {obstacles}",
                    constraints={
                        'obstacles': obstacles,
                        'mode': 'avoidance'
                    },
                    priority=2,
                    dependencies=["sg_001_reach_center"]
                ))

            # Sub-goal 3: Reach final destination
            sub_goals.append(SubGoal(
                id="sg_003_reach_goal",
                description=f"Navigate from center to {end}",
                constraints={
                    'from': center,
                    'to': end,
                    'final': True
                },
                priority=3,
                dependencies=["sg_001_reach_center"]
            ))

        elif puzzle_type == 'sudoku':
            size = constraints.get('grid_size', 9)
            # Decompose into row, column, and box constraints
            sub_goals.append(SubGoal(
                id="sg_001_rows",
                description=f"Ensure all rows contain unique values 1-{size}",
                constraints={
                    'type': 'row_constraint',
                    'size': size
                },
                priority=1
            ))
            sub_goals.append(SubGoal(
                id="sg_002_columns",
                description=f"Ensure all columns contain unique values 1-{size}",
                constraints={
                    'type': 'column_constraint',
                    'size': size
                },
                priority=2,
                dependencies=["sg_001_rows"]
            ))
            sub_goals.append(SubGoal(
                id="sg_003_boxes",
                description=f"Ensure all boxes contain unique values 1-{size}",
                constraints={
                    'type': 'box_constraint',
                    'size': size
                },
                priority=3,
                dependencies=["sg_002_columns"]
            ))

        elif puzzle_type == 'logic':
            clauses = constraints.get('clauses', [])
            # Create sub-goals for each major clause group
            for i, clause in enumerate(clauses[:self.max_sub_goals]):
                sub_goals.append(SubGoal(
                    id=f"sg_{i+1:03d}_clause_group",
                    description=f"Satisfy clause group {i+1}: {str(clause)[:50]}",
                    constraints={
                        'clause': clause,
                        'group_id': i
                    },
                    priority=i + 1
                ))

        # Limit to max_sub_goals
        return sub_goals[:self.max_sub_goals]

    def decompose(
        self,
        constraints: Dict[str, Any]
    ) -> DecompositionResult:
        """
        Decompose puzzle constraints into a sequence of sub-goals.

        Args:
            constraints: Dictionary containing puzzle constraints

        Returns:
            DecompositionResult with sub-goals and status
        """
        import time
        start_time = time.time()

        try:
            # Validate constraints
            is_valid, error_msg = self._validate_constraints(constraints)
            if not is_valid:
                raise PARSE_FAILURE(error_msg)

            # Check for contradictions
            contradiction = self._detect_contradictions(constraints)
            if contradiction:
                raise CONTRADICTION_DETECTED(contradiction)

            # Generate sub-goals
            sub_goals = self._generate_sub_goals(constraints)

            execution_time_ms = (time.time() - start_time) * 1000

            log(f"Successfully decomposed puzzle into {len(sub_goals)} sub-goals")

            return DecompositionResult(
                sub_goals=sub_goals,
                status=SubGoalStatus.COMPLETED,
                execution_time_ms=execution_time_ms
            )

        except (PARSE_FAILURE, CONTRADICTION_DETECTED) as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_type = "PARSE_FAILURE" if isinstance(e, PARSE_FAILURE) else "CONTRADICTION_DETECTED"
            return DecompositionResult(
                sub_goals=[],
                status=SubGoalStatus.FAILED,
                error_code=error_type,
                error_message=str(e),
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            log(f"Unexpected error during decomposition: {str(e)}", level="ERROR")
            return DecompositionResult(
                sub_goals=[],
                status=SubGoalStatus.FAILED,
                error_code="DECOMPOSITION_ERROR",
                error_message=str(e),
                execution_time_ms=execution_time_ms
            )


def main() -> None:
    """
    Entry point for testing the symbolic planner.

    Demonstrates the decomposition process with sample puzzles.
    """
    # Set seed for reproducibility
    set_seed(42)

    # Initialize planner
    planner = SymbolicPlanner(max_sub_goals=5, debug=True)

    # Sample pathfinding puzzle
    pathfinding_constraints = {
        'type': 'pathfinding',
        'grid_size': 5,
        'start': (0, 0),
        'end': (4, 4),
        'obstacles': [(2, 2), (3, 3)]
    }

    print("Decomposing pathfinding puzzle...")
    result = planner.decompose(pathfinding_constraints)

    print(json.dumps(result.to_dict(), indent=2))

    # Sample sudoku puzzle
    sudoku_constraints = {
        'type': 'sudoku',
        'grid_size': 4,
        'initial_grid': [
            [1, 0, 0, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [4, 0, 0, 1]
        ]
    }

    print("\nDecomposing sudoku puzzle...")
    result = planner.decompose(sudoku_constraints)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()