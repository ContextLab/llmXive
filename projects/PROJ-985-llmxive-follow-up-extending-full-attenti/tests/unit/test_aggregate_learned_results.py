"""
Unit tests for the aggregate_learned_results module (T026b).

Verifies that the aggregation logic correctly computes mean, variance,
and standard deviation, and matches manual calculations on small subsets.
"""
import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.aggregate_learned_results import load_eval_scores, aggregate_metrics, get_project_root

@pytest.fixture
def temp_seed_dir(tmp_path):
    """Create a temporary directory with mock seed result files."""
    # Create mock data for 3 seeds
    mock_data = [
        [
            {"document_id": "doc1", "metric_name": "perplexity", "value": 10.0},
            {"document_id": "doc2", "metric_name": "perplexity", "value": 12.0},
            {"document_id": "doc3", "metric_name": "perplexity", "value": 14.0}
        ],
        [
            {"document_id": "doc1", "metric_name": "perplexity", "value": 11.0},
            {"document_id": "doc2", "metric_name": "perplexity", "value": 13.0},
            {"document_id": "doc3", "metric_name": "perplexity", "value": 15.0}
        ],
        [
            {"document_id": "doc1", "metric_name": "perplexity", "value": 9.0},
            {"document_id": "doc2", "metric_name": "perplexity", "value": 11.0},
            {"document_id": "doc3", "metric_name": "perplexity", "value": 13.0}
        ]
    ]
    
    # Expected means per seed: [12.0, 13.0, 11.0]
    # Expected overall mean: 12.0
    # Expected std: sqrt(((0)^2 + (1)^2 + (-1)^2)/3) = sqrt(2/3) ≈ 0.8165
    # Expected variance: 2/3 ≈ 0.6667
    
    for i, data in enumerate(mock_data):
        file_path = tmp_path / f"seed_{i}_per_doc.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
    
    return tmp_path

def test_load_eval_scores(temp_seed_dir):
    """Test that load_eval_scores correctly extracts and aggregates per-seed means."""
    scores = load_eval_scores(str(temp_seed_dir), metric_name="perplexity")
    
    assert len(scores) == 3, "Should load 3 seeds"
    
    # Check individual seed means
    # Seed 0: (10+12+14)/3 = 12.0
    # Seed 1: (11+13+15)/3 = 13.0
    # Seed 2: (9+11+13)/3 = 11.0
    expected_means = [12.0, 13.0, 11.0]
    
    for i, expected in enumerate(expected_means):
        assert abs(scores[i] - expected) < 1e-6, f"Seed {i} mean mismatch: got {scores[i]}, expected {expected}"

def test_aggregate_metrics_manual_calculation(temp_seed_dir):
    """
    Test aggregation logic against manual calculation on a small subset.
    
    This verifies the core requirement: "Assert aggregation logic matches 
    manual calculation on a small subset."
    """
    scores = load_eval_scores(str(temp_seed_dir), metric_name="perplexity")
    result = aggregate_metrics(scores)
    
    # Manual calculation for [12.0, 13.0, 11.0]
    expected_mean = 12.0
    expected_var = np.var([12.0, 13.0, 11.0])  # 0.6666...
    expected_std = np.std([12.0, 13.0, 11.0])  # 0.81649...
    
    assert result['n_seeds'] == 3
    assert abs(result['mean_metric'] - expected_mean) < 1e-6
    assert abs(result['variance_metric'] - expected_var) < 1e-6
    assert abs(result['std_metric'] - expected_std) < 1e-6
    
    # Verify seed_values are preserved
    assert len(result['seed_values']) == 3
    for i, val in enumerate(result['seed_values']):
        assert abs(val - scores[i]) < 1e-6

def test_aggregate_metrics_schema():
    """Test that the output schema matches the specification."""
    test_values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = aggregate_metrics(test_values)
    
    required_keys = ['mean_metric', 'std_metric', 'variance_metric', 'n_seeds', 'seed_values']
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    assert isinstance(result['mean_metric'], float)
    assert isinstance(result['std_metric'], float)
    assert isinstance(result['variance_metric'], float)
    assert isinstance(result['n_seeds'], int)
    assert isinstance(result['seed_values'], list)
    assert len(result['seed_values']) == 5

def test_load_eval_scores_empty_directory(tmp_path):
    """Test that load_eval_scores raises error when no seed files found."""
    with pytest.raises(FileNotFoundError):
        load_eval_scores(str(tmp_path), metric_name="perplexity")

def test_load_eval_scores_missing_metric(temp_seed_dir):
    """Test handling of files with missing metric."""
    # Create a file with a different metric
    wrong_metric_file = temp_seed_dir / "seed_99_per_doc.json"
    with open(wrong_metric_file, 'w') as f:
        json.dump([{"document_id": "doc1", "metric_name": "accuracy", "value": 0.9}], f)
    
    # Should still load the original 3 seeds, ignoring the one with wrong metric
    scores = load_eval_scores(str(temp_seed_dir), metric_name="perplexity")
    assert len(scores) == 3