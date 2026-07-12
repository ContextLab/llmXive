"""
Unit tests for code/dataset/generator.py.

This module contains contract tests to ensure the generator handles
edge cases correctly, specifically empty input scenarios.
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.dataset.generator import generate_puzzles, validate_puzzle_input
from code.exceptions import PARSE_FAILURE


class TestGeneratorEmptyInput:
    """Contract tests for handling empty input in the puzzle generator."""

    def test_generator_handles_empty_input(self):
        """
        Contract: When the generator receives an empty list of constraints
        or an empty configuration, it must return an empty list of puzzles
        rather than crashing or generating invalid artifacts.
        """
        # Test with empty constraints list
        empty_constraints = []
        
        # The generator should handle this gracefully and return empty list
        # It should NOT raise an exception unless explicitly designed to fail on empty input
        # Based on robust design principles, returning empty is safer for pipeline flow
        result = generate_puzzles(empty_constraints)
        
        assert isinstance(result, list), "Generator must return a list"
        assert len(result) == 0, "Generator must return empty list for empty input"

    def test_generator_handles_empty_config(self):
        """
        Contract: When the generator receives an empty configuration dictionary,
        it must raise a PARSE_FAILURE or return empty, depending on strictness.
        Here we test for graceful handling (returning empty or raising specific error).
        """
        empty_config = {}
        
        # Test with empty config
        # We expect either an empty list or a specific exception
        try:
            result = generate_puzzles([], config=empty_config)
            assert isinstance(result, list)
            assert len(result) == 0
        except PARSE_FAILURE:
            # If the design requires strict validation, this is acceptable
            pass

    def test_validate_puzzle_input_empty(self):
        """
        Contract: The validation helper should reject empty puzzle definitions.
        """
        empty_puzzle = {}
        is_valid, error_code = validate_puzzle_input(empty_puzzle)
        
        assert is_valid is False
        assert error_code is not None
        assert "EMPTY" in error_code or error_code == "INVALID_FORMAT"

    def test_generator_with_none_constraints(self):
        """
        Contract: Passing None as constraints should be handled gracefully.
        """
        with pytest.raises((TypeError, PARSE_FAILURE)):
            generate_puzzles(None)

    def test_generator_with_only_whitespace_constraints(self):
        """
        Contract: Constraints that are effectively empty (e.g., list of empty strings)
        should result in no puzzles generated.
        """
        # Assuming constraints are strings or dicts; if strings, empty ones should be skipped
        # This test depends on the specific constraint format in generator.py
        # For now, we test the list structure
        whitespace_constraints = ["", "   ", "\t"]
        
        result = generate_puzzles(whitespace_constraints)
        
        # Should produce no valid puzzles
        assert len(result) == 0, "Whitespace-only constraints should not generate puzzles"

    def test_generator_empty_output_structure(self):
        """
        Contract: Even when returning empty, the structure of the return type
        must be consistent (list of dicts) to prevent downstream errors.
        """
        result = generate_puzzles([])
        
        assert isinstance(result, list)
        # If there were items, they would be dicts. Empty list satisfies this.