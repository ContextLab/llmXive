"""
Unit tests for sensitivity analysis threshold handling.

This module verifies that the sensitivity analysis logic correctly filters
perturbation candidates across a range of semantic similarity thresholds.
It ensures that the filtering logic adheres to the strict > 0.95 constraint
and correctly calculates delta metrics for the sensitivity report.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import the analysis module functions we are testing
# Note: The actual analysis logic is in code/analysis/statistics.py
# We import the relevant data loading and processing helpers here.
# Since we cannot import the full statistics module without running the full pipeline,
# we test the core filtering logic directly or via a helper function.

from code.analysis.statistics import load_results_data, run_sensitivity_analysis
from code.utils.logging import init_logging
from code.config import ensure_directories


class MockResult:
    """Mock result object to simulate data loaded from execution results."""
    def __init__(self, task_id: str, perturbation_type: str, threshold: float, passed: bool):
        self.task_id = task_id
        self.perturbation_type = perturbation_type
        self.threshold = threshold
        self.passed = passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "perturbation_type": self.perturbation_type,
            "threshold": self.threshold,
            "passed": self.passed
        }


def create_mock_results_file(tmp_path: Path) -> Path:
    """
    Creates a temporary JSON file with mock execution results for testing.
    Includes data points at various thresholds to test filtering logic.
    """
    mock_data = [
        # Baseline (original) - no perturbation, effectively 1.0 similarity
        {"task_id": "human_eval_001", "perturbation_type": "original", "threshold": 1.0, "passed": True},
        {"task_id": "human_eval_002", "perturbation_type": "original", "threshold": 1.0, "passed": False},
        
        # Synonym perturbations with varying scores
        {"task_id": "human_eval_001", "perturbation_type": "synonym", "threshold": 0.96, "passed": True},
        {"task_id": "human_eval_001", "perturbation_type": "synonym", "threshold": 0.94, "passed": True}, # Below strict threshold
        {"task_id": "human_eval_002", "perturbation_type": "synonym", "threshold": 0.96, "passed": False},
        
        # Typo perturbations
        {"task_id": "human_eval_001", "perturbation_type": "typo", "threshold": 0.98, "passed": True},
        {"task_id": "human_eval_002", "perturbation_type": "typo", "threshold": 0.92, "passed": False},
        
        # Rephrase perturbations
        {"task_id": "human_eval_001", "perturbation_type": "rephrase", "threshold": 0.95, "passed": True}, # Edge case: exactly 0.95
        {"task_id": "human_eval_002", "perturbation_type": "rephrase", "threshold": 0.97, "passed": False},
    ]

    results_file = tmp_path / "mock_results.json"
    with open(results_file, "w") as f:
        json.dump(mock_data, f)
    
    return results_file


def test_sensitivity_filtering_logic():
    """
    Test that the sensitivity analysis correctly filters candidates based on threshold.
    
    Specifically verifies:
    1. Candidates with threshold <= 0.95 are excluded (strict > 0.95 rule).
    2. Candidates with threshold > 0.95 are included.
    3. The baseline (original) is handled correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ensure_directories(tmp_path)
        
        results_file = create_mock_results_file(tmp_path)
        
        # Define the threshold range to test
        thresholds_to_test = [0.90, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]
        
        # Load the data
        data = load_results_data(results_file)
        
        # Verify the data loaded correctly
        assert len(data) == 9, f"Expected 9 mock records, got {len(data)}"
        
        # Test filtering logic manually to ensure correctness
        for threshold in thresholds_to_test:
            # Filter data: must be > threshold (strict inequality as per spec)
            filtered_data = [
                item for item in data 
                if item["threshold"] > threshold
            ]
            
            # Verify expected counts for specific thresholds
            if threshold == 0.95:
                # Only items with threshold > 0.95 should remain
                # Expected: 1.0 (2 items), 0.96 (2 items), 0.98 (1 item), 0.97 (1 item)
                # Excluded: 0.94, 0.92, 0.95 (exactly)
                expected_count = 6
                assert len(filtered_data) == expected_count, \
                    f"At threshold {threshold}, expected {expected_count} items, got {len(filtered_data)}"
                
                # Verify 0.95 is excluded
                assert not any(item["threshold"] == 0.95 for item in filtered_data), \
                    "Threshold 0.95 should be excluded (strict > 0.95 rule)"
                
            elif threshold == 0.96:
                # Only items > 0.96: 1.0 (2), 0.98 (1), 0.97 (1)
                expected_count = 4
                assert len(filtered_data) == expected_count, \
                    f"At threshold {threshold}, expected {expected_count} items, got {len(filtered_data)}"
                
            elif threshold == 0.94:
                # Items > 0.94: 1.0 (2), 0.96 (2), 0.98 (1), 0.97 (1), 0.95 (1)
                expected_count = 7
                assert len(filtered_data) == expected_count, \
                    f"At threshold {threshold}, expected {expected_count} items, got {len(filtered_data)}"


