"""
Unit tests for compliance plausibility validation logic.

Tests the plausibility validation (0 <= minutes <= 1440) for daily logs
as specified in FR-010.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the code directory to the path for imports
# Assuming this test runs from the project root or tests/unit
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from validation.compliance_plausibility import validate_plausibility


class TestPlausibilityValidation:
    """Tests for the validate_plausibility function."""

    def test_valid_minutes_zero(self):
        """Test that 0 minutes is considered valid."""
        result = validate_plausibility(0)
        assert result is True

    def test_valid_minutes_max(self):
        """Test that 1440 minutes (24 hours) is considered valid."""
        result = validate_plausibility(1440)
        assert result is True

    def test_valid_minutes_mid_range(self):
        """Test that a mid-range value (e.g., 600) is valid."""
        result = validate_plausibility(600)
        assert result is True

    def test_invalid_minutes_negative(self):
        """Test that negative minutes are invalid."""
        result = validate_plausibility(-1)
        assert result is False

    def test_invalid_minutes_exceeds_day(self):
        """Test that minutes exceeding 1440 are invalid."""
        result = validate_plausibility(1441)
        assert result is False

    def test_invalid_minutes_large(self):
        """Test that a large number of minutes is invalid."""
        result = validate_plausibility(5000)
        assert result is False

    def test_invalid_type_string(self):
        """Test that string input is handled gracefully (should be False)."""
        # Depending on implementation, this might raise TypeError or return False
        # Assuming the function checks types or comparisons fail gracefully
        try:
            result = validate_plausibility("invalid")
            assert result is False
        except (TypeError, ValueError):
            # If it raises an error, that's also a form of failing validation
            pass

    def test_invalid_type_none(self):
        """Test that None input is handled gracefully."""
        try:
            result = validate_plausibility(None)
            assert result is False
        except (TypeError, ValueError):
            pass

    def test_float_minutes_valid(self):
        """Test that float minutes within range are valid."""
        result = validate_plausibility(600.5)
        assert result is True

    def test_float_minutes_invalid(self):
        """Test that float minutes outside range are invalid."""
        result = validate_plausibility(1440.1)
        assert result is False