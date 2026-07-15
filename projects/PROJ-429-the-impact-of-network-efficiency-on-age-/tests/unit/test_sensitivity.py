"""
Unit tests for code/stats/sensitivity.py
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions to test
from stats.sensitivity import (
    compute_metrics_at_threshold,
    aggregate_metrics,
    calculate_stability,
    STABILITY_TOLERANCE
)

@pytest.fixture
def sample_matrices():
    """Create a mock dictionary of connectivity matrices."""
    # 3x3 symmetric matrix with positive weights
    matrix1 = np.array([
        [0.0, 0.8, 0.2],
        [0.8, 0.0, 0.5],
        [0.2, 0.5, 0.0]
    ])
    matrix2 = np.array([
        [0.0, 0.9, 0.3],
        [0.9, 0.0, 0.6],
        [0.3, 0.6, 0.0]
    ])
    return {
        'subj_001': matrix1,
        'subj_002': matrix2
    }

@patch('stats.sensitivity.compute_all_metrics')
def test_compute_metrics_at_threshold(mock_compute, sample_matrices):
    """Test that thresholding and metric computation works."""
    # Mock the return value of compute_all_metrics
    mock_compute.return_value = {
        'global_efficiency': 0.5,
        'local_efficiency': 0.4,
        'clustering_coefficient': 0.3
    }

    result = compute_metrics_at_threshold(sample_matrices, threshold=0.1)
    
    assert isinstance(result, dict)
    assert 'subj_001' in result
    assert 'subj_002' in result
    assert 'global_efficiency' in result['subj_001']
    
    # Verify the mock was called
    assert mock_compute.call_count == 2

def test_aggregate_metrics():
    """Test aggregation of metrics across subjects."""
    metrics_dict = {
        'subj_1': {'global_efficiency': 0.5, 'local_efficiency': 0.4},
        'subj_2': {'global_efficiency': 0.6, 'local_efficiency': 0.5},
        'subj_3': {'global_efficiency': 0.55, 'local_efficiency': 0.45}
    }
    
    aggregated = aggregate_metrics(metrics_dict)
    
    assert 'global_efficiency' in aggregated
    assert 'local_efficiency' in aggregated
    assert len(aggregated['global_efficiency']) == 3
    assert len(aggregated['local_efficiency']) == 3

def test_calculate_stability():
    """Test stability calculation logic."""
    # Case 1: Low variation (stable)
    aggregated_stable = {
        'metric_A': [0.5, 0.51, 0.49], # std ~ 0.01 < 0.05
        'metric_B': [0.1, 0.2, 0.3]    # std ~ 0.08 > 0.05
    }
    
    stats = calculate_stability(aggregated_stable)
    
    metric_a = next(s for s in stats if s['metric_name'] == 'metric_A')
    metric_b = next(s for s in stats if s['metric_name'] == 'metric_B')
    
    assert metric_a['is_stable'] is True
    assert metric_b['is_stable'] is False
    
    # Check std_dev calculation roughly
    assert metric_a['std_dev'] < STABILITY_TOLERANCE
    assert metric_b['std_dev'] >= STABILITY_TOLERANCE

def test_calculate_stability_single_value():
    """Test stability calculation with only one value (should not crash)."""
    aggregated = {
        'metric_A': [0.5]
    }
    
    stats = calculate_stability(aggregated)
    metric_a = next(s for s in stats if s['metric_name'] == 'metric_A')
    
    assert metric_a['std_dev'] == 0.0
    assert metric_a['is_stable'] is True # 0.0 < 0.05

def test_nan_handling():
    """Test that NaN values are excluded from aggregation."""
    metrics_dict = {
        'subj_1': {'metric_A': 0.5},
        'subj_2': {'metric_A': float('nan')},
        'subj_3': {'metric_A': 0.6}
    }
    
    aggregated = aggregate_metrics(metrics_dict)
    
    assert len(aggregated['metric_A']) == 2
    assert float('nan') not in aggregated['metric_A']
    assert 0.5 in aggregated['metric_A']
    assert 0.6 in aggregated['metric_A']