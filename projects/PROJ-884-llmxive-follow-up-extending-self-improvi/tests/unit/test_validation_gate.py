"""
Unit tests for T036: validation_gate.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dataset.validation_gate import load_json, save_json, validate_distribution

class TestValidationGateSchema:
    """Tests for T036b-verify: Verify validation_gate.json schema."""

    def test_schema_valid(self, tmp_path):
        """
        Assert the JSON structure matches the required schema:
        {"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}
        """
        test_data = {
            "status": "PASS",
            "reason": "Test reason",
            "distribution_stats": {"key": "value"}
        }
        output_file = tmp_path / "validation_gate.json"

        # Save test data
        with open(output_file, 'w') as f:
            json.dump(test_data, f)

        # Load and verify structure
        loaded = load_json(output_file)
        assert loaded is not None
        assert "status" in loaded
        assert loaded["status"] in ["PASS", "FAIL"]
        assert "reason" in loaded
        assert isinstance(loaded["reason"], str)
        assert "distribution_stats" in loaded
        assert isinstance(loaded["distribution_stats"], dict)

    def test_status_fail_reason_present(self, tmp_path):
        """Verify that a FAIL status includes a non-empty reason."""
        test_data = {
            "status": "FAIL",
            "reason": "Validation failed due to low power",
            "distribution_stats": {}
        }
        output_file = tmp_path / "validation_gate_fail.json"

        with open(output_file, 'w') as f:
            json.dump(test_data, f)

        loaded = load_json(output_file)
        assert loaded["status"] == "FAIL"
        assert len(loaded["reason"]) > 0

class TestValidateDistributionLogic:
    """Tests for the validation logic."""

    def test_missing_input_fails(self):
        """Test that missing or empty input results in FAIL."""
        is_valid, reason, stats = validate_distribution(None)
        assert is_valid is False
        assert "missing" in reason.lower() or "empty" in reason.lower()

    def test_invalid_distribution_fails(self):
        """Test that is_valid=False in input results in FAIL."""
        input_data = {
            "is_valid": False,
            "notes": "Type ratio mismatch",
            "power_estimate": 0.9
        }
        is_valid, reason, stats = validate_distribution(input_data)
        assert is_valid is False
        assert "Type ratio mismatch" in reason

    def test_low_power_fails(self):
        """Test that power_estimate < 0.8 results in FAIL."""
        input_data = {
            "is_valid": True,
            "notes": "OK",
            "power_estimate": 0.5,
            "distribution_stats": {"complexity_scaling": {"is_continuous": True}}
        }
        is_valid, reason, stats = validate_distribution(input_data)
        assert is_valid is False
        assert "power" in reason.lower()

    def test_continuous_scaling_passes(self):
        """Test that valid data with continuous scaling passes."""
        input_data = {
            "is_valid": True,
            "notes": "OK",
            "power_estimate": 0.95,
            "distribution_stats": {
                "complexity_scaling": {"is_continuous": True},
                "type_distribution": {"sudoku": 50, "pathfinding": 50}
            }
        }
        is_valid, reason, stats = validate_distribution(input_data)
        assert is_valid is True
        assert "passed" in reason.lower()

    def test_non_continuous_scaling_fails(self):
        """Test that non-continuous scaling fails."""
        input_data = {
            "is_valid": True,
            "notes": "OK",
            "power_estimate": 0.95,
            "distribution_stats": {
                "complexity_scaling": {"is_continuous": False},
                "type_distribution": {"sudoku": 50, "pathfinding": 50}
            }
        }
        is_valid, reason, stats = validate_distribution(input_data)
        assert is_valid is False
        assert "continuous" in reason.lower()
