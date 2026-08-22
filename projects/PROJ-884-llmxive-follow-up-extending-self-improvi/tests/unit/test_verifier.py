"""
Unit tests for code/dataset/verifier.py
Focus: test_verifier_rejects_invalid_solution
"""
import json
import os
import sys
import pytest
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.dataset.verifier import PuzzleVerifier, SolutionResult, ErrorCodes, DataVerificationError

class TestVerifierRejectsInvalidSolution:
    """
    Tests that the verifier correctly identifies and rejects invalid solutions.
    This is a critical contract test for US1.
    """

    def test_verifier_rejects_sudoku_duplicate_row(self):
        """
        Test that a Sudoku solution with a duplicate row is rejected.
        """
        # Setup: A 9x9 Sudoku grid that violates the row constraint
        # Row 0 has two 5s
        puzzle = {
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
            ],
            "target_state": [
                [5, 3, 4, 6, 7, 8, 9, 1, 2],
                [6, 7, 2, 1, 9, 5, 3, 4, 8], # Intentional duplicate: 5 appears twice in row 0 (indices 0 and 8)
                [1, 9, 8, 3, 4, 2, 5, 6, 7],
                [8, 5, 9, 7, 6, 1, 4, 2, 3],
                [4, 2, 6, 8, 5, 3, 7, 9, 1],
                [7, 1, 3, 9, 2, 4, 8, 5, 6],
                [9, 6, 1, 5, 3, 7, 2, 8, 4],
                [2, 8, 7, 4, 1, 9, 6, 3, 5],
                [3, 4, 5, 2, 8, 6, 1, 7, 9]
            ]
        }

        # The solution provided has a duplicate 5 in the first row (positions 0 and 8)
        # Actually, let's make a clearer invalid solution:
        # Row 0: [5, 3, 4, 6, 7, 8, 9, 1, 5] -> Two 5s
        invalid_solution = {
            "puzzle_id": "test_sudoku_dup_row",
            "solution": [
                [5, 3, 4, 6, 7, 8, 9, 1, 5], # Invalid: two 5s
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

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.DUPLICATE_ROW
        assert "Row 0" in result.message

    def test_verifier_rejects_sudoku_invalid_column(self):
        """
        Test that a Sudoku solution with an invalid column is rejected.
        """
        invalid_solution = {
            "puzzle_id": "test_sudoku_dup_col",
            "solution": [
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
        # Manually corrupt column 0 to have two 5s
        invalid_solution["solution"][0][0] = 5
        invalid_solution["solution"][4][0] = 5 # Duplicate in col 0

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.DUPLICATE_COLUMN
        assert "Column 0" in result.message

    def test_verifier_rejects_pathfinding_invalid_step(self):
        """
        Test that a pathfinding solution with an invalid step (diagonal or jump) is rejected.
        """
        puzzle = {
            "type": "pathfinding",
            "grid_size": 5,
            "obstacles": [[2, 2]],
            "start": [0, 0],
            "end": [4, 4]
        }

        # Solution that jumps from [0,0] to [0,2] (skipping [0,1])
        invalid_solution = {
            "puzzle_id": "test_path_jump",
            "path": [
                [0, 0],
                [0, 2], # Invalid: jumped over [0,1]
                [0, 3],
                [1, 3],
                [2, 3],
                [3, 3],
                [4, 3],
                [4, 4]
            ]
        }

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INVALID_PATH
        assert "invalid step" in result.message.lower()

    def test_verifier_rejects_pathfinding_out_of_bounds(self):
        """
        Test that a pathfinding solution going out of bounds is rejected.
        """
        invalid_solution = {
            "puzzle_id": "test_path_oob",
            "path": [
                [0, 0],
                [0, 1],
                [0, 2],
                [0, 3],
                [0, 4],
                [0, 5], # Out of bounds (grid size 5, max index 4)
                [1, 5],
                [2, 5],
                [3, 5],
                [4, 5]
            ]
        }

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.OUT_OF_BOUNDS
        assert "out of bounds" in result.message.lower()

    def test_verifier_rejects_pathfinding_collision(self):
        """
        Test that a pathfinding solution hitting an obstacle is rejected.
        """
        invalid_solution = {
            "puzzle_id": "test_path_collision",
            "path": [
                [0, 0],
                [1, 0],
                [2, 0],
                [2, 1],
                [2, 2] # Hits obstacle at [2, 2]
            ]
        }

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.COLLISION
        assert "collision" in result.message.lower()

    def test_verifier_rejects_arithmetic_wrong_result(self):
        """
        Test that an arithmetic puzzle solution with the wrong result is rejected.
        """
        puzzle = {
            "type": "arithmetic",
            "expression": "2 + 3 * 4",
            "expected_result": 14
        }

        invalid_solution = {
            "puzzle_id": "test_arith_wrong",
            "result": 20 # (2+3)*4 = 20, but 2+3*4 = 14
        }

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INCORRECT_RESULT
        assert "incorrect result" in result.message.lower()

    def test_verifier_rejects_malformed_input(self):
        """
        Test that a solution with missing required fields raises an error.
        """
        verifier = PuzzleVerifier()
        
        # Missing 'solution' or 'path' or 'result' depending on type
        invalid_solution = {
            "puzzle_id": "test_malformed",
            # Missing the actual solution data
        }

        with pytest.raises(DataVerificationError):
            verifier.verify(invalid_solution)

    def test_verifier_rejects_type_mismatch(self):
        """
        Test that a solution for the wrong puzzle type is rejected.
        """
        # A Sudoku puzzle expecting a grid
        puzzle = {
            "type": "sudoku",
            "size": 9,
            "initial_state": [[0]*9 for _ in range(9)],
            "target_state": [[0]*9 for _ in range(9)]
        }

        # But the solution is a path (for pathfinding)
        invalid_solution = {
            "puzzle_id": "test_type_mismatch",
            "solution": [[0, 0], [0, 1], [1, 1]] # Path format, not grid
        }

        verifier = PuzzleVerifier()
        result = verifier.verify(invalid_solution)

        assert result.is_valid is False
        assert result.error_code == ErrorCodes.TYPE_MISMATCH

if __name__ == "__main__":
    pytest.main([__file__, "-v"])