"""
Integration tests for threshold optimization logic.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.threshold_opt import find_optimal_threshold, analyze_thresholds


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entropy_data(temp_test_dir):
    """Generate a sample dataset for threshold testing."""
    # Create a synthetic but realistic dataset
    # We will create a file that simulates the merged output from T022
    # Structure: List of records with sequence_id, validity, and entropy_values
    
    data = []
    
    # Case 1: Clear separation
    # Valid tokens (low entropy)
    for i in range(50):
        data.append({
            "sequence_id": f"seq_valid_{i}",
            "validity": 1,
            "entropy_values": [0.1 + (i * 0.01)] # Low entropy
        })
    
    # Invalid tokens (high entropy)
    for i in range(50):
        data.append({
            "sequence_id": f"seq_invalid_{i}",
            "validity": 0,
            "entropy_values": [1.5 + (i * 0.01)] # High entropy
        })

    # Write to temp file
    input_path = temp_test_dir / "sample_data.jsonl"
    with open(input_path, 'w') as f:
        for record in data:
            f.write(json.dumps(record) + "\n")
    
    return {
        "input_path": str(input_path),
        "output_path": str(temp_test_dir / "threshold_results.json"),
        "expected_threshold_range": (0.8, 1.2) # Should be between 0.1 and 1.5
    }


def test_threshold_optimization_imports():
    """Verify that the threshold_opt module can be imported."""
    try:
        from src.analysis.threshold_opt import find_optimal_threshold, analyze_thresholds, calculate_metrics_at_threshold
        assert callable(find_optimal_threshold)
        assert callable(analyze_thresholds)
        assert callable(calculate_metrics_at_threshold)
    except ImportError as e:
        pytest.fail(f"Failed to import threshold_opt module: {e}")


def test_find_optimal_threshold_logic():
    """Test the core logic of finding optimal threshold with known data."""
    # Construct a simple scenario:
    # Valid: [0.1, 0.2, 0.3]
    # Invalid: [0.8, 0.9, 1.0]
    # Optimal threshold should be around 0.55 (midpoint)
    
    y_true = np.array([1, 1, 1, 0, 0, 0])
    entropy_values = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])
    
    # We assume lower entropy = valid (higher_entropy_is_valid=False)
    threshold, metrics = find_optimal_threshold(
        y_true, entropy_values, 
        cost_fp=1.0, cost_fn=1.0,
        higher_entropy_is_valid=False
    )
    
    # The threshold should be between the highest valid (0.3) and lowest invalid (0.8)
    assert 0.3 < threshold < 0.8, f"Threshold {threshold} not in expected range (0.3, 0.8)"
    
    # At this threshold, we should have perfect classification
    assert metrics['tp'] == 3
    assert metrics['tn'] == 3
    assert metrics['fp'] == 0
    assert metrics['fn'] == 0
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0


def test_threshold_optimization_significance(sample_entropy_data):
    """Test the full integration of threshold optimization on a file."""
    input_path = sample_entropy_data["input_path"]
    output_path = sample_entropy_data["output_path"]
    
    # Run the analysis
    result = analyze_thresholds(
        data_path=input_path,
        output_path=output_path,
        cost_fp=1.0,
        cost_fn=1.0,
        higher_entropy_is_valid=False # Lower entropy is valid
    )
    
    # Verify output file exists
    assert os.path.exists(output_path), "Output file was not created"
    
    # Verify result structure
    assert "optimal_threshold" in result
    assert "metrics_at_optimal" in result
    assert "dataset_size" in result
    
    # Verify the threshold is in the expected range
    assert sample_entropy_data["expected_threshold_range"][0] < result["optimal_threshold"] < sample_entropy_data["expected_threshold_range"][1]
    
    # Verify metrics are perfect (since data is separable)
    assert result["metrics_at_optimal"]["fp"] == 0
    assert result["metrics_at_optimal"]["fn"] == 0
    assert result["metrics_at_optimal"]["precision"] == 1.0
    assert result["metrics_at_optimal"]["recall"] == 1.0


def test_threshold_optimization_imbalanced_costs(sample_entropy_data):
    """Test that changing costs shifts the threshold."""
    input_path = sample_entropy_data["input_path"]
    output_path = str(Path(input_path).parent / "threshold_results_imbalanced.json")
    
    # High cost for False Negatives (missing valid tokens) -> Lower threshold (more inclusive)
    result_fn = analyze_thresholds(
        data_path=input_path,
        output_path=output_path,
        cost_fp=1.0,
        cost_fn=10.0, # Penalize FN heavily
        higher_entropy_is_valid=False
    )
    
    # High cost for False Positives (accepting invalid tokens) -> Higher threshold (more exclusive)
    result_fp = analyze_thresholds(
        data_path=input_path,
        output_path=str(Path(input_path).parent / "threshold_results_fp.json"),
        cost_fp=10.0,
        cost_fn=1.0, # Penalize FP heavily
        higher_entropy_is_valid=False
    )
    
    # The threshold for high FN cost should be lower (more inclusive) than for high FP cost
    # Wait: if we want to avoid FN (missing valid), we must classify more as valid.
    # If lower entropy = valid, and we want to avoid FN, we must lower the threshold 
    # (so more items with slightly higher entropy are still classified as valid).
    # So threshold_fn should be lower than threshold_fp.
    
    # However, our logic: y_pred = (entropy < threshold).
    # To catch more valid (low entropy), we need a higher threshold? 
    # No, if threshold is high, say 1.0, then 0.9 is valid. If threshold is 0.2, 0.9 is invalid.
    # So to avoid FN (classifying valid as invalid), we need a HIGHER threshold.
    
    # Let's re-evaluate:
    # Valid: 0.1, Invalid: 0.9.
    # Threshold 0.5: 0.1 -> Valid (TP), 0.9 -> Invalid (TN).
    # Threshold 0.2: 0.1 -> Valid (TP), 0.9 -> Invalid (TN).
    # Threshold 0.0: 0.1 -> Invalid (FN).
    
    # If cost_fn is high, we want to avoid FN. So we want to classify as many as possible as Valid.
    # Since Valid has low entropy, we want to raise the threshold so that items with slightly higher entropy are still Valid.
    # So threshold_fn (high cost_fn) should be > threshold_fp (high cost_fp).
    
    assert result_fn["optimal_threshold"] >= result_fp["optimal_threshold"], \
        f"High FN cost should result in higher threshold. Got {result_fn['optimal_threshold']} vs {result_fp['optimal_threshold']}"