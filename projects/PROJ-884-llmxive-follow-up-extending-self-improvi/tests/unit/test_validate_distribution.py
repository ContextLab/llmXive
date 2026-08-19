"""
Unit tests for code/dataset/validate_distribution.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.dataset.validate_distribution import (
    load_json,
    load_schema,
    calculate_chi_square,
    validate_complexity_scaling,
    calculate_power_estimate,
    main
)

class TestLoadJson:
    def test_load_json_exists(self, tmp_path):
        test_data = {"key": "value"}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(test_data))
        
        result = load_json(file_path)
        assert result == test_data

    def test_load_json_not_found(self, tmp_path):
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_json(file_path)

class TestCalculateChiSquare:
    def test_perfect_fit(self):
        observed = {"sudoku": 50, "pathfinding": 50}
        expected = {"sudoku": 0.5, "pathfinding": 0.5}
        # Total 100. Expected 50 each. (50-50)^2 / 50 = 0
        result = calculate_chi_square(observed, expected)
        assert result == 0.0

    def test_mismatch_fit(self):
        observed = {"sudoku": 90, "pathfinding": 10}
        expected = {"sudoku": 0.5, "pathfinding": 0.5}
        # Total 100. Expected 50 each.
        # (90-50)^2/50 + (10-50)^2/50 = 1600/50 + 1600/50 = 32 + 32 = 64
        result = calculate_chi_square(observed, expected)
        assert result == 64.0

class TestValidateComplexityScaling:
    def test_valid_range(self):
        report = {
            "complexity_distribution": {
                "10": 10,
                "50": 10,
                "500": 10
            }
        }
        result = validate_complexity_scaling(report)
        assert result['is_valid'] is True
        assert "within bounds" in result['notes']

    def test_invalid_min(self):
        report = {
            "complexity_distribution": {
                "5": 10
            }
        }
        result = validate_complexity_scaling(report)
        assert result['is_valid'] is False

    def test_invalid_max(self):
        report = {
            "complexity_distribution": {
                "600": 10
            }
        }
        result = validate_complexity_scaling(report)
        assert result['is_valid'] is False

    def test_empty_distribution(self):
        report = {"complexity_distribution": {}}
        result = validate_complexity_scaling(report)
        assert result['is_valid'] is False

class TestCalculatePowerEstimate:
    def test_small_sample(self):
        assert calculate_power_estimate(0) == 0.0
        assert calculate_power_estimate(1) == 0.0

    def test_large_sample(self):
        # With large N, power should approach 1.0 for default effect size
        power = calculate_power_estimate(10000)
        assert power > 0.8

class TestMain:
    def test_main_success(self, tmp_path):
        # Setup mock inputs
        dist_report = {
            "total_count": 100,
            "type_distribution": {"sudoku": 50, "pathfinding": 50},
            "complexity_distribution": {"10": 20, "50": 20, "500": 60}
        }
        schema = {"type": "object"}
        
        report_file = tmp_path / "distribution_report.json"
        schema_file = tmp_path / "dataset.schema.yaml"
        output_file = tmp_path / "distribution_validation.json"
        
        report_file.write_text(json.dumps(dist_report))
        schema_file.write_text(json.dumps(schema))
        
        # Mock PROJECT_ROOT usage by temporarily changing the script's paths logic?
        # Since main() uses global constants, we need to patch them or run in a specific env.
        # For this test, we will test the logic by importing the function and mocking the paths.
        # However, the function main() is the entry point.
        # We will test by creating the files in the expected locations relative to a temp dir
        # and monkey-patching the constants in the module.
        
        import code.dataset.validate_distribution as mod
        
        original_report_path = mod.DISTRIBUTION_REPORT_PATH
        original_schema_path = mod.SCHEMA_PATH
        original_output_path = mod.OUTPUT_PATH
        
        mod.DISTRIBUTION_REPORT_PATH = report_file
        mod.SCHEMA_PATH = schema_file
        mod.OUTPUT_PATH = output_file
        
        try:
            exit_code = main()
            assert exit_code == 0
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                result = json.load(f)
            assert result['is_valid'] is True
            assert 'notes' in result
        finally:
            mod.DISTRIBUTION_REPORT_PATH = original_report_path
            mod.SCHEMA_PATH = original_schema_path
            mod.OUTPUT_PATH = original_output_path

    def test_main_missing_input(self, tmp_path):
        import code.dataset.validate_distribution as mod
        
        original_report_path = mod.DISTRIBUTION_REPORT_PATH
        mod.DISTRIBUTION_REPORT_PATH = tmp_path / "nonexistent.json"
        
        try:
            exit_code = main()
            assert exit_code == 1
        finally:
            mod.DISTRIBUTION_REPORT_PATH = original_report_path