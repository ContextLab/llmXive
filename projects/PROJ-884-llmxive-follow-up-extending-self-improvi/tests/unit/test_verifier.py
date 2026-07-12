import pytest
import json
import os
import sys
from pathlib import Path

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.dataset.verifier import verify_solution, SolutionResult
from code.exceptions import VERIFIER_ERROR

# Test fixtures
VALID_SUDOKU_SOLUTION = {
    "puzzle_id": "test_001",
    "type": "sudoku",
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
    ],
    "solution_path": ["step1", "step2", "step3"]
}

INVALID_SUDOKU_DUPLICATE_ROW = {
    "puzzle_id": "test_002",
    "type": "sudoku",
    "grid": [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9]  # Correct
    ],
    "solution_path": ["step1"],
    "error_type": "duplicate_row"
}

# Intentionally create an invalid grid for testing duplicate detection
INVALID_SUDOKU_GRID = [
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
# Modify to create a duplicate row (row 0 and row 1 are now identical in logic for testing)
INVALID_SUDOKU_GRID[1] = INVALID_SUDOKU_GRID[0].copy()

INVALID_SOLUTION_DATA = {
    "puzzle_id": "test_003",
    "type": "sudoku",
    "grid": INVALID_SUDOKU_GRID,
    "solution_path": []
}

INVALID_PATH_SOLUTION = {
    "puzzle_id": "test_004",
    "type": "pathfinding",
    "path": [
        {"x": 0, "y": 0},
        {"x": 0, "y": 0},  # Duplicate point (invalid for simple path)
        {"x": 0, "y": 1}
    ],
    "solution_path": ["step1"]
}

def test_verifier_rejects_invalid_solution():
    """
    Unit test for code/dataset/verifier.py with known invalid solutions.
    Specifically tests that the verifier rejects a solution with a duplicate row
    and returns the correct error code DUPLICATE_ROW.
    """
    # Test 1: Valid solution should pass
    result = verify_solution(VALID_SUDOKU_SOLUTION)
    assert result.is_valid is True
    assert result.error_code is None

    # Test 2: Invalid solution with duplicate row should fail
    result = verify_solution(INVALID_SOLUTION_DATA)
    assert result.is_valid is False
    assert result.error_code == "DUPLICATE_ROW"
    
    # Test 3: Invalid path solution
    result = verify_solution(INVALID_PATH_SOLUTION)
    assert result.is_valid is False
    assert result.error_code == "INVALID_PATH"

def test_verifier_handles_missing_fields():
    """
    Test that verifier raises appropriate errors for missing required fields.
    """
    incomplete_solution = {
        "puzzle_id": "test_005",
        "type": "sudoku"
        # Missing 'grid' and 'solution_path'
    }
    
    with pytest.raises(VERIFIER_ERROR):
        verify_solution(incomplete_solution)

def test_verifier_unsupported_type():
    """
    Test verifier behavior with unsupported puzzle types.
    """
    unsupported_solution = {
        "puzzle_id": "test_006",
        "type": "unsupported_type",
        "data": {}
    }
    
    result = verify_solution(unsupported_solution)
    assert result.is_valid is False
    assert result.error_code == "UNSUPPORTED_TYPE"
