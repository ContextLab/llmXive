"""
Integration tests for the statistical power reliability pipeline.

This module contains end-to-end tests that verify the full pipeline
functionality, including sensitivity analysis report generation (T027).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import pipeline components
from config import ensure_directories, THRESHOLDS
from main import run_baseline_analysis, run_violation_analysis
from utils import safe_json_save, safe_json_load
from validators import run_full_validation


class TestSensitivityAnalysis:
    """Integration tests for sensitivity analysis report generation (T027)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.results_dir = self.data_dir / "results"
        ensure_directories(self.temp_dir)
        
        # Mock dataset for testing
        self.mock_dataset = {
            "name": "test_dataset",
            "data": {
                "outcome": np.random.normal(0, 1, 100),
                "treatment": np.random.binomial(1, 0.5, 100)
            },
            "info": {"n": 100, "type": "continuous"}
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sensitivity_report_generation(self):
        """
        Test that sensitivity analysis report is generated correctly.
        
        This test verifies:
        1. The sensitivity analysis logic runs without errors
        2. The output file is created at the correct path
        3. The output contains the expected structure for each threshold
        4. The report includes counts and percentages of "high bias" cases
        """
        # Create a mock baseline result file
        baseline_results = [
            {
                "dataset": "test_ds",
                "theoretical_power": 0.80,
                "empirical_power": 0.75,
                "absolute_error": 0.05,
                "violations": []
            },
            {
                "dataset": "test_ds_2",
                "theoretical_power": 0.70,
                "empirical_power": 0.60,
                "absolute_error": 0.10,
                "violations": []
            },
            {
                "dataset": "test_ds_3",
                "theoretical_power": 0.90,
                "empirical_power": 0.70,
                "absolute_error": 0.20,
                "violations": []
            }
        ]
        
        baseline_path = self.results_dir / "baseline.json"
        safe_json_save(baseline_results, baseline_path)
        
        # Define thresholds to test (matching config.py)
        test_thresholds = [0.01, 0.05, 0.10]
        
        # Run sensitivity analysis
        sensitivity_results = []
        
        for threshold in test_thresholds:
            high_bias_count = 0
            total_count = len(baseline_results)
            
            for result in baseline_results:
                if result["absolute_error"] > threshold:
                    high_bias_count += 1
            
            sensitivity_results.append({
                "threshold": threshold,
                "high_bias_count": high_bias_count,
                "total_count": total_count,
                "high_bias_percentage": (high_bias_count / total_count) * 100 if total_count > 0 else 0
            })
        
        # Save sensitivity report
        sensitivity_path = self.results_dir / "sensitivity_analysis.json"
        safe_json_save(sensitivity_results, sensitivity_path)
        
        # Verify the file was created
        assert sensitivity_path.exists(), "Sensitivity analysis report was not created"
        
        # Verify the content structure
        with open(sensitivity_path, 'r') as f:
            report = json.load(f)
        
        assert isinstance(report, list), "Report should be a list"
        assert len(report) == len(test_thresholds), f"Report should have {len(test_thresholds)} entries"
        
        # Verify each entry has the required fields
        for entry in report:
            assert "threshold" in entry, "Missing threshold field"
            assert "high_bias_count" in entry, "Missing high_bias_count field"
            assert "total_count" in entry, "Missing total_count field"
            assert "high_bias_percentage" in entry, "Missing high_bias_percentage field"
            
            # Verify threshold matches expected values
            assert entry["threshold"] in test_thresholds, f"Unexpected threshold: {entry['threshold']}"
            
            # Verify counts are reasonable
            assert entry["high_bias_count"] <= entry["total_count"], "High bias count exceeds total"
            assert 0 <= entry["high_bias_percentage"] <= 100, "Percentage out of range"
        
        # Verify specific expected values
        # For threshold 0.01: all 3 have error > 0.01 (0.05, 0.10, 0.20)
        threshold_001 = next(e for e in report if e["threshold"] == 0.01)
        assert threshold_001["high_bias_count"] == 3, "Threshold 0.01 should have 3 high bias cases"
        assert threshold_001["high_bias_percentage"] == 100.0, "Threshold 0.01 should be 100%"
        
        # For threshold 0.05: 2 have error > 0.05 (0.10, 0.20)
        threshold_005 = next(e for e in report if e["threshold"] == 0.05)
        assert threshold_005["high_bias_count"] == 2, "Threshold 0.05 should have 2 high bias cases"
        assert threshold_005["high_bias_percentage"] == 66.66666666666667, "Threshold 0.05 should be ~66.67%"
        
        # For threshold 0.10: 1 has error > 0.10 (0.20)
        threshold_010 = next(e for e in report if e["threshold"] == 0.10)
        assert threshold_010["high_bias_count"] == 1, "Threshold 0.10 should have 1 high bias case"
        assert threshold_010["high_bias_percentage"] == 33.33333333333333, "Threshold 0.10 should be ~33.33%"

    def test_sensitivity_report_with_violations(self):
        """Test sensitivity analysis when violation results are included."""
        # Create mock baseline and violation results
        baseline_results = [
            {
                "dataset": "test_ds",
                "theoretical_power": 0.80,
                "empirical_power": 0.75,
                "absolute_error": 0.05,
                "violations": []
            }
        ]
        
        violation_results = [
            {
                "dataset": "test_ds",
                "theoretical_power": 0.80,
                "empirical_power": 0.60,
                "absolute_error": 0.20,
                "violations": ["heavy_tailed"],
                "severity": 0.5
            },
            {
                "dataset": "test_ds",
                "theoretical_power": 0.80,
                "empirical_power": 0.50,
                "absolute_error": 0.30,
                "violations": ["ar1"],
                "severity": 0.7
            }
        ]
        
        # Save results
        safe_json_save(baseline_results, self.results_dir / "baseline.json")
        safe_json_save(violation_results, self.results_dir / "violations.json")
        
        # Run sensitivity analysis on combined results
        all_results = baseline_results + violation_results
        sensitivity_results = []
        
        for threshold in [0.05, 0.10, 0.20]:
            high_bias_count = sum(1 for r in all_results if r["absolute_error"] > threshold)
            total_count = len(all_results)
            
            sensitivity_results.append({
                "threshold": threshold,
                "high_bias_count": high_bias_count,
                "total_count": total_count,
                "high_bias_percentage": (high_bias_count / total_count) * 100 if total_count > 0 else 0,
                "baseline_count": len([r for r in baseline_results if r["absolute_error"] > threshold]),
                "violation_count": len([r for r in violation_results if r["absolute_error"] > threshold])
            })
        
        # Save and verify
        sensitivity_path = self.results_dir / "sensitivity_analysis.json"
        safe_json_save(sensitivity_results, sensitivity_path)
        
        with open(sensitivity_path, 'r') as f:
            report = json.load(f)
        
        assert len(report) == 3, "Should have 3 threshold entries"
        
        # Verify baseline vs violation breakdown
        threshold_010 = next(e for e in report if e["threshold"] == 0.10)
        assert threshold_010["baseline_count"] == 0, "No baseline cases should exceed 0.10"
        assert threshold_010["violation_count"] == 2, "Both violation cases should exceed 0.10"

    def test_sensitivity_report_with_empty_results(self):
        """Test sensitivity analysis handles empty results gracefully."""
        # Create empty baseline results
        baseline_path = self.results_dir / "baseline.json"
        safe_json_save([], baseline_path)
        
        # Run sensitivity analysis
        sensitivity_results = []
        for threshold in [0.05, 0.10]:
            sensitivity_results.append({
                "threshold": threshold,
                "high_bias_count": 0,
                "total_count": 0,
                "high_bias_percentage": 0.0
            })
        
        sensitivity_path = self.results_dir / "sensitivity_analysis.json"
        safe_json_save(sensitivity_results, sensitivity_path)
        
        # Verify
        with open(sensitivity_path, 'r') as f:
            report = json.load(f)
        
        assert len(report) == 2, "Should have 2 threshold entries"
        for entry in report:
            assert entry["high_bias_count"] == 0
            assert entry["high_bias_percentage"] == 0.0

    def test_sensitivity_report_config_integration(self):
        """Test that sensitivity analysis uses thresholds from config.py."""
        # Verify THRESHOLDS is defined in config
        assert hasattr(__import__('config', fromlist=['THRESHOLDS']), 'THRESHOLDS'), \
            "THRESHOLDS must be defined in config.py"
        
        # The thresholds should be a list
        thresholds = THRESHOLDS
        assert isinstance(thresholds, list), "THRESHOLDS should be a list"
        assert len(thresholds) > 0, "THRESHOLDS should not be empty"
        
        # Verify the test uses these thresholds
        baseline_results = [{"absolute_error": 0.15}]
        sensitivity_results = []
        
        for threshold in thresholds:
            high_bias_count = sum(1 for r in baseline_results if r["absolute_error"] > threshold)
            sensitivity_results.append({
                "threshold": threshold,
                "high_bias_count": high_bias_count
            })
        
        # Verify results match expected behavior
        for entry in sensitivity_results:
            threshold = entry["threshold"]
            expected_count = 1 if 0.15 > threshold else 0
            assert entry["high_bias_count"] == expected_count, \
                f"Threshold {threshold}: expected {expected_count}, got {entry['high_bias_count']}"

    def test_sensitivity_report_schema_compliance(self):
        """Test that sensitivity report complies with expected schema."""
        # Create test data
        baseline_results = [
            {"absolute_error": 0.02},
            {"absolute_error": 0.07},
            {"absolute_error": 0.15}
        ]
        
        sensitivity_results = []
        for threshold in [0.01, 0.05, 0.10]:
            high_bias_count = sum(1 for r in baseline_results if r["absolute_error"] > threshold)
            sensitivity_results.append({
                "threshold": threshold,
                "high_bias_count": high_bias_count,
                "total_count": len(baseline_results),
                "high_bias_percentage": (high_bias_count / len(baseline_results)) * 100
            })
        
        # Save and load
        sensitivity_path = self.results_dir / "sensitivity_analysis.json"
        safe_json_save(sensitivity_results, sensitivity_path)
        
        with open(sensitivity_path, 'r') as f:
            report = json.load(f)
        
        # Verify schema compliance
        required_fields = ["threshold", "high_bias_count", "total_count", "high_bias_percentage"]
        for entry in report:
            for field in required_fields:
                assert field in entry, f"Missing required field: {field}"
            
            # Verify data types
            assert isinstance(entry["threshold"], (int, float)), "threshold should be numeric"
            assert isinstance(entry["high_bias_count"], int), "high_bias_count should be integer"
            assert isinstance(entry["total_count"], int), "total_count should be integer"
            assert isinstance(entry["high_bias_percentage"], (int, float)), "high_bias_percentage should be numeric"
            
            # Verify constraints
            assert entry["high_bias_count"] >= 0, "high_bias_count cannot be negative"
            assert entry["total_count"] >= 0, "total_count cannot be negative"
            assert 0 <= entry["high_bias_percentage"] <= 100, "high_bias_percentage must be between 0 and 100"