import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import functions to test
from stats.sensitivity import (
    compute_metrics_at_threshold,
    calculate_stability,
    aggregate_metrics,
    run_sensitivity_analysis
)
from network.metrics import compute_all_metrics

def test_compute_metrics_at_threshold():
    """Test that thresholding and metric computation works."""
    # Create a simple 4x4 connectivity matrix
    conn_matrix = np.array([
        [0.0, 0.8, 0.2, 0.1],
        [0.8, 0.0, 0.9, 0.3],
        [0.2, 0.9, 0.0, 0.7],
        [0.1, 0.3, 0.7, 0.0]
    ])

    # Test with threshold 0.5
    metrics = compute_metrics_at_threshold(conn_matrix, 0.5)

    # Check that metrics are returned and are numeric
    assert 'global_efficiency' in metrics
    assert 'local_efficiency' in metrics
    assert isinstance(metrics['global_efficiency'], (int, float, np.floating))
    assert not np.isnan(metrics['global_efficiency'])

def test_aggregate_metrics():
    """Test aggregation of metrics across subjects."""
    metrics_list = [
        {'global_efficiency': 0.5, 'local_efficiency': 0.3},
        {'global_efficiency': 0.6, 'local_efficiency': 0.4},
        {'global_efficiency': 0.4, 'local_efficiency': 0.2}
    ]

    metric_names = ['global_efficiency', 'local_efficiency']
    aggregated = aggregate_metrics(metrics_list, metric_names)

    assert 'global_efficiency' in aggregated
    assert 'local_efficiency' in aggregated
    assert abs(aggregated['global_efficiency']['mean'] - 0.5) < 1e-6
    assert abs(aggregated['local_efficiency']['mean'] - 0.3) < 1e-6
    assert aggregated['global_efficiency']['std'] > 0

def test_calculate_stability():
    """Test stability calculation."""
    aggregated_metrics = {
        'global_efficiency': {'mean': 0.5, 'std': 0.02},  # Stable
        'local_efficiency': {'mean': 0.3, 'std': 0.1}     # Unstable
    }

    stability = calculate_stability(aggregated_metrics, 0.5, stability_threshold=0.05)

    assert stability['global_efficiency'] == True
    assert stability['local_efficiency'] == False

def test_run_sensitivity_analysis_integration(tmp_path):
    """Integration test for the full sensitivity analysis pipeline."""
    # Create a mock epochs directory structure with fake connectivity matrices
    epochs_dir = tmp_path / "processed" / "epochs"
    epochs_dir.mkdir(parents=True)

    subject_dir = epochs_dir / "subject_001"
    subject_dir.mkdir()

    # Create a fake connectivity matrix file
    conn_matrix = np.array([
        [0.0, 0.8, 0.2, 0.1],
        [0.8, 0.0, 0.9, 0.3],
        [0.2, 0.9, 0.0, 0.7],
        [0.1, 0.3, 0.7, 0.0]
    ])
    np.savez(subject_dir / "connectivity_0.npz", connectivity=conn_matrix)

    output_path = tmp_path / "sensitivity_report.csv"

    # Run the analysis
    df = run_sensitivity_analysis(epochs_dir, output_path)

    # Verify output
    assert output_path.exists()
    assert df.shape[0] > 0
    assert 'threshold' in df.columns
    assert 'metric_name' in df.columns
    assert 'std_dev' in df.columns
    assert 'is_stable' in df.columns
    assert df['threshold'].nunique() > 1  # Multiple thresholds tested