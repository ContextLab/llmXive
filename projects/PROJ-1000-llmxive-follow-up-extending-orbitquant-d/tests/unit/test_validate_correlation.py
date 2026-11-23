"""
Unit tests for code/validation/validate_correlation.py (Task T023b).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from validation.validate_correlation import validate_correlation_results, SIGNIFICANCE_THRESHOLD


class TestValidateCorrelation:
    """Tests for the validate_correlation_results function."""

    def test_file_not_found(self, tmp_path):
        """Test that validation fails when the file does not exist."""
        non_existent_path = tmp_path / "missing.json"
        assert validate_correlation_results(non_existent_path) is False

    def test_invalid_json(self, tmp_path):
        """Test that validation fails on invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ this is not json }")
        assert validate_correlation_results(bad_file) is False

    def test_missing_required_keys(self, tmp_path):
        """Test that validation fails if required keys are missing."""
        good_file = tmp_path / "missing_keys.json"
        # Missing 'p_value'
        data = {"correlation_coefficient": 0.5, "num_samples": 100}
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is False

    def test_p_value_invalid_type(self, tmp_path):
        """Test that validation fails if p_value is not a number."""
        good_file = tmp_path / "bad_type.json"
        data = {"p_value": "low", "correlation_coefficient": 0.5, "num_samples": 100}
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is False

    def test_p_value_out_of_range(self, tmp_path):
        """Test that validation fails if p_value is outside [0, 1]."""
        good_file = tmp_path / "out_of_range.json"
        data = {"p_value": 1.5, "correlation_coefficient": 0.5, "num_samples": 100}
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is False

    def test_p_value_significant(self, tmp_path):
        """Test that validation passes when p-value < 0.05."""
        good_file = tmp_path / "significant.json"
        data = {
            "p_value": 0.01,
            "correlation_coefficient": 0.85,
            "num_samples": 500
        }
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is True

    def test_p_value_not_significant(self, tmp_path):
        """Test that validation fails when p-value >= 0.05."""
        good_file = tmp_path / "not_significant.json"
        data = {
            "p_value": 0.06,
            "correlation_coefficient": 0.12,
            "num_samples": 500
        }
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is False

    def test_p_value_boundary(self, tmp_path):
        """Test behavior exactly at the threshold (0.05)."""
        good_file = tmp_path / "boundary.json"
        # Should fail because it is NOT strictly less than
        data = {
            "p_value": 0.05,
            "correlation_coefficient": 0.2,
            "num_samples": 1000
        }
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is False

    def test_p_value_just_below_boundary(self, tmp_path):
        """Test behavior just below the threshold."""
        good_file = tmp_path / "just_below.json"
        data = {
            "p_value": 0.049999,
            "correlation_coefficient": 0.3,
            "num_samples": 1000
        }
        good_file.write_text(json.dumps(data))
        assert validate_correlation_results(good_file) is True