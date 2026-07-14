"""
Unit tests for T040: Create Comparison Report.
"""
import pytest
import os
import json
import tempfile
from datetime import datetime

# Import functions to test
from t040_create_comparison_report import (
    load_baseline_metrics,
    load_cleaned_metrics,
    calculate_absolute_diff,
    calculate_relative_diff,
    aggregate_metrics_for_comparison,
    create_comparison_report
)

def test_calculate_absolute_diff():
    assert calculate_absolute_diff(0.05, 0.04) == 0.01
    assert calculate_absolute_diff(0.05, 0.05) == 0.0
    assert calculate_absolute_diff(0.05, 0.06) == 0.01

def test_calculate_relative_diff():
    assert abs(calculate_relative_diff(0.05, 0.04) - (-0.2)) < 0.001
    assert calculate_relative_diff(0.05, 0.05) == 0.0
    assert calculate_relative_diff(0.0, 0.05) == 0.0  # Edge case

def test_aggregate_metrics_for_comparison():
    baseline = {
        "datasets": [
            {
                "dataset_name": "test_ds",
                "analysis": {
                    "t_tests": {
                        "test_1": {"p_value": 0.05, "ci": [0.1, 0.9], "effect_size": 0.5}
                    }
                }
            }
        ]
    }
    cleaned = {
        "datasets": [
            {
                "dataset_name": "test_ds",
                "analysis": {
                    "t_tests": {
                        "test_1": {"p_value": 0.03, "ci": [0.2, 0.8], "effect_size": 0.6}
                    }
                }
            }
        ]
    }

    result = aggregate_metrics_for_comparison(baseline, cleaned)
    
    assert result["summary"]["total_datasets"] == 1
    assert result["datasets"][0]["dataset_id"] == "test_ds"
    assert result["datasets"][0]["differences"]["p_value_shift"] == 0.02

def test_create_comparison_report_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = os.path.join(tmpdir, "baseline.json")
        cleaned_path = os.path.join(tmpdir, "cleaned.json")
        output_path = os.path.join(tmpdir, "report.json")

        baseline_data = {"datasets": [{"dataset_name": "ds1", "analysis": {"t_tests": {}}}]}
        cleaned_data = {"datasets": [{"dataset_name": "ds1", "analysis": {"t_tests": {}}}]}

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(cleaned_path, 'w') as f:
            json.dump(cleaned_data, f)

        # Mock the load functions to use our temp files
        import t040_create_comparison_report as t040
        
        # We can't easily mock the internal load functions without refactoring,
        # so we test the logic directly by passing dicts to create_comparison_report
        report = create_comparison_report(
            baseline_data, 
            cleaned_data, 
            output_path=output_path
        )

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert "id" in saved_report
        assert "baseline_metrics" in saved_report
        assert "cleaned_metrics" in saved_report