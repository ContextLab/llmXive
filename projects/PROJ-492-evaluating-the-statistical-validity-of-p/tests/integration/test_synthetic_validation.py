"""
Integration test for T029: Synthetic validation evaluation.

This test runs the evaluation script and verifies that:
1. The script executes successfully
2. The output file is created
3. The metrics meet the required thresholds (or ERR-800 is raised appropriately)
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def synthetic_data_dir():
    """Ensure synthetic data exists."""
    return Path("data/synthetic")


@pytest.fixture
def output_dir():
    """Ensure output directory exists."""
    output = Path("output")
    output.mkdir(exist_ok=True)
    return output


def test_synthetic_validation_evaluation_runs(synthetic_data_dir, output_dir):
    """Test that the evaluation script runs and produces output."""
    # Check that input files exist (T026 should have created them)
    synthetic_csv = synthetic_data_dir / "synthetic_validation.csv"
    ground_truth_json = synthetic_data_dir / "synthetic_ground_truth.json"
    
    if not synthetic_csv.exists():
        pytest.skip(f"Synthetic validation dataset not found at {synthetic_csv}. "
                   "Run T026 first to generate synthetic data.")
    
    if not ground_truth_json.exists():
        pytest.skip(f"Ground truth file not found at {ground_truth_json}. "
                   "Run T026 first to generate synthetic data.")
    
    # Run the evaluation script
    result = subprocess.run(
        [sys.executable, "code/src/audit/evaluation.py"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    
    # The script should exit with 0 (success) or 1 (thresholds not met)
    # In either case, it should produce output
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}. Stderr: {result.stderr}"
    
    # Check that output file was created
    output_json = output_dir / "evaluation_results.json"
    assert output_json.exists(), f"Output file not created: {output_json}"
    
    # Load and verify output structure
    with open(output_json, 'r') as f:
        metrics = json.load(f)
    
    required_fields = ['precision', 'recall', 'f1', 'tp', 'fp', 'tn', 'fn']
    for field in required_fields:
        assert field in metrics, f"Missing required field in output: {field}"
    
    # Verify thresholds (if script returned 0)
    if result.returncode == 0:
        assert metrics['precision'] >= 0.90, f"Precision {metrics['precision']} < 0.90"
        assert metrics['recall'] >= 0.80, f"Recall {metrics['recall']} < 0.80"
        assert metrics['f1'] >= 0.85, f"F1 {metrics['f1']} < 0.85"
    
    # If script returned 1, verify that ERR-800 was logged
    if result.returncode == 1:
        assert "ERR-800" in result.stderr or "ERR-800" in result.stdout, \
            "ERR-800 should be logged when thresholds are not met"


def test_metrics_are_reasonable(synthetic_data_dir, output_dir):
    """Test that the computed metrics are within valid ranges."""
    output_json = output_dir / "evaluation_results.json"
    
    if not output_json.exists():
        pytest.skip("Output file not found. Run evaluation first.")
    
    with open(output_json, 'r') as f:
        metrics = json.load(f)
    
    # Precision, recall, F1 should be between 0 and 1
    assert 0 <= metrics['precision'] <= 1, "Precision out of range"
    assert 0 <= metrics['recall'] <= 1, "Recall out of range"
    assert 0 <= metrics['f1'] <= 1, "F1 out of range"
    
    # TP, FP, TN, FN should be non-negative integers
    for field in ['tp', 'fp', 'tn', 'fn']:
        assert isinstance(metrics[field], int), f"{field} should be an integer"
        assert metrics[field] >= 0, f"{field} should be non-negative"
    
    # Total evaluated should equal sum of TP, FP, TN, FN
    total = metrics['tp'] + metrics['fp'] + metrics['tn'] + metrics['fn']
    assert metrics['total_evaluated'] == total, \
        f"Total evaluated ({metrics['total_evaluated']}) != TP+FP+TN+FN ({total})"
