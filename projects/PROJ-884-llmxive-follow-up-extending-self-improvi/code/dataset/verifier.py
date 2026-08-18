"""
Puzzle Verifier Module for llmXive.

Executes deterministic validation logic for puzzle instances.
Implements strict "Fail Loudly" semantics: any failure in verification
raises an exception immediately. No silent fallbacks.
"""

import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import custom exceptions
from code.exceptions import BaseResearchException, VERIFIER_ERROR

class DataVerificationError(BaseResearchException):
    """
    Raised when puzzle verification fails due to invalid input format,
    constraint violations, or inability to parse the solution.
    This exception halts execution immediately; no fallback is attempted.
    """
    pass

class ErrorCodes(Enum):
    """Specific error codes for verification failures."""
    VALID = "VALID"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    DUPLICATE_COL = "DUPLICATE_COL"
    DUPLICATE_BLOCK = "DUPLICATE_BLOCK"
    INVALID_PATH = "INVALID_PATH"
    MISSING_CHECKPOINT = "MISSING_CHECKPOINT"
    OBSTACLE_COLLISION = "OBSTACLE_COLLISION"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    PARSE_FAILURE = "PARSE_FAILURE"
    VERIFIER_ERROR = "VERIFIER_ERROR"

@dataclass
class SolutionResult:
    """Result of verifying a solution."""
    is_valid: bool
    error_code: Optional[ErrorCodes] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_code": self.error_code.value if self.error_code else None,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }

