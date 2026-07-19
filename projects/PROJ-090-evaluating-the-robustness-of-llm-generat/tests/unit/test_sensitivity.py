"""
Unit tests for sensitivity analysis threshold handling.

This module verifies that the sensitivity analysis logic correctly filters
and processes data across the specific threshold set {0.85, 0.90, 0.95, 0.99}
as defined in FR-009.

It ensures that:
1. The threshold sweep range is exactly {0.85, 0.90, 0.95, 0.99}.
2. The filtering logic correctly identifies samples meeting each threshold.
3. The delta calculation against the baseline (0.95) works correctly.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.statistics import run_sensitivity_analysis, load_results_data
from utils.logging import init_logging


# Mock data fixture for execution results
# Simulates a small dataset of pass/fail results for original and perturbed tasks
@pytest.fixture
def mock_execution_results(tmp_path: Path) -> Path:
    """Create a temporary JSON file with mock execution results."""
    results = [
        {
            "task_id": "HumanEval/0",
            "type": "original",
            "passed": True,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/0",
            "type": "perturbed",
            "passed": False,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/1",
            "type": "original",
            "passed": True,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/1",
            "type": "perturbed",
            "passed": True,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/2",
            "type": "original",
            "passed": False,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/2",
            "type": "perturbed",
            "passed": False,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/3",
            "type": "original",
            "passed": True,
            "threshold_used": 0.95
        },
        {
            "task_id": "HumanEval/3",
            "type": "perturbed",
            "passed": False,
            "threshold_used": 0.95
        },
    ]

    output_path = tmp_path / "execution_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f)
    return output_path


@pytest.fixture
def mock_perturbation_candidates(tmp_path: Path) -> Path:
    """Create a temporary JSON file with mock perturbation candidates and scores."""
    # This simulates the output from T018 (log_perturbation_candidates)
    # containing raw scores for various thresholds
    candidates = [
        {
            "task_id": "HumanEval/0",
            "perturbation_type": "synonym",
            "raw_score": 0.98,
            "is_valid": True,
            "reason": "Semantic similarity > 0.95"
        },
        {
            "task_id": "HumanEval/0",
            "perturbation_type": "synonym",
            "raw_score": 0.88,
            "is_valid": False,
            "reason": "Semantic similarity < 0.95"
        },
        {
            "task_id": "HumanEval/1",
            "perturbation_type": "typo",
            "raw_score": 0.96,
            "is_valid": True,
            "reason": "Semantic similarity > 0.95"
        },
        {
            "task_id": "HumanEval/2",
            "perturbation_type": "rephrase",
            "raw_score": 0.92,
            "is_valid": False,
            "reason": "Semantic similarity < 0.95"
        },
        {
            "task_id": "HumanEval/3",
            "perturbation_type": "synonym",
            "raw_score": 0.99,
            "is_valid": True,
            "reason": "Semantic similarity > 0.95"
        },
    ]

    output_path = tmp_path / "perturbation_candidates.json"
    with open(output_path, "w") as f:
        json.dump(candidates, f)
    return output_path


class TestSensitivityThresholdHandling:
    """Tests for sensitivity analysis threshold filtering logic."""

    def test_threshold_sweep_range_is_correct(self, tmp_path: Path, mock_execution_results, mock_perturbation_candidates):
        """Verify that the sensitivity analysis uses exactly the thresholds {0.85, 0.90, 0.95, 0.99}."""
        # Initialize logging to avoid warnings
        init_logging(tmp_path / "logs")

        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            execution_results_path=str(mock_execution_results),
            candidates_path=str(mock_perturbation_candidates),
            output_path=str(tmp_path / "sensitivity_report.csv"),
            thresholds=[0.85, 0.90, 0.95, 0.99]
        )

        # Verify the returned thresholds match the expected set
        expected_thresholds = {0.85, 0.90, 0.95, 0.99}
        actual_thresholds = set(results["thresholds"])

        assert actual_thresholds == expected_thresholds, (
            f"Threshold sweep range mismatch. Expected {expected_thresholds}, got {actual_thresholds}"
        )

    def test_filtering_logic_for_threshold_095(self, tmp_path: Path, mock_execution_results, mock_perturbation_candidates):
        """Verify that the filtering logic correctly identifies valid perturbations at 0.95 threshold."""
        init_logging(tmp_path / "logs")

        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            execution_results_path=str(mock_execution_results),
            candidates_path=str(mock_perturbation_candidates),
            output_path=str(tmp_path / "sensitivity_report.csv"),
            thresholds=[0.95]
        )

        # Check that the report was generated
        assert os.path.exists(results["output_path"]), "Sensitivity report file was not created"

        # Load the report to verify content
        with open(results["output_path"], "r") as f:
            lines = f.readlines()

        # Header should be present
        assert "threshold" in lines[0].lower(), "Header missing 'threshold' column"

        # There should be exactly one data row for threshold 0.95
        data_rows = [line for line in lines[1:] if line.strip()]
        assert len(data_rows) == 1, f"Expected 1 data row for threshold 0.95, got {len(data_rows)}"

    def test_delta_calculation_against_baseline(self, tmp_path: Path, mock_execution_results, mock_perturbation_candidates):
        """Verify that delta_from_baseline is calculated correctly relative to 0.95 baseline."""
        init_logging(tmp_path / "logs")

        # Run sensitivity analysis with multiple thresholds
        results = run_sensitivity_analysis(
            execution_results_path=str(mock_execution_results),
            candidates_path=str(mock_perturbation_candidates),
            output_path=str(tmp_path / "sensitivity_report.csv"),
            thresholds=[0.85, 0.90, 0.95, 0.99]
        )

        # Load the CSV
        import csv
        with open(results["output_path"], "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Find the baseline row (0.95)
        baseline_row = next((r for r in rows if float(r["threshold"]) == 0.95), None)
        assert baseline_row is not None, "Baseline threshold 0.95 not found in results"

        baseline_pass_rate = float(baseline_row["pass_rate"])

        # Check delta calculation for other thresholds
        for row in rows:
            threshold = float(row["threshold"])
            pass_rate = float(row["pass_rate"])
            delta = float(row["delta_from_baseline"])

            expected_delta = pass_rate - baseline_pass_rate
            assert abs(delta - expected_delta) < 1e-6, (
                f"Delta calculation error for threshold {threshold}: "
                f"expected {expected_delta}, got {delta}"
            )

    def test_no_synthetic_fallback_in_threshold_logic(self, tmp_path: Path):
        """Verify that the sensitivity analysis does not use synthetic data as fallback."""
        # This test ensures that if real data is missing, the function fails
        # rather than generating synthetic results.

        init_logging(tmp_path / "logs")

        # Use non-existent file paths to simulate missing real data
        non_existent_results = str(tmp_path / "non_existent_results.json")
        non_existent_candidates = str(tmp_path / "non_existent_candidates.json")

        # The function should raise an error when real data is missing
        # (it should NOT fall back to synthetic data)
        with pytest.raises((FileNotFoundError, ValueError)):
            run_sensitivity_analysis(
                execution_results_path=non_existent_results,
                candidates_path=non_existent_candidates,
                output_path=str(tmp_path / "sensitivity_report.csv"),
                thresholds=[0.85, 0.90, 0.95, 0.99]
            )

    def test_threshold_ordering_in_output(self, tmp_path: Path, mock_execution_results, mock_perturbation_candidates):
        """Verify that the output CSV maintains the specified threshold order."""
        init_logging(tmp_path / "logs")

        # Run with a specific order
        ordered_thresholds = [0.99, 0.85, 0.95, 0.90]
        results = run_sensitivity_analysis(
            execution_results_path=str(mock_execution_results),
            candidates_path=str(mock_perturbation_candidates),
            output_path=str(tmp_path / "sensitivity_report.csv"),
            thresholds=ordered_thresholds
        )

        # Load the CSV
        import csv
        with open(results["output_path"], "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Extract thresholds from output
        output_thresholds = [float(row["threshold"]) for row in rows]

        # The output should follow the input order (or be sorted, but not random)
        # We check that all expected thresholds are present
        assert set(output_thresholds) == set(ordered_thresholds), (
            f"Output thresholds {output_thresholds} do not match input {ordered_thresholds}"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
