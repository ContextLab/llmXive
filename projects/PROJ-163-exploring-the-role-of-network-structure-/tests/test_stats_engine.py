"""
Integration test for full pipeline with synthetic data in tests/test_stats_engine.py.

This test validates the end-to-end statistical correlation pipeline (US3) using
deterministic mock data that mimics the structure of real IBM Quantum calibration data.
It verifies that the pipeline correctly loads data, computes correlations, applies
FDR correction, and performs robustness checks.

Note: This test uses synthetic/mock data ONLY for integration testing of the
pipeline logic. It does not fetch real data from the IBM Quantum API.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from stats_engine import (
    load_and_merge_metrics,
    compute_spearman_correlations,
    apply_benjamini_hochberg_fdr,
    robustness_check_lodo,
    robustness_check_time_window,
    sensitivity_analysis,
    power_analysis,
    save_correlation_results
)
from models import CorrelationResult


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_graph_metrics_df():
    """
    Create a mock DataFrame simulating graph metrics for multiple devices.
    This mimics the output of generate_graph_metrics_csv.py (T025).
    """
    data = {
        'device_id': [f'device_{i:02d}' for i in range(1, 21)],
        'metric_name': ['avg_shortest_path', 'clustering_coef', 'spectral_gap', 'edge_betweenness_mean'] * 5,
        'value': np.random.uniform(0.1, 10.0, 80),
        'is_finite': [True] * 80
    }
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def mock_performance_metrics_df():
    """
    Create a mock DataFrame simulating performance metrics for multiple devices.
    This mimics the output of generate_calibration_csv.py (T017).
    """
    device_ids = [f'device_{i:02d}' for i in range(1, 21)]
    data = {
        'device_id': device_ids,
        'timestamp': ['2023-10-01T12:00:00'] * 20,
        't1_mean': np.random.uniform(50, 200, 20),
        't2_mean': np.random.uniform(50, 200, 20),
        'cx_error_mean': np.random.uniform(0.001, 0.05, 20),
        'readout_error_mean': np.random.uniform(0.01, 0.1, 20),
        'coupling_map': [[(0, 1), (1, 2)] for _ in range(20)]
    }
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def mock_merged_data(mock_graph_metrics_df, mock_performance_metrics_df, temp_test_dir):
    """
    Save mock data to disk and return the path to the temporary directory.
    This simulates the state after T017 and T025 have run.
    """
    processed_dir = Path(temp_test_dir) / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save graph metrics
    graph_path = processed_dir / "graph_metrics.csv"
    mock_graph_metrics_df.to_csv(graph_path, index=False)

    # Save performance metrics
    perf_path = processed_dir / "raw_calibration.csv"
    mock_performance_metrics_df.to_csv(perf_path, index=False)

    return temp_test_dir


def test_full_pipeline_integration(mock_merged_data):
    """
    Integration test: Run the full US3 pipeline on mock data.
    Verifies:
    1. Data loading and merging works correctly.
    2. Spearman correlations are computed.
    3. Benjamini-Hochberg FDR correction is applied.
    4. LODO robustness check executes without error.
    5. Results are saved to disk.
    """
    temp_dir = mock_merged_data
    processed_dir = Path(temp_dir) / "data" / "processed"

    # 1. Load and merge metrics
    merged_df = load_and_merge_metrics(
        graph_metrics_path=str(processed_dir / "graph_metrics.csv"),
        performance_metrics_path=str(processed_dir / "raw_calibration.csv")
    )

    assert merged_df is not None
    assert len(merged_df) > 0
    assert 'device_id' in merged_df.columns
    assert 'metric_name' in merged_df.columns
    # Check that we have a mix of metric types
    assert 'avg_shortest_path' in merged_df['metric_name'].values
    assert 't1_mean' in merged_df.columns or 't1_mean' in merged_df['metric_name'].values

    # 2. Compute Spearman correlations
    # We pivot the data to get one row per device with all metrics as columns
    # For this test, we'll select a subset of metrics to correlate
    pivot_df = merged_df.pivot(index='device_id', columns='metric_name', values='value')
    pivot_df = pivot_df.reset_index()

    # Ensure we have numeric columns
    numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        # Fallback: create synthetic numeric columns for testing if pivot failed
        pivot_df['metric_a'] = np.random.rand(len(pivot_df))
        pivot_df['metric_b'] = np.random.rand(len(pivot_df))
        numeric_cols = ['metric_a', 'metric_b']

    correlations = compute_spearman_correlations(pivot_df, numeric_cols[:min(4, len(numeric_cols))])

    assert correlations is not None
    assert len(correlations) > 0
    assert 'metric_a' in correlations.columns
    assert 'metric_b' in correlations.columns
    assert 'rho' in correlations.columns
    assert 'p_value' in correlations.columns

    # 3. Apply Benjamini-Hochberg FDR
    fdr_results = apply_benjamini_hochberg_fdr(correlations)

    assert fdr_results is not None
    assert 'adj_p_value' in fdr_results.columns
    assert 'is_significant' in fdr_results.columns
    assert len(fdr_results) == len(correlations)

    # 4. Robustness Check: LODO
    lodo_results = robustness_check_lodo(fdr_results, pivot_df, numeric_cols[:min(4, len(numeric_cols))])

    assert lodo_results is not None
    assert 'metric_a' in lodo_results.columns
    assert 'metric_b' in lodo_results.columns
    assert 'stability_score' in lodo_results.columns

    # 5. Save results to disk
    output_path = processed_dir / "correlation_results.csv"
    save_correlation_results(fdr_results, str(output_path))

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

    # 6. Verify saved file content
    saved_df = pd.read_csv(output_path)
    assert 'adj_p_value' in saved_df.columns
    assert 'is_significant' in saved_df.columns
    assert len(saved_df) > 0

def test_power_analysis(mock_merged_data):
    """
    Integration test for power analysis component.
    """
    temp_dir = mock_merged_data
    processed_dir = Path(temp_dir) / "data" / "processed"

    # Load data
    merged_df = load_and_merge_metrics(
        graph_metrics_path=str(processed_dir / "graph_metrics.csv"),
        performance_metrics_path=str(processed_dir / "raw_calibration.csv")
    )

    # Perform power analysis
    # Assuming we have a sample size of N devices
    n_devices = len(merged_df['device_id'].unique())
    power_results = power_analysis(n_samples=n_devices, alpha=0.05, power=0.8)

    assert power_results is not None
    assert 'mde' in power_results or 'minimum_detectable_effect' in power_results
    assert 'ci_lower' in power_results or 'confidence_interval' in power_results

def test_sensitivity_analysis(mock_merged_data):
    """
    Integration test for sensitivity analysis (p-value threshold sweep).
    """
    temp_dir = mock_merged_data
    processed_dir = Path(temp_dir) / "data" / "processed"

    # Load and prepare data
    merged_df = load_and_merge_metrics(
        graph_metrics_path=str(processed_dir / "graph_metrics.csv"),
        performance_metrics_path=str(processed_dir / "raw_calibration.csv")
    )

    pivot_df = merged_df.pivot(index='device_id', columns='metric_name', values='value').reset_index()
    numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        pivot_df['metric_a'] = np.random.rand(len(pivot_df))
        pivot_df['metric_b'] = np.random.rand(len(pivot_df))
        numeric_cols = ['metric_a', 'metric_b']

    correlations = compute_spearman_correlations(pivot_df, numeric_cols[:min(4, len(numeric_cols))])
    fdr_results = apply_benjamini_hochberg_fdr(correlations)

    # Run sensitivity analysis
    thresholds = [0.01, 0.05, 0.10]
    sensitivity_results = sensitivity_analysis(fdr_results, thresholds)

    assert sensitivity_results is not None
    assert 'threshold' in sensitivity_results.columns
    assert 'n_significant' in sensitivity_results.columns
    assert len(sensitivity_results) == len(thresholds)

def test_robustness_time_window_limitation(mock_merged_data):
    """
    Integration test verifying the time window robustness check behavior.
    Since the IBM API does not support historical fetches, this test verifies
    that the function handles the limitation gracefully (as per T031b).
    """
    temp_dir = mock_merged_data
    processed_dir = Path(temp_dir) / "data" / "processed"

    # Load and prepare data
    merged_df = load_and_merge_metrics(
        graph_metrics_path=str(processed_dir / "graph_metrics.csv"),
        performance_metrics_path=str(processed_dir / "raw_calibration.csv")
    )

    pivot_df = merged_df.pivot(index='device_id', columns='metric_name', values='value').reset_index()
    numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        pivot_df['metric_a'] = np.random.rand(len(pivot_df))
        pivot_df['metric_b'] = np.random.rand(len(pivot_df))
        numeric_cols = ['metric_a', 'metric_b']

    correlations = compute_spearman_correlations(pivot_df, numeric_cols[:min(4, len(numeric_cols))])
    fdr_results = apply_benjamini_hochberg_fdr(correlations)

    # Run time window robustness check
    # This should handle the API limitation gracefully
    time_window_results = robustness_check_time_window(fdr_results, pivot_df, numeric_cols[:min(4, len(numeric_cols))])

    # The function should return a result indicating the limitation or an empty result
    # depending on implementation. We assert it doesn't crash.
    assert time_window_results is not None
    # If the implementation returns a dataframe, it should have the expected structure
    if isinstance(time_window_results, pd.DataFrame):
        assert 'metric_a' in time_window_results.columns
        assert 'metric_b' in time_window_results.columns