"""
Integration test for T029: Evaluate inconsistency detection on synthetic dataset.

This test verifies that the evaluation script runs successfully and produces
metrics meeting the required thresholds (FR-031):
- Precision >= 90%
- Recall >= 80%
- F1 >= 0.85

It also verifies that the synthetic dataset contains both binary and continuous outcomes.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_SCRIPT = PROJECT_ROOT / 'code' / 'src' / 'audit' / 'evaluation.py'
SYNTHETIC_CSV = PROJECT_ROOT / 'data' / 'synthetic' / 'synthetic_validation.csv'
GROUND_TRUTH_JSON = PROJECT_ROOT / 'data' / 'synthetic' / 'synthetic_ground_truth.json'
OUTPUT_JSON = PROJECT_ROOT / 'output' / 'evaluation_results.json'

@pytest.fixture(scope="module")
def evaluation_results():
    """Run the evaluation script and return results."""
    # Ensure synthetic data exists
    if not SYNTHETIC_CSV.exists():
        pytest.skip("Synthetic dataset not found. Run T026 first.")
    
    if not GROUND_TRUTH_JSON.exists():
        pytest.skip("Ground truth file not found. Run T026 first.")
    
    # Run evaluation script
    result = subprocess.run(
        [sys.executable, str(EVALUATION_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(f"Evaluation script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    
    # Load results
    if not OUTPUT_JSON.exists():
        pytest.fail("Evaluation results file not created.")
    
    with open(OUTPUT_JSON, 'r') as f:
        return json.load(f)

@pytest.mark.integration
def test_evaluation_script_runs(evaluation_results):
    """Test that the evaluation script completes successfully."""
    assert 'precision' in evaluation_results
    assert 'recall' in evaluation_results
    assert 'f1' in evaluation_results
    assert 'thresholds_met' in evaluation_results

@pytest.mark.integration
def test_precision_threshold(evaluation_results):
    """Test that precision >= 90%."""
    precision = evaluation_results['precision']
    assert precision >= 0.90, f"Precision {precision:.4f} is below required 0.90"

@pytest.mark.integration
def test_recall_threshold(evaluation_results):
    """Test that recall >= 80%."""
    recall = evaluation_results['recall']
    assert recall >= 0.80, f"Recall {recall:.4f} is below required 0.80"

@pytest.mark.integration
def test_f1_threshold(evaluation_results):
    """Test that F1 >= 0.85."""
    f1 = evaluation_results['f1']
    assert f1 >= 0.85, f"F1 {f1:.4f} is below required 0.85"

@pytest.mark.integration
def test_thresholds_met_flag(evaluation_results):
    """Test that all thresholds are met."""
    assert evaluation_results['thresholds_met'] is True, "Not all evaluation thresholds were met"

@pytest.mark.integration
def test_record_counts(evaluation_results):
    """Test that evaluation was performed on sufficient records."""
    total = evaluation_results.get('total_records', 0)
    assert total >= 10000, f"Expected at least 10000 records, got {total}"

@pytest.mark.integration
def test_confusion_matrix_validity(evaluation_results):
    """Test that confusion matrix values are non-negative and consistent."""
    tp = evaluation_results['true_positives']
    fp = evaluation_results['false_positives']
    tn = evaluation_results['true_negatives']
    fn = evaluation_results['false_negatives']
    
    assert tp >= 0
    assert fp >= 0
    assert tn >= 0
    assert fn >= 0
    
    # Sum should equal total records
    total = tp + fp + tn + fn
    assert total == evaluation_results['total_records']

@pytest.mark.integration
def test_synthetic_dataset_outcome_types():
    """Verify that synthetic dataset contains both binary and continuous outcomes."""
    if not SYNTHETIC_CSV.exists():
        pytest.skip("Synthetic CSV not found.")
    
    import csv
    
    binary_count = 0
    continuous_count = 0
    
    with open(SYNTHETIC_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            outcome_type = row.get('outcome_type', '').lower()
            if outcome_type == 'binary':
                binary_count += 1
            elif outcome_type == 'continuous':
                continuous_count += 1
    
    assert binary_count > 0, "No binary outcomes found in synthetic dataset"
    assert continuous_count > 0, "No continuous outcomes found in synthetic dataset"
    
    # Log counts for verification
    total = binary_count + continuous_count
    assert total >= 10000, f"Total records {total} is below required 10000"
