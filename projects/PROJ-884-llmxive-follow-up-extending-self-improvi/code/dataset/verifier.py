"""
Deterministic puzzle verifier for the llmXive pipeline.
Validates puzzle solutions against constraints and returns boolean validity
with specific constraint violation codes.
"""
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import custom exceptions from the project's exceptions module
from code.exceptions import VERIFIER_ERROR, raise_verifier_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorCodes(Enum):
    """Specific constraint violation codes for deterministic validation."""
    VALID = "VALID"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    DUPLICATE_COLUMN = "DUPLICATE_COLUMN"
    DUPLICATE_BLOCK = "DUPLICATE_BLOCK"
    INVALID_PATH = "INVALID_PATH"
    PATH_DISCONNECTED = "PATH_DISCONNECTED"
    MISSING_STEP = "MISSING_STEP"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    INVALID_FORMAT = "INVALID_FORMAT"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    VERIFIER_CRASH = "VERIFIER_CRASH"

@dataclass
class SolutionResult:
    """Result of verifying a puzzle solution."""
    is_valid: bool
    error_code: Optional[ErrorCodes] = None
    error_details: Optional[str] = None
    verification_time_ms: float = 0.0
    puzzle_id: Optional[str] = None

class DataVerificationError(Exception):
    """Custom exception for data verification failures."""
    pass

class PuzzleVerifier:
    """
    Deterministic verifier for puzzle instances.
    Supports Sudoku variants and pathfinding puzzles.
    Must complete validation within 100ms per instance.
    """

    def __init__(self, timeout_ms: int = 100):
        """
        Initialize the verifier with a timeout constraint.

        Args:
            timeout_ms: Maximum allowed verification time in milliseconds.
        """
        self.timeout_ms = timeout_ms

    def verify_solution(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """
        Verify a solution against a puzzle instance.

        Args:
            puzzle: Dictionary containing puzzle constraints, initial_state, target_state.
            solution: Dictionary containing the proposed solution path or grid.

        Returns:
            SolutionResult with validity status and specific error codes.
        """
        start_time = time.time()
        puzzle_id = puzzle.get("id", "unknown")

        try:
            # Validate input format
            if not self._validate_input_format(puzzle, solution):
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_FORMAT,
                    error_details="Invalid input format",
                    puzzle_id=puzzle_id
                )

            puzzle_type = puzzle.get("type", "").lower()

            if puzzle_type == "sudoku":
                result = self._verify_sudoku(puzzle, solution)
            elif puzzle_type == "pathfinding":
                result = self._verify_pathfinding(puzzle, solution)
            else:
                raise DataVerificationError(f"Unknown puzzle type: {puzzle_type}")

            # Check timeout
            elapsed_ms = (time.time() - start_time) * 1000
            result.verification_time_ms = elapsed_ms

            if elapsed_ms > self.timeout_ms:
                logger.warning(f"Verification for {puzzle_id} exceeded timeout: {elapsed_ms:.2f}ms")

            result.puzzle_id = puzzle_id
            return result

        except DataVerificationError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                error_details=str(e),
                verification_time_ms=elapsed_ms,
                puzzle_id=puzzle_id
            )
        except Exception as e:
            # Fail loudly on unexpected errors - do not return silent "invalid"
            elapsed_ms = (time.time() - start_time) * 1000
            raise_verifier_error(f"Unexpected error during verification: {str(e)}")

    def _validate_input_format(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> bool:
        """Validate that puzzle and solution have required fields."""
        required_puzzle_fields = ["type", "constraints"]
        for field_name in required_puzzle_fields:
            if field_name not in puzzle:
                return False

        puzzle_type = puzzle.get("type", "").lower()
        if puzzle_type == "sudoku":
            return "grid" in puzzle and "solution_grid" in solution
        elif puzzle_type == "pathfinding":
            return "initial_state" in puzzle and "target_state" in puzzle and "path" in solution
        return False

    def _verify_sudoku(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """Verify Sudoku solution against constraints."""
        grid = solution.get("solution_grid", [])
        size = len(grid)

        if size == 0:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_FORMAT,
                error_details="Empty grid"
            )

        # Check row constraints
        for i, row in enumerate(grid):
            if len(row) != size:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.DUPLICATE_ROW,
                    error_details=f"Row {i} has incorrect length"
                )
            if len(set(row)) != size:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.DUPLICATE_ROW,
                    error_details=f"Row {i} contains duplicates"
                )

        # Check column constraints
        for col_idx in range(size):
            column = [grid[row_idx][col_idx] for row_idx in range(size)]
            if len(set(column)) != size:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.DUPLICATE_COLUMN,
                    error_details=f"Column {col_idx} contains duplicates"
                )

        # Check block constraints (assuming square blocks for standard Sudoku)
        block_size = int(size ** 0.5)
        if block_size * block_size != size:
            # Non-standard Sudoku, skip block check or handle differently
            pass
        else:
            for block_row in range(block_size):
                for block_col in range(block_size):
                    block_values = []
                    for i in range(block_size):
                        for j in range(block_size):
                            row_idx = block_row * block_size + i
                            col_idx = block_col * block_size + j
                            block_values.append(grid[row_idx][col_idx])
                    if len(set(block_values)) != size:
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.DUPLICATE_BLOCK,
                            error_details=f"Block ({block_row}, {block_col}) contains duplicates"
                        )

        # Verify against initial state constraints
        initial_grid = puzzle.get("grid", [])
        for i in range(size):
            for j in range(size):
                if initial_grid[i][j] != 0 and initial_grid[i][j] != grid[i][j]:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                        error_details=f"Conflict at ({i}, {j}): initial={initial_grid[i][j]}, solution={grid[i][j]}"
                    )

        return SolutionResult(is_valid=True)

    def _verify_pathfinding(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """Verify pathfinding solution against constraints."""
        path = solution.get("path", [])
        initial_state = puzzle.get("initial_state", {})
        target_state = puzzle.get("target_state", {})
        constraints = puzzle.get("constraints", {})

        if not path:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Empty path"
            )

        # Check if path starts at initial state
        if path[0] != initial_state:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Path does not start at initial state"
            )

        # Check if path ends at target state
        if path[-1] != target_state:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Path does not end at target state"
            )

        # Check path continuity and constraints
        grid_size = constraints.get("grid_size", (0, 0))
        if len(grid_size) == 2:
            rows, cols = grid_size
        else:
            rows, cols = 0, 0

        for i in range(len(path) - 1):
            current = path[i]
            next_step = path[i + 1]

            # Check if steps are adjacent (Manhattan distance = 1)
            if isinstance(current, tuple) and isinstance(next_step, tuple):
                dx = abs(current[0] - next_step[0])
                dy = abs(current[1] - next_step[1])
                if dx + dy != 1:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.PATH_DISCONNECTED,
                        error_details=f"Steps {i} and {i+1} are not adjacent"
                    )

                # Check bounds
                if not (0 <= next_step[0] < rows and 0 <= next_step[1] < cols):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.OUT_OF_BOUNDS,
                        error_details=f"Step {i+1} is out of bounds"
                    )

            # Check against obstacle constraints
            obstacles = constraints.get("obstacles", [])
            if next_step in obstacles:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                    error_details=f"Path hits obstacle at step {i+1}"
                )

        return SolutionResult(is_valid=True)

