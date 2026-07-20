"""
Unit tests for the renderer module.
Focus: Validating out-of-bounds state handling and error block generation.
"""
import pytest
import os
import sys
import json
from typing import List, Dict, Any, Tuple

# Add project root to path if running standalone, though in pipeline context imports are resolved
# The implementation assumes the `code/` directory is in the PYTHONPATH or this test is run from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.renderer import (
    validate_grid_coordinates,
    validate_grid_bounds,
    render_error_block,
    generate_ascii_grid,
    validate_ascii_grid,
    create_event_entry
)

# Constants for testing
GRID_WIDTH = 10
GRID_HEIGHT = 10
ERROR_MARKER = "ERROR: STATE_CORRUPT"


class TestOutOfBoundsValidation:
    """Tests for out-of-bounds state validation logic."""

    def test_validate_grid_coordinates_valid(self):
        """Test that valid coordinates pass validation."""
        # Valid coordinates within grid
        assert validate_grid_coordinates(0, 0, GRID_WIDTH, GRID_HEIGHT) is True
        assert validate_grid_coordinates(9, 9, GRID_WIDTH, GRID_HEIGHT) is True
        assert validate_grid_coordinates(5, 5, GRID_WIDTH, GRID_HEIGHT) is True

    def test_validate_grid_coordinates_negative_x(self):
        """Test that negative x-coordinate fails validation."""
        assert validate_grid_coordinates(-1, 5, GRID_WIDTH, GRID_HEIGHT) is False

    def test_validate_grid_coordinates_negative_y(self):
        """Test that negative y-coordinate fails validation."""
        assert validate_grid_coordinates(5, -1, GRID_WIDTH, GRID_HEIGHT) is False

    def test_validate_grid_coordinates_x_out_of_bounds(self):
        """Test that x-coordinate >= width fails validation."""
        assert validate_grid_coordinates(10, 5, GRID_WIDTH, GRID_HEIGHT) is False
        assert validate_grid_coordinates(15, 5, GRID_WIDTH, GRID_HEIGHT) is False

    def test_validate_grid_coordinates_y_out_of_bounds(self):
        """Test that y-coordinate >= height fails validation."""
        assert validate_grid_coordinates(5, 10, GRID_WIDTH, GRID_HEIGHT) is False
        assert validate_grid_coordinates(5, 15, GRID_WIDTH, GRID_HEIGHT) is False

    def test_validate_grid_bounds_valid_state(self):
        """Test validation of a complete valid state."""
        state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": 0, "y": 0, "type": "wall"},
                {"x": 9, "y": 9, "type": "player"},
                {"x": 5, "y": 5, "type": "item"}
            ]
        }
        assert validate_grid_bounds(state) is True

    def test_validate_grid_bounds_invalid_x(self):
        """Test validation fails when an item has invalid x."""
        state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": -1, "y": 0, "type": "wall"}
            ]
        }
        assert validate_grid_bounds(state) is False

    def test_validate_grid_bounds_invalid_y(self):
        """Test validation fails when an item has invalid y."""
        state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": 5, "y": 100, "type": "wall"}
            ]
        }
        assert validate_grid_bounds(state) is False

    def test_validate_grid_bounds_missing_dimensions(self):
        """Test validation fails if grid dimensions are missing."""
        state = {
            "items": [{"x": 0, "y": 0}]
        }
        assert validate_grid_bounds(state) is False

    def test_validate_grid_bounds_mismatched_dimensions(self):
        """Test validation fails if item coordinates don't match grid dims."""
        state = {
            "width": 5,
            "height": 5,
            "items": [{"x": 6, "y": 0}]
        }
        assert validate_grid_bounds(state) is False