class PuzzleVerifier:
    """
    Verifies solutions for Sudoku and Pathfinding puzzles.
    Implements strict fail-loudly logic: if a solution cannot be parsed
    or verified, an exception is raised immediately.
    """

    def verify_sudoku(self, instance: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """
        Verify a Sudoku solution.
        
        Args:
            instance: The puzzle instance dictionary.
            solution: The proposed solution dictionary.
        
        Returns:
            SolutionResult indicating validity and any errors.
        
        Raises:
            DataVerificationError: If the solution format is invalid or cannot be parsed.
        """
        start_time = time.time()
        
        try:
            grid_size = instance["complexity_n"]
            block_size = int(grid_size ** 0.5)
            
            # Parse solution grid
            if "grid" not in solution:
                raise DataVerificationError("Solution missing 'grid' key.")
            
            sol_grid = solution["grid"]
            
            if not isinstance(sol_grid, list) or len(sol_grid) != grid_size:
                raise DataVerificationError(f"Solution grid must be a {grid_size}x{grid_size} list.")
            
            # Check each row
            for r in range(grid_size):
                if len(sol_grid[r]) != grid_size:
                    raise DataVerificationError(f"Row {r} has incorrect length.")
                row_vals = sol_grid[r]
                if len(row_vals) != len(set(row_vals)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Duplicate values in row {r}",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                if not all(1 <= v <= grid_size for v in row_vals):
                    raise DataVerificationError(f"Row {r} contains invalid values.")
            
            # Check each column
            for c in range(grid_size):
                col_vals = [sol_grid[r][c] for r in range(grid_size)]
                if len(col_vals) != len(set(col_vals)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_COL,
                        error_message=f"Duplicate values in column {c}",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
            
            # Check each block
            for block_r in range(block_size):
                for block_c in range(block_size):
                    block_vals = []
                    for r in range(block_r * block_size, (block_r + 1) * block_size):
                        for c in range(block_c * block_size, (block_c + 1) * block_size):
                            block_vals.append(sol_grid[r][c])
                    if len(block_vals) != len(set(block_vals)):
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.DUPLICATE_BLOCK,
                            error_message=f"Duplicate values in block ({block_r}, {block_c})",
                            execution_time_ms=(time.time() - start_time) * 1000
                        )
            
            # Check consistency with initial state
            initial_grid = instance["initial_state"]["grid"]
            for r in range(grid_size):
                for c in range(grid_size):
                    if initial_grid[r][c] != 0 and initial_grid[r][c] != sol_grid[r][c]:
                        raise DataVerificationError(f"Solution conflicts with initial state at ({r}, {c}).")
            
            return SolutionResult(
                is_valid=True,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        except DataVerificationError:
            raise
        except Exception as e:
            raise DataVerificationError(f"Unexpected error during Sudoku verification: {e}")

    def verify_pathfinding(self, instance: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """
        Verify a Pathfinding solution.
        
        Args:
            instance: The puzzle instance dictionary.
            solution: The proposed solution dictionary.
        
        Returns:
            SolutionResult indicating validity and any errors.
        
        Raises:
            DataVerificationError: If the solution format is invalid or cannot be parsed.
        """
        start_time = time.time()
        
        try:
            grid_size = instance["complexity_n"]
            grid = instance["initial_state"]["grid"]
            start = tuple(instance["initial_state"]["start"])
            end = tuple(instance["initial_state"]["end"])
            checkpoints = [tuple(cp) for cp in instance["constraints"]["checkpoints"]]
            
            # Parse solution path
            if "path" not in solution:
                raise DataVerificationError("Solution missing 'path' key.")
            
            path = solution["path"]
            
            if not isinstance(path, list) or len(path) == 0:
                raise DataVerificationError("Solution path must be a non-empty list.")
            
            # Check start and end
            if tuple(path[0]) != start:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message=f"Path does not start at {start}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            if tuple(path[-1]) != end:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message=f"Path does not end at {end}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check path continuity and constraints
            for i in range(len(path)):
                r, c = path[i]
                
                # Check bounds
                if not (0 <= r < grid_size and 0 <= c < grid_size):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.OUT_OF_BOUNDS,
                        error_message=f"Path point ({r}, {c}) is out of bounds",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Check obstacles
                if grid[r][c] == 1:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.OBSTACLE_COLLISION,
                        error_message=f"Path collides with obstacle at ({r}, {c})",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Check continuity (except for first point)
                if i > 0:
                    prev_r, prev_c = path[i-1]
                    if abs(r - prev_r) + abs(c - prev_c) != 1:
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.INVALID_PATH,
                            error_message=f"Path jumps from ({prev_r}, {prev_c}) to ({r}, {c})",
                            execution_time_ms=(time.time() - start_time) * 1000
                        )
            
            # Check checkpoints
            path_set = set(tuple(p) for p in path)
            for cp in checkpoints:
                if cp not in path_set:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.MISSING_CHECKPOINT,
                        error_message=f"Path does not visit checkpoint {cp}",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
            
            return SolutionResult(
                is_valid=True,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        except DataVerificationError:
            raise
        except Exception as e:
            raise DataVerificationError(f"Unexpected error during Pathfinding verification: {e}")

    def verify_solution(self, instance: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """
        Verify a solution for any supported puzzle type.
        
        Args:
            instance: The puzzle instance dictionary.
            solution: The proposed solution dictionary.
        
        Returns:
            SolutionResult indicating validity.
        
        Raises:
            DataVerificationError: If the puzzle type is unsupported or verification fails.
        """
        puzzle_type = instance.get("puzzle_type")
        
        if puzzle_type == "sudoku":
            return self.verify_sudoku(instance, solution)
        elif puzzle_type == "pathfinding":
            return self.verify_pathfinding(instance, solution)
        else:
            raise DataVerificationError(f"Unsupported puzzle type: {puzzle_type}")

def verify_solution(instance: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
    """
    Convenience function to verify a solution.
    """
    verifier = PuzzleVerifier()
    return verifier.verify_solution(instance, solution)

def main():
    """
    Command-line entry point for verifying solutions.
    
    Usage:
        python -m code.dataset.verifier --instance <path> --solution <path>
    
    This script verifies a solution against an instance and prints the result.
    It implements strict fail-loudly logic: any verification failure raises an exception.
    """
    import argparse
    import logging
    from code.utils.logger import setup_logging

    parser = argparse.ArgumentParser(description="Verify puzzle solutions.")
    parser.add_argument("--instance", type=str, required=True, help="Path to instance JSON file")
    parser.add_argument("--solution", type=str, required=True, help="Path to solution JSON file")

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        with open(args.instance, 'r') as f:
            instance = json.load(f)
        
        with open(args.solution, 'r') as f:
            solution = json.load(f)
        
        result = verify_solution(instance, solution)
        
        if result.is_valid:
            logger.info(f"Solution is VALID. Time: {result.execution_time_ms:.2f}ms")
        else:
            logger.error(f"Solution is INVALID. Code: {result.error_code}, Message: {result.error_message}")
            # Fail loudly: exit with error code
            sys.exit(1)
    
    except DataVerificationError as e:
        logger.error(f"CRITICAL: Verification failed with error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CRITICAL: Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()