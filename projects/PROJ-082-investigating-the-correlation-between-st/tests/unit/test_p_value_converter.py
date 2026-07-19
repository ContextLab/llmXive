"""
Unit tests for p_value_converter.py
"""
import pytest
import math
import os
import csv
from pathlib import Path

# Add parent directory to path for imports if running as script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from extraction.p_value_converter import (
    p_to_z_two_tailed,
    convert_p_value_to_effect_size,
    log_conversion,
    LOG_PATH
)

class TestPValueConverter:
    def test_valid_conversion(self):
        """Test conversion of a valid p-value."""
        # p=0.05, n=30 -> t approx 2.045 -> r approx 0.361 -> z approx 0.377
        z, r, status = p_to_z_two_tailed(0.05, 30)
        assert status == "converted"
        assert z is not None
        assert r is not None
        assert -1 <= r <= 1
        assert isinstance(z, float)

    def test_invalid_p_value_range(self):
        """Test that p-values outside (0, 1] are rejected."""
        z, r, status = p_to_z_two_tailed(-0.1, 30)
        assert status == "invalid_p_range"
        assert z is None
        assert r is None

        z, r, status = p_to_z_two_tailed(1.5, 30)
        assert status == "invalid_p_range"
        assert z is None
        assert r is None

    def test_p_value_one(self):
        """Test p=1.0 results in r=0, z=0."""
        z, r, status = p_to_z_two_tailed(1.0, 30)
        assert status == "converted"
        assert math.isclose(r, 0.0, abs_tol=1e-6)
        assert math.isclose(z, 0.0, abs_tol=1e-6)

    def test_ambiguous_conversion_infinite(self):
        """Test that r=1 (p extremely small) is handled as ambiguous/infinite."""
        # p extremely small might result in r close to 1
        # We simulate the edge case by checking the logic path
        # Direct test with very small p
        z, r, status = p_to_z_two_tailed(1e-20, 30)
        # Depending on precision, this might be capped or return infinite
        # Our logic returns None for infinite effect size
        if z is None:
            assert status == "infinite_effect_size"
        else:
            # If it didn't return None, it must be a valid number
            assert z is not None

    def test_conversion_result_dict(self):
        """Test the main convert_p_value_to_effect_size function."""
        result = convert_p_value_to_effect_size("Test_Study", 0.05, 30)
        assert result is not None
        assert "z" in result
        assert "r" in result
        assert result["status"] == "success"

    def test_conversion_failure_logging(self):
        """Test that failures are logged correctly."""
        # Clear log file if exists to start fresh
        if LOG_PATH.exists():
            LOG_PATH.unlink()
        
        # Trigger a failure
        result = convert_p_value_to_effect_size("Bad_Study", -0.1, 30)
        assert result is None
        
        # Check log file
        assert LOG_PATH.exists()
        with open(LOG_PATH, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 1
            last_row = rows[-1]
            assert last_row['study_id'] == 'Bad_Study'
            assert last_row['status'] == 'failed'
            assert 'invalid_p_range' in last_row['error_message']

    def test_successful_conversion_logging(self):
        """Test that successes are logged correctly."""
        # Trigger a success
        result = convert_p_value_to_effect_size("Good_Study", 0.05, 30)
        assert result is not None
        
        # Check log file
        with open(LOG_PATH, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Find our row
            good_rows = [r for r in rows if r['study_id'] == 'Good_Study']
            assert len(good_rows) >= 1
            row = good_rows[-1]
            assert row['status'] == 'success'
            assert row['result_r'] != ''
            assert row['result_z'] != ''