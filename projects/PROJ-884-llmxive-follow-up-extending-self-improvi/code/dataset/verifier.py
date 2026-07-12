import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from code.exceptions import VERIFIER_ERROR

class ErrorCodes(Enum):
    DUPLICATE_ROW = "DUPLICATE_ROW"
    INVALID_PATH = "INVALID_PATH"
    UNSUPPORTED_TYPE = "UNSUPPORTED_TYPE"
    PARSE_FAILURE = "PARSE_FAILURE"
    MISSING_FIELD = "MISSING_FIELD"
    SUBGRID_INVALID = "SUBGRID_INVALID"
    COLUMN_INVALID = "COLUMN_INVALID"
    PATH_NOT_CONNECTED = "PATH_NOT_CONNECTED"
    PATH_OUT_OF_BOUNDS = "PATH_OUT_OF_BOUNDS"

@dataclass
class SolutionResult:
    is_valid: bool
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    details: Optional[str] = None

def verify_solution(solution_data: Dict[str, Any]) -> SolutionResult:
    """
    Verify a solution against a puzzle instance.
    
    Args:
        solution_data: Dictionary containing puzzle_id, type, grid/path, and solution_path
        
    Returns:
        SolutionResult with validity status, error code (if invalid), and execution time
        
    Raises:
        VERIFIER_ERROR: If required fields are missing or solution cannot be parsed
    """
    start_time = time.time()
    
    # Validate required fields
    required_fields = ["puzzle_id", "type"]
    for field in required_fields:
        if field not in solution_data:
            raise VERIFIER_ERROR(f"Missing required field: {field}")
    
    puzzle_type = solution_data["type"]
    
    try:
        if puzzle_type == "sudoku":
            return _verify_sudoku(solution_data, start_time)
        elif puzzle_type == "pathfinding":
            return _verify_pathfinding(solution_data, start_time)
        else:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.UNSUPPORTED_TYPE.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Unsupported puzzle type: {puzzle_type}"
            )
    except Exception as e:
        raise VERIFIER_ERROR(f"Verification failed: {str(e)}")

def _verify_sudoku(solution_data: Dict[str, Any], start_time: float) -> SolutionResult:
    """Verify a Sudoku solution with specific error codes."""
    if "grid" not in solution_data:
        raise VERIFIER_ERROR("Missing 'grid' field for sudoku puzzle")
        
    grid = solution_data["grid"]
    
    # Basic validation: must be 9x9
    if len(grid) != 9:
        return SolutionResult(
            is_valid=False,
            error_code=ErrorCodes.DUPLICATE_ROW.value,
            execution_time_ms=(time.time() - start_time) * 1000,
            details="Grid must be 9x9"
        )
        
    for row_idx, row in enumerate(grid):
        if len(row) != 9:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.DUPLICATE_ROW.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Row {row_idx} must have 9 elements"
            )
        
        # Check for duplicates in row
        if len(set(row)) != 9:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.DUPLICATE_ROW.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Row {row_idx} contains duplicate values"
            )
    
    # Check columns
    for col_idx in range(9):
        column = [grid[row_idx][col_idx] for row_idx in range(9)]
        if len(set(column)) != 9:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.COLUMN_INVALID.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Column {col_idx} contains duplicate values"
            )
    
    # Check 3x3 subgrids
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            subgrid = []
            for i in range(3):
                for j in range(3):
                    subgrid.append(grid[box_row + i][box_col + j])
            if len(set(subgrid)) != 9:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.SUBGRID_INVALID.value,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details=f"Subgrid at ({box_row}, {box_col}) contains duplicate values"
                )
    
    return SolutionResult(
        is_valid=True,
        execution_time_ms=(time.time() - start_time) * 1000
    )

def _verify_pathfinding(solution_data: Dict[str, Any], start_time: float) -> SolutionResult:
    """Verify a pathfinding solution with connectivity and bounds checks."""
    if "path" not in solution_data:
        raise VERIFIER_ERROR("Missing 'path' field for pathfinding puzzle")
    
    if "grid" not in solution_data:
        raise VERIFIER_ERROR("Missing 'grid' field for pathfinding puzzle")
        
    path = solution_data["path"]
    grid = solution_data["grid"]
    
    if not path:
        return SolutionResult(
            is_valid=False,
            error_code=ErrorCodes.INVALID_PATH.value,
            execution_time_ms=(time.time() - start_time) * 1000,
            details="Path cannot be empty"
        )
    
    # Check start and end points
    if "start" not in solution_data or "end" not in solution_data:
        raise VERIFIER_ERROR("Missing 'start' or 'end' field for pathfinding puzzle")
    
    start_point = solution_data["start"]
    end_point = solution_data["end"]
    
    # Validate start and end coordinates
    if path[0] != start_point or path[-1] != end_point:
        return SolutionResult(
            is_valid=False,
            error_code=ErrorCodes.INVALID_PATH.value,
            execution_time_ms=(time.time() - start_time) * 1000,
            details="Path must start at 'start' and end at 'end'"
        )
    
    # Check for duplicate points and connectivity
    seen_points = set()
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    
    for i, point in enumerate(path):
        if "x" not in point or "y" not in point:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Point at index {i} missing x or y coordinate"
            )
        
        x, y = point["x"], point["y"]
        
        # Check bounds
        if x < 0 or x >= cols or y < 0 or y >= rows:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.PATH_OUT_OF_BOUNDS.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Point ({x}, {y}) at index {i} is out of bounds"
            )
        
        # Check for obstacles
        if grid[y][x] == 1:  # Assuming 1 represents an obstacle
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Point ({x}, {y}) at index {i} is an obstacle"
            )
        
        point_tuple = (x, y)
        if point_tuple in seen_points:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_PATH.value,
                execution_time_ms=(time.time() - start_time) * 1000,
                details=f"Path contains duplicate point ({x}, {y}) at index {i}"
            )
        seen_points.add(point_tuple)
        
        # Check connectivity (adjacent points only)
        if i > 0:
            prev_point = path[i-1]
            dx = abs(point["x"] - prev_point["x"])
            dy = abs(point["y"] - prev_point["y"])
            if dx + dy != 1:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.PATH_NOT_CONNECTED.value,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details=f"Point at index {i} is not adjacent to previous point"
                )
    
    return SolutionResult(
        is_valid=True,
        execution_time_ms=(time.time() - start_time) * 1000
    )