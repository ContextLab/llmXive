"""
Integration tests for threshold optimization module.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.threshold_opt import (
    calculate_metrics_at_threshold,
    find_optimal_threshold,
    analyze_thresholds
)


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entropy_data():
    """
    Create a sample dataset with known entropy values and validity labels.
    Structure: Low entropy => Valid, High entropy => Invalid.
    """
    # Construct a simple bimodal distribution
    entropies = [
        0.1, 0.2, 0.15, 0.12, 0.18,  # Valid (low entropy)
        0.9, 0.95, 0.88, 0.92, 0.85,  # Invalid (high entropy)
        0.11, 0.13, 0.91, 0.89         # Mixed
    ]
    validity = [
        True, True, True, True, True,
        False, False, False, False, False,
        True, True, False, False
    ]
    return {
        'entropies': entropies,
        'validity_labels': validity
    }


def test_threshold_optimization_imports():
    """Test that all required functions are importable."""
    assert callable(calculate_metrics_at_threshold)
    assert callable(find_optimal_threshold)
    assert callable(analyze_thresholds)


def test_find_optimal_threshold_logic(sample_entropy_data):
    """Test that the optimal threshold logic finds a threshold between the two modes."""
    entropies = sample_entropy_data['entropies']
    validity = sample_entropy_data['validity_labels']

    result = find_optimal_threshold(entropies, validity, num_candidates=50)

    assert result['optimal_threshold'] is not None
    assert 0.2 < result['optimal_threshold'] < 0.9  # Should be between the two modes
    assert result['metrics'] is not None
    assert 'weighted_cost' in result['metrics']
    assert 'precision' in result['metrics']
    assert 'recall' in result['metrics']


def test_threshold_optimization_significance(sample_entropy_data, temp_test_dir):
    """Test that analysis produces significant separation at optimal threshold."""
    entropies = sample_entropy_data['entropies']
    validity = sample_entropy_data['validity_labels']

    output_path = temp_test_dir / "threshold_results.json"

    result = analyze_thresholds(
        entropies,
        validity,
        output_path=str(output_path),
        fp_weight=1.0,
        fn_weight=1.0
    )

    # Verify file was written
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        saved_data = json.load(f)

    assert saved_data['optimal_threshold'] is not None
    assert saved_data['metrics']['f1'] > 0.5  # Should have reasonable F1


def test_threshold_optimization_imbalanced_costs(sample_entropy_data):
    """Test that changing weights shifts the optimal threshold."""
    entropies = sample_entropy_data['entropies']
    validity = sample_entropy_data['validity_labels']

    # High weight on FP (penalize false positives heavily)
    result_fp_heavy = find_optimal_threshold(
        entropies, validity, fp_weight=5.0, fn_weight=1.0
    )

    # High weight on FN (penalize false negatives heavily)
    result_fn_heavy = find_optimal_threshold(
        entropies, validity, fp_weight=1.0, fn_weight=5.0
    )

    # The thresholds should differ
    assert result_fp_heavy['optimal_threshold'] != result_fn_heavy['optimal_threshold']

    # FP-heavy should have a higher threshold (more conservative about predicting valid)
    # FN-heavy should have a lower threshold (more aggressive about predicting valid)
    # Note: Exact direction depends on data distribution, but they must differ
    assert abs(result_fp_heavy['optimal_threshold'] - result_fn_heavy['optimal_threshold']) > 0.01


def test_empty_input_handling():
    """Test that empty inputs are handled gracefully."""
    result = find_optimal_threshold([], [], num_candidates=10)
    assert result['optimal_threshold'] is None
    assert result['metrics'] is None
    assert result['all_metrics'] == []


def test_calculate_metrics_edge_cases():
    """Test edge cases in metric calculation."""
    # All valid
    entropies = [0.1, 0.2, 0.3]
    labels = [True, True, True]
    metrics = calculate_metrics_at_threshold(entropies, labels, 0.5)
    assert metrics['tp'] == 3
    assert metrics['fp'] == 0
    assert metrics['fn'] == 0
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0

    # All invalid
    labels = [False, False, False]
    metrics = calculate_metrics_at_threshold(entropies, labels, 0.5)
    assert metrics['tn'] == 3
    assert metrics['fp'] == 0
    assert metrics['fn'] == 0
    assert metrics['precision'] == 0.0  # No positive predictions
    assert metrics['recall'] == 0.0