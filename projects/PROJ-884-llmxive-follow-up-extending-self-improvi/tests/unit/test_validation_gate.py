"""
Unit tests for the validation gate functionality.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.dataset.validation_gate import load_json, save_json, validate_distribution

class TestValidationGateSchema:
    """Tests for the validation_gate.json schema."""

    def test_schema_valid(self, tmp_path):
        """
        Verify that the generated validation_gate.json matches the required schema:
        {"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}
        """
        # Create a mock distribution validation result
        mock_validation = {
            "is_valid": True,
            "power_estimate": 0.85,
            "sample_size": 100,
            "notes": ["All checks passed"],
            "distribution_stats": {
                "type_counts": {"sudoku": 50, "pathfinding": 50},
                "complexity_distribution": {"low": 30, "medium": 40, "high": 30}
            }
        }
        
        input_file = tmp_path / "distribution_validation.json"
        with open(input_file, 'w') as f:
            json.dump(mock_validation, f)
        
        output_file = tmp_path / "validation_gate.json"
        
        # Run the validation logic
        result = validate_distribution(
            load_json(input_file),
            min_power_estimate=0.8,
            min_sample_size=10
        )
        
        save_json(result, output_file)
        
        # Load and verify the output
        with open(output_file, 'r') as f:
            gate_data = json.load(f)
        
        # Check required fields
        assert "status" in gate_data, "Missing 'status' field"
        assert "reason" in gate_data, "Missing 'reason' field"
        assert "distribution_stats" in gate_data, "Missing 'distribution_stats' field"
        
        # Check status values
        assert gate_data["status"] in ["PASS", "FAIL"], f"Invalid status: {gate_data['status']}"
        
        # Check types
        assert isinstance(gate_data["reason"], str), "Reason must be a string"
        assert isinstance(gate_data["distribution_stats"], dict), "Distribution stats must be a dict"
        
        # Verify the specific outcome for our mock data
        assert gate_data["status"] == "PASS", "Expected PASS for valid mock data"
        assert gate_data["power_estimate"] == 0.85
        assert gate_data["sample_size"] == 100

    def test_schema_fail_case(self, tmp_path):
        """Verify the schema when validation fails."""
        mock_validation = {
            "is_valid": False,
            "power_estimate": 0.5,
            "sample_size": 5,
            "notes": ["Power too low"],
            "distribution_stats": {"type_counts": {}}
        }
        
        input_file = tmp_path / "distribution_validation.json"
        with open(input_file, 'w') as f:
            json.dump(mock_validation, f)
        
        output_file = tmp_path / "validation_gate.json"
        
        result = validate_distribution(
            load_json(input_file),
            min_power_estimate=0.8,
            min_sample_size=10
        )
        
        save_json(result, output_file)
        
        with open(output_file, 'r') as f:
            gate_data = json.load(f)
        
        assert gate_data["status"] == "FAIL"
        assert "Power estimate" in gate_data["reason"]
        assert "Sample size" in gate_data["reason"]

    def test_schema_missing_input_handling(self, tmp_path):
        """Verify behavior when input file is missing."""
        output_file = tmp_path / "validation_gate.json"
        non_existent_input = tmp_path / "non_existent.json"
        
        # Simulate the main logic's error handling
        try:
            load_json(non_existent_input)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            # This is expected
            pass

class TestValidationDistributionLogic:
    """Tests for the validation logic itself."""

    def test_passes_with_high_power_and_sample(self):
        """Test that high power and sample size result in PASS."""
        validation = {
            "is_valid": True,
            "power_estimate": 0.95,
            "sample_size": 200,
            "notes": [],
            "distribution_stats": {}
        }
        result = validate_distribution(validation, min_power_estimate=0.8, min_sample_size=10)
        assert result["status"] == "PASS"

    def test_fails_with_low_power(self):
        """Test that low power results in FAIL."""
        validation = {
            "is_valid": True,
            "power_estimate": 0.5,
            "sample_size": 200,
            "notes": [],
            "distribution_stats": {}
        }
        result = validate_distribution(validation, min_power_estimate=0.8, min_sample_size=10)
        assert result["status"] == "FAIL"
        assert "Power estimate" in result["reason"]

    def test_fails_with_low_sample_size(self):
        """Test that low sample size results in FAIL."""
        validation = {
            "is_valid": True,
            "power_estimate": 0.95,
            "sample_size": 5,
            "notes": [],
            "distribution_stats": {}
        }
        result = validate_distribution(validation, min_power_estimate=0.8, min_sample_size=10)
        assert result["status"] == "FAIL"
        assert "Sample size" in result["reason"]

    def test_fails_when_source_invalid(self):
        """Test that is_valid=False at source results in FAIL."""
        validation = {
            "is_valid": False,
            "power_estimate": 0.95,
            "sample_size": 200,
            "notes": ["Source validation failed"],
            "distribution_stats": {}
        }
        result = validate_distribution(validation, min_power_estimate=0.8, min_sample_size=10)
        assert result["status"] == "FAIL"
        assert "Distribution validation failed at source" in result["reason"]
