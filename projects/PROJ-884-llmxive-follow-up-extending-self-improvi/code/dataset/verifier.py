"""
Deterministic puzzle solution verifier.

Validates solution paths against puzzle constraints without LLM involvement.
Returns boolean validity and specific constraint violation codes.
"""
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from code.exceptions import VERIFIER_ERROR


class ErrorCodes(Enum):
    """Specific constraint violation codes for solution validation."""
    VALID = "VALID"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    DUPLICATE_COLUMN = "DUPLICATE_COLUMN"
    DUPLICATE_BOX = "DUPLICATE_BOX"
    INVALID_PATH = "INVALID_PATH"
    MISSING_CELL = "MISSING_CELL"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    INCORRECT_TARGET = "INCORRECT_TARGET"
    UNREACHABLE_TARGET = "UNREACHABLE_TARGET"
    INVALID_START_STATE = "INVALID_START_STATE"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class SolutionResult:
    """Result of solution verification."""
    is_valid: bool
    error_code: Optional[ErrorCodes] = None
    error_details: Optional[str] = None
    execution_time_ms: float = 0.0
    puzzle_id: Optional[str] = None
    solution_id: Optional[str] = None


class PuzzleVerifier:
    """
    Verifies solution paths for various puzzle types.
    
    Supports:
    - Sudoku variants (constraint satisfaction)
    - Pathfinding puzzles (graph traversal)
    - Arithmetic puzzles (expression evaluation)
    
    All verifications must complete within 100ms.
    """
    
    MAX_EXECUTION_TIME_MS = 100.0
    
    def __init__(self):
        self._start_time = None
    
    def _check_time_limit(self) -> bool:
        """Check if execution time exceeds limit."""
        if self._start_time is None:
            return False
        elapsed_ms = (time.time() - self._start_time) * 1000
        return elapsed_ms > self.MAX_EXECUTION_TIME_MS
    
    def verify_solution(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """
        Main entry point for solution verification.
        
        Args:
            puzzle: Puzzle instance with constraints, initial state, target
            solution: Solution path to validate
        
        Returns:
            SolutionResult with validity status and error details
        """
        self._start_time = time.time()
        puzzle_id = puzzle.get("id", "unknown")
        solution_id = solution.get("id", "unknown")
        
        try:
            # Validate puzzle structure
            puzzle_type = puzzle.get("type")
            if not puzzle_type:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.SYNTAX_ERROR,
                    error_details="Missing puzzle type",
                    execution_time_ms=(time.time() - self._start_time) * 1000,
                    puzzle_id=puzzle_id,
                    solution_id=solution_id
                )
            
            # Dispatch to type-specific verifier
            if puzzle_type == "sudoku":
                result = self._verify_sudoku(puzzle, solution)
            elif puzzle_type == "pathfinding":
                result = self._verify_pathfinding(puzzle, solution)
            elif puzzle_type == "arithmetic":
                result = self._verify_arithmetic(puzzle, solution)
            else:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.SYNTAX_ERROR,
                    error_details=f"Unknown puzzle type: {puzzle_type}",
                    execution_time_ms=(time.time() - self._start_time) * 1000,
                    puzzle_id=puzzle_id,
                    solution_id=solution_id
                )
            
            result.puzzle_id = puzzle_id
            result.solution_id = solution_id
            result.execution_time_ms = (time.time() - self._start_time) * 1000
            
            return result
            
        except VERIFIER_ERROR as e:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details=f"Verifier error: {str(e)}",
                execution_time_ms=(time.time() - self._start_time) * 1000,
                puzzle_id=puzzle_id,
                solution_id=solution_id
            )
        except Exception as e:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details=f"Unexpected error: {str(e)}",
                execution_time_ms=(time.time() - self._start_time) * 1000,
                puzzle_id=puzzle_id,
                solution_id=solution_id
            )
    
    def _verify_sudoku(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """Verify Sudoku variant solution."""
        if self._check_time_limit():
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details="Verification timeout",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        grid = solution.get("grid")
        if not grid or not isinstance(grid, list):
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Missing or invalid grid in solution",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Check grid dimensions
        n = puzzle.get("size", 9)
        if len(grid) != n:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details=f"Grid has {len(grid)} rows, expected {n}",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Check each row
        for i, row in enumerate(grid):
            if not isinstance(row, list) or len(row) != n:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_details=f"Row {i} has invalid length",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
            
            # Check for duplicates in row
            seen = set()
            for val in row:
                if val in seen:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_details=f"Duplicate value {val} in row {i}",
                        puzzle_id=puzzle.get("id"),
                        solution_id=solution.get("id")
                    )
                seen.add(val)
        
        # Check columns
        for col_idx in range(n):
            seen = set()
            for row_idx in range(n):
                val = grid[row_idx][col_idx]
                if val in seen:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_COLUMN,
                        error_details=f"Duplicate value {val} in column {col_idx}",
                        puzzle_id=puzzle.get("id"),
                        solution_id=solution.get("id")
                    )
                seen.add(val)
        
        # Check boxes (for standard Sudoku)
        if n == 9:
            box_size = 3
            for box_row in range(3):
                for box_col in range(3):
                    seen = set()
                    for i in range(box_size):
                        for j in range(box_size):
                            row_idx = box_row * box_size + i
                            col_idx = box_col * box_size + j
                            val = grid[row_idx][col_idx]
                            if val in seen:
                                return SolutionResult(
                                    is_valid=False,
                                    error_code=ErrorCodes.DUPLICATE_BOX,
                                    error_details=f"Duplicate value {val} in box ({box_row}, {box_col})",
                                    puzzle_id=puzzle.get("id"),
                                    solution_id=solution.get("id")
                                )
                            seen.add(val)
        
        # Check against initial state
        initial = puzzle.get("initial_state", [])
        for i, row in enumerate(initial):
            for j, val in enumerate(row):
                if val != 0 and val != grid[i][j]:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                        error_details=f"Initial state mismatch at ({i}, {j})",
                        puzzle_id=puzzle.get("id"),
                        solution_id=solution.get("id")
                    )
        
        return SolutionResult(
            is_valid=True,
            error_code=ErrorCodes.VALID,
            puzzle_id=puzzle.get("id"),
            solution_id=solution.get("id")
        )
    
    def _verify_pathfinding(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """Verify pathfinding solution."""
        if self._check_time_limit():
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details="Verification timeout",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        path = solution.get("path")
        if not path or not isinstance(path, list):
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Missing or invalid path in solution",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        grid = puzzle.get("grid", [])
        if not grid:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_START_STATE,
                error_details="Missing grid in puzzle",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        
        start = puzzle.get("start")
        end = puzzle.get("target")
        
        if not start or not end:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_START_STATE,
                error_details="Missing start or target in puzzle",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Check path starts at start position
        if path[0] != start:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details=f"Path does not start at {start}",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Check path ends at target
        if path[-1] != end:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INCORRECT_TARGET,
                error_details=f"Path does not end at {end}",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Check each step
        for i, pos in enumerate(path):
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_details=f"Invalid position format at step {i}",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
            
            x, y = pos
            if x < 0 or x >= rows or y < 0 or y >= cols:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.OUT_OF_BOUNDS,
                    error_details=f"Position ({x}, {y}) out of bounds",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
            
            if grid[x][y] == 1:  # Assuming 1 represents obstacle
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_details=f"Path crosses obstacle at ({x}, {y})",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
        
        # Check connectivity between consecutive steps
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            # Allow 8-directional movement (including diagonals)
            if dx > 1 or dy > 1 or (dx == 0 and dy == 0):
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_details=f"Invalid move from {path[i]} to {path[i+1]}",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
        
        return SolutionResult(
            is_valid=True,
            error_code=ErrorCodes.VALID,
            puzzle_id=puzzle.get("id"),
            solution_id=solution.get("id")
        )
    
    def _verify_arithmetic(self, puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
        """Verify arithmetic puzzle solution."""
        if self._check_time_limit():
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_details="Verification timeout",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        expression = solution.get("expression")
        if not expression:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH,
                error_details="Missing expression in solution",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        target = puzzle.get("target")
        if target is None:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_START_STATE,
                error_details="Missing target in puzzle",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        # Safe evaluation of arithmetic expression
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.SYNTAX_ERROR,
                error_details="Expression contains invalid characters",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        
        try:
            # Evaluate expression safely
            result = eval(expression, {"__builtins__": {}}, {})
            
            if abs(result - target) > 1e-6:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INCORRECT_TARGET,
                    error_details=f"Result {result} does not match target {target}",
                    puzzle_id=puzzle.get("id"),
                    solution_id=solution.get("id")
                )
            
            return SolutionResult(
                is_valid=True,
                error_code=ErrorCodes.VALID,
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
            
        except ZeroDivisionError:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                error_details="Division by zero in expression",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )
        except Exception as e:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.SYNTAX_ERROR,
                error_details=f"Expression evaluation error: {str(e)}",
                puzzle_id=puzzle.get("id"),
                solution_id=solution.get("id")
            )