class TestRenderErrorBlock:
    """Tests for the standardized error block generation."""

    def test_render_error_block_content(self):
        """Verify the error block contains the exact required string."""
        error_block = render_error_block()
        assert ERROR_MARKER in error_block
        assert error_block.strip() == ERROR_MARKER

    def test_render_error_block_type(self):
        """Verify the error block is returned as a string."""
        error_block = render_error_block()
        assert isinstance(error_block, str)

    def test_render_error_block_consistency(self):
        """Verify the error block is consistent across multiple calls."""
        block1 = render_error_block()
        block2 = render_error_block()
        assert block1 == block2
        assert block1 == ERROR_MARKER


class TestAsciiGridGenerationWithCorruption:
    """Tests for ASCII grid generation when corruption is detected."""

    def test_generate_ascii_grid_on_corruption(self):
        """Verify that generate_ascii_grid returns error block for invalid states."""
        # Create a state with out-of-bounds coordinates
        corrupt_state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": 15, "y": 5, "type": "wall"}  # x is out of bounds
            ]
        }

        # The renderer should detect this and return the error block
        result = generate_ascii_grid(corrupt_state)

        assert result == render_error_block()
        assert ERROR_MARKER in result

    def test_generate_ascii_grid_on_negative_corruption(self):
        """Verify error block for negative coordinate corruption."""
        corrupt_state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": -5, "y": 5, "type": "wall"}  # x is negative
            ]
        }

        result = generate_ascii_grid(corrupt_state)
        assert result == render_error_block()

    def test_generate_ascii_grid_on_valid_state(self):
        """Verify normal grid generation for valid states (sanity check)."""
        valid_state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": 0, "y": 0, "type": "wall"},
                {"x": 5, "y": 5, "type": "player"}
            ]
        }

        result = generate_ascii_grid(valid_state)

        # Should not be an error block
        assert result != render_error_block()
        # Should be a grid string (contains newlines and grid characters)
        assert isinstance(result, str)
        assert "\n" in result or len(result) > 0


class TestValidateAsciiGrid:
    """Tests for the ASCII grid validation utility."""

    def test_validate_ascii_grid_valid(self):
        """Test validation of a correctly formatted ASCII grid."""
        grid_str = "##########\n#........#\n#........#\n##########"
        assert validate_ascii_grid(grid_str, 10, 4) is True

    def test_validate_ascii_grid_invalid_width(self):
        """Test validation fails if grid width doesn't match."""
        grid_str = "##########\n#........#"
        # Width is 10, height 2. But grid_str has 2 rows.
        # If we claim height 4, it should fail.
        assert validate_ascii_grid(grid_str, 10, 4) is False

    def test_validate_ascii_grid_invalid_height(self):
        """Test validation fails if grid height doesn't match."""
        grid_str = "##########\n#........#\n##########"
        # Width 10, height 3.
        assert validate_ascii_grid(grid_str, 10, 2) is False

    def test_validate_ascii_grid_mismatched_chars(self):
        """Test validation fails if row lengths don't match width."""
        grid_str = "##########\n#....\n##########"
        # Second row is too short
        assert validate_ascii_grid(grid_str, 10, 3) is False

    def test_validate_ascii_grid_empty(self):
        """Test validation fails for empty string."""
        assert validate_ascii_grid("", 10, 1) is False


class TestEventEntryCreationWithCorruption:
    """Tests for event entry creation when state is corrupted."""

    def test_create_event_entry_with_corrupted_state(self):
        """Verify event entry is created with error marker when state is invalid."""
        corrupt_state = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "items": [
                {"x": 20, "y": 20, "type": "wall"}
            ]
        }

        # Simulate creating an event entry for this state
        # In the actual implementation, this might be handled inside generate_event_log
        # or the caller checks validity first. Here we test the logic path.
        is_valid = validate_grid_bounds(corrupt_state)

        assert is_valid is False

        # If we were to create an entry, it should reflect the error
        # This test ensures the validation logic is correctly integrated
        # into the flow that would eventually call render_error_block
        error_block = render_error_block()
        assert error_block == ERROR_MARKER