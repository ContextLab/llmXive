"""
Unit tests for code/dataset/verifier.py.
Focus: Known valid/invalid solutions and rejection logic.
"""
import json
import pytest
import sys
import os
from pathlib import Path

# Ensure code/ is on path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.dataset.verifier import PuzzleVerifier, ErrorCodes, SolutionResult, DataVerificationError


@pytest.fixture
def verifier():
    """Instantiate the PuzzleVerifier."""
    return PuzzleVerifier()


@pytest.fixture
def valid_puzzle():
    """
    Return a valid puzzle instance (Sudoku variant) with a known correct solution.
    This fixture defines the ground truth for validation.
    """
    # Simple 4x4 Sudoku-like puzzle for speed
    return {
        "constraints": [
            "Each row must contain distinct integers from 1 to 4.",
            "Each column must contain distinct integers from 1 to 4.",
            "Each 2x2 block must contain distinct integers from 1 to 4."
        ],
        "initial_state": {
            "grid": [
                [1, 2, 0, 0],
                [3, 4, 0, 0],
                [0, 0, 1, 2],
                [0, 0, 3, 4]
            ]
        },
        "target_state": {
            "grid": [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [2, 1, 4, 3],
                [4, 3, 2, 1]
            ]
        },
        "metadata": {
            "source_id": "test_valid_001",
            "generation_seed": 42
        }
    }


@pytest.fixture
def invalid_puzzle():
    """
    Return a puzzle instance where the provided solution violates constraints.
    """
    return {
        "constraints": [
            "Each row must contain distinct integers from 1 to 4.",
            "Each column must contain distinct integers from 1 to 4."
        ],
        "initial_state": {
            "grid": [
                [1, 2, 0, 0],
                [3, 4, 0, 0],
                [0, 0, 1, 2],
                [0, 0, 3, 4]
            ]
        },
        "target_state": {
            "grid": [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [2, 1, 4, 3],
                [4, 3, 2, 1]
            ]
        },
        "provided_solution": {
            "grid": [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [2, 1, 4, 3],
                [4, 3, 1, 1]  # Violation: Duplicate '1' in last row, also '1' in col 3
            ]
        },
        "metadata": {
            "source_id": "test_invalid_001",
            "generation_seed": 43
        }
    }


@pytest.fixture
def malformed_solution_puzzle():
    """
    Return a puzzle where the solution structure is missing required fields.
    """
    return {
        "constraints": ["Row sum must be 10."],
        "initial_state": {"grid": [[1, 2, 3, 4]]},
        "target_state": {"grid": [[10, 0, 0, 0]]},
        "provided_solution": {
            "grid": [[1, 2, 3]]  # Missing a column
        },
        "metadata": {"source_id": "test_malformed", "generation_seed": 44}
    }


class TestVerifierRejectsInvalidSolution:
    """
    Test suite specifically for T010: Unit test for verifier with known invalid solutions.
    """

    def test_verifier_accepts_valid_solution(self, verifier, valid_puzzle):
        """
        Verify that the verifier returns True for a solution that satisfies all constraints.
        """
        result = verifier.verify(valid_puzzle)
        assert result.is_valid is True
        assert result.error_code is None

    def test_verifier_rejects_invalid_solution(self, verifier, invalid_puzzle):
        """
        T010 Core Test: Verify that the verifier rejects a solution that violates constraints.
        Specifically checks for duplicate values in rows/cols as defined in the puzzle.
        """
        result = verifier.verify(invalid_puzzle)
        assert result.is_valid is False
        # The verifier should identify a specific error code, e.g., DUPLICATE_ROW or DUPLICATE_COL
        assert result.error_code in [ErrorCodes.DUPLICATE_ROW, ErrorCodes.DUPLICATE_COL, ErrorCodes.CONSTRAINT_VIOLATION]
        assert result.message is not None
        assert "invalid" in result.message.lower() or "violation" in result.message.lower()

    def test_verifier_rejects_malformed_solution(self, verifier, malformed_solution_puzzle):
        """
        Verify that the verifier rejects a solution with incorrect structure (dimension mismatch).
        """
        result = verifier.verify(malformed_solution_puzzle)
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.MALFORMED_SOLUTION
        assert "dimension" in result.message.lower() or "shape" in result.message.lower()

    def test_verifier_handles_missing_solution(self, verifier, valid_puzzle):
        """
        Verify behavior when 'provided_solution' key is missing from the puzzle instance.
        """
        puzzle_no_sol = {k: v for k, v in valid_puzzle.items() if k != 'provided_solution'}
        result = verifier.verify(puzzle_no_sol)
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.MISSING_SOLUTION

    def test_verifier_handles_empty_grid(self, verifier):
        """
        Verify behavior when the solution grid is empty.
        """
        puzzle = {
            "constraints": ["Grid must be 2x2."],
            "initial_state": {"grid": []},
            "provided_solution": {"grid": []},
            "metadata": {"source_id": "test_empty"}
        }
        result = verifier.verify(puzzle)
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INVALID_DIMENSIONS

class TestVerifierEdgeCases:
    """
    Additional edge case tests to ensure robustness of the verifier.
    """

    def test_verifier_handles_non_integer_values(self, verifier):
        """
        Verify that the verifier rejects solutions containing non-integer values if integers are expected.
        """
        puzzle = {
            "constraints": ["Grid must contain integers."],
            "initial_state": {"grid": [[1, 2]]},
            "provided_solution": {"grid": [[1, "a"]]},
            "metadata": {"source_id": "test_non_int"}
        }
        result = verifier.verify(puzzle)
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.TYPE_MISMATCH

    def test_verifier_handles_null_values(self, verifier):
        """
        Verify that the verifier rejects solutions containing null/None where values are expected.
        """
        puzzle = {
            "constraints": ["Grid must be fully filled."],
            "initial_state": {"grid": [[1, 2]]},
            "provided_solution": {"grid": [[1, None]]},
            "metadata": {"source_id": "test_null"}
        }
        result = verifier.verify(puzzle)
        assert result.is_valid is False
        assert result.error_code == ErrorCodes.INCOMPLETE_SOLUTION