def verify_solution(puzzle: Dict[str, Any], solution: Dict[str, Any]) -> SolutionResult:
    """
    Convenience function to verify a solution.
    
    Args:
        puzzle: Puzzle instance dictionary
        solution: Solution dictionary to validate
    
    Returns:
        SolutionResult indicating validity and error details
    """
    verifier = PuzzleVerifier()
    return verifier.verify_solution(puzzle, solution)
    

def main():
    """Test the verifier with sample puzzles and solutions."""
    # Test Sudoku
    sudoku_puzzle = {
        "id": "sudoku_001",
        "type": "sudoku",
        "size": 9,
        "initial_state": [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9]
        ]
    }
    
    valid_sudoku_solution = {
        "id": "sol_001",
        "grid": [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9]
        ]
    }
    
    result = verify_solution(sudoku_puzzle, valid_sudoku_solution)
    print(f"Sudoku Valid: {result.is_valid}, Code: {result.error_code}, Time: {result.execution_time_ms:.2f}ms")
    
    # Test invalid Sudoku (duplicate in row)
    invalid_sudoku_solution = {
        "id": "sol_002",
        "grid": [
            [5, 3, 4, 6, 7, 8, 9, 1, 1],  # Duplicate 1
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9]
        ]
    }
    
    result = verify_solution(sudoku_puzzle, invalid_sudoku_solution)
    print(f"Sudoku Invalid: {result.is_valid}, Code: {result.error_code}, Time: {result.execution_time_ms:.2f}ms")
    
    # Test Pathfinding
    path_puzzle = {
        "id": "path_001",
        "type": "pathfinding",
        "grid": [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 1, 0, 0]
        ],
        "start": [0, 0],
        "target": [3, 3]
    }
    
    valid_path_solution = {
        "id": "path_sol_001",
        "path": [[0, 0], [0, 1], [0, 2], [0, 3], [1, 3], [2, 3], [3, 3]]
    }
    
    result = verify_solution(path_puzzle, valid_path_solution)
    print(f"Path Valid: {result.is_valid}, Code: {result.error_code}, Time: {result.execution_time_ms:.2f}ms")
    
    # Test Arithmetic
    arith_puzzle = {
        "id": "arith_001",
        "type": "arithmetic",
        "numbers": [1, 3, 4, 6],
        "target": 24
    }
    
    valid_arith_solution = {
        "id": "arith_sol_001",
        "expression": "6 / (1 - 3 / 4)"
    }
    
    result = verify_solution(arith_puzzle, valid_arith_solution)
    print(f"Arithmetic Valid: {result.is_valid}, Code: {result.error_code}, Time: {result.execution_time_ms:.2f}ms")


if __name__ == "__main__":
    main()