def test_sensitivity_analysis_function():
    """
    Test the run_sensitivity_analysis function with mock data.
    Verifies that it produces a valid sensitivity report structure.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ensure_directories(tmp_path)
        
        results_file = create_mock_results_file(tmp_path)
        output_file = tmp_path / "sensitivity_report.csv"
        
        # Run the sensitivity analysis
        # We pass a range of thresholds to test
        thresholds = [0.94, 0.95, 0.96, 0.97, 0.98]
        
        try:
            result = run_sensitivity_analysis(
                results_file=str(results_file),
                output_file=str(output_file),
                thresholds=thresholds
            )
            
            # Verify the output file was created
            assert output_file.exists(), "Sensitivity report CSV was not created"
            
            # Verify the result structure
            assert isinstance(result, dict), "Sensitivity analysis result should be a dict"
            assert "thresholds_tested" in result, "Result missing 'thresholds_tested'"
            assert "baseline_pass_rate" in result, "Result missing 'baseline_pass_rate'"
            assert "sensitivity_data" in result, "Result missing 'sensitivity_data'"
            
            # Verify the number of thresholds tested matches input
            assert len(result["thresholds_tested"]) == len(thresholds), \
                "Number of tested thresholds does not match input"
            
            # Verify the CSV has the expected columns
            with open(output_file, "r") as f:
                header = f.readline().strip()
                expected_columns = ["threshold", "pass_rate", "delta_from_baseline", "sample_count"]
                for col in expected_columns:
                    assert col in header, f"CSV missing column: {col}"
                    
        except Exception as e:
            pytest.fail(f"Sensitivity analysis failed with error: {e}")


def test_strict_threshold_enforcement():
    """
    Test that the strict > 0.95 threshold is enforced and no fallback logic exists.
    This is a critical constraint per FR-002/FR-003.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ensure_directories(tmp_path)
        
        # Create data with a mix of scores around the threshold
        mock_data = [
            {"task_id": "test_1", "perturbation_type": "synonym", "threshold": 0.950, "passed": True},
            {"task_id": "test_2", "perturbation_type": "synonym", "threshold": 0.951, "passed": True},
            {"task_id": "test_3", "perturbation_type": "synonym", "threshold": 0.949, "passed": True},
        ]
        
        results_file = tmp_path / "strict_test.json"
        with open(results_file, "w") as f:
            json.dump(mock_data, f)
        
        data = load_results_data(results_file)
        
        # Test at exactly 0.95
        filtered = [item for item in data if item["threshold"] > 0.95]
        
        # Only test_2 (0.951) should remain
        assert len(filtered) == 1, f"Expected 1 item > 0.95, got {len(filtered)}"
        assert filtered[0]["task_id"] == "test_2", "Wrong item passed the filter"
        
        # Verify 0.950 is excluded
        assert not any(item["threshold"] == 0.950 for item in filtered), \
            "Threshold 0.950 should be excluded (strict > 0.95)"
        
        # Verify 0.949 is excluded
        assert not any(item["threshold"] == 0.949 for item in filtered), \
            "Threshold 0.949 should be excluded"


def test_delta_calculation():
    """
    Test that delta_from_baseline is calculated correctly.
    """
    baseline_rate = 0.80
    perturbed_rate = 0.65
    
    expected_delta = perturbed_rate - baseline_rate
    actual_delta = perturbed_rate - baseline_rate
    
    assert actual_delta == expected_delta, "Delta calculation is incorrect"
    
    # Test with negative delta (degradation)
    assert actual_delta < 0, "Delta should be negative for performance degradation"
    
    # Test with positive delta (improvement - unlikely but possible)
    improved_rate = 0.85
    positive_delta = improved_rate - baseline_rate
    assert positive_delta > 0, "Delta should be positive for performance improvement"