def verify_solution(puzzle: Dict[str, Any], solution: Dict[str, Any], timeout_ms: int = 100) -> SolutionResult:
    """
    Convenience function to verify a puzzle solution.

    Args:
        puzzle: Puzzle instance dictionary.
        solution: Solution dictionary.
        timeout_ms: Maximum verification time in milliseconds.

    Returns:
        SolutionResult with validity status.
    """
    verifier = PuzzleVerifier(timeout_ms=timeout_ms)
    return verifier.verify_solution(puzzle, solution)

def main():
    """Main entry point for command-line verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify puzzle solutions")
    parser.add_argument("--puzzle", required=True, help="Path to puzzle JSON file")
    parser.add_argument("--solution", required=True, help="Path to solution JSON file")
    parser.add_argument("--output", help="Path to output result JSON file")
    args = parser.parse_args()

    try:
        with open(args.puzzle, 'r') as f:
            puzzle = json.load(f)
        with open(args.solution, 'r') as f:
            solution = json.load(f)

        result = verify_solution(puzzle, solution)

        result_dict = {
            "is_valid": result.is_valid,
            "error_code": result.error_code.value if result.error_code else None,
            "error_details": result.error_details,
            "verification_time_ms": result.verification_time_ms,
            "puzzle_id": result.puzzle_id
        }

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result_dict, f, indent=2)
            print(f"Result written to {args.output}")
        else:
            print(json.dumps(result_dict, indent=2))

        sys.exit(0 if result.is_valid else 1)

    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()