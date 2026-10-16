"""
Unit tests for the statistical engine (correlation pipeline).

These tests use tiny synthetic datasets that are deterministic and
exercise the full workflow:
  1. Load and merge performance and graph metrics.
  2. Compute Spearman correlations.
  3. Apply Benjamini‑Hochberg FDR correction.
The data are written to temporary CSV files; no real IBM Quantum data
is required for the correctness checks.
"""

import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the functions from the stats_engine module
from code.stats_engine import (
    load_and_merge_metrics,
    compute_spearman_correlations,
    apply_benjamini_hochberg_fdr,
)

@pytest.fixture
def temp_perf_graph_paths(tmp_path):
    """
    Create temporary performance and graph CSV files with deterministic data.
    Returns a tuple (perf_path, graph_path).
    """
    # Performance CSV
    perf_df = pd.DataFrame(
        {
            "device_id": ["dev1", "dev2", "dev3"],
            "t1_mean": [10.0, 20.0, 30.0],
            "t2_mean": [5.0, 5.0, 5.0],
            "cx_error_mean": [0.01, 0.02, 0.03],
            "readout_error_mean": [0.02, 0.02, 0.02],
            "chip_family": ["famA", "famA", "famB"],
        }
    )
    perf_path = tmp_path / "performance_metrics.csv"
    perf_df.to_csv(perf_path, index=False)

    # Graph CSV (wide format after pivot)
    graph_long = pd.DataFrame(
        {
            "device_id": ["dev1", "dev2", "dev3", "dev1", "dev2", "dev3"],
            "metric_name": [
                "avg_shortest_path",
                "avg_shortest_path",
                "avg_shortest_path",
                "clustering_coeff",
                "clustering_coeff",
                "clustering_coeff",
            ],
            "value": [5.0, 4.0, 3.0, 0.8, 0.7, 0.6],
            "is_finite": [True] * 6,
        }
    )
    graph_path = tmp_path / "graph_metrics.csv"
    graph_long.to_csv(graph_path, index=False)

    return str(perf_path), str(graph_path)

def test_load_and_merge_metrics(temp_perf_graph_paths):
    perf_path, graph_path = temp_perf_graph_paths
    merged = load_and_merge_metrics(performance_path=perf_path, graph_path=graph_path)

    # After merging, we should have the original performance columns plus the two graph metrics
    expected_columns = {
        "device_id",
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
        "chip_family",
        "avg_shortest_path",
        "clustering_coeff",
    }
    assert set(merged.columns) == expected_columns
    assert merged.shape[0] == 3  # three devices

def test_compute_spearman_correlations(temp_perf_graph_paths):
    perf_path, graph_path = temp_perf_graph_paths
    merged = load_and_merge_metrics(performance_path=perf_path, graph_path=graph_path)

    corr_df = compute_spearman_correlations(merged)

    # We know that t1_mean (10,20,30) and avg_shortest_path (5,4,3) are perfectly negatively correlated
    # Hence rho should be -1.0 and p_value should be 0.0 (exact for 3 points)
    row = corr_df[
        (corr_df["metric_a"] == "t1_mean") & (corr_df["metric_b"] == "avg_shortest_path")
    ].iloc[0]

    assert np.isclose(row["rho"], -1.0)
    assert np.isclose(row["p_value"], 0.0)

def test_apply_benjamini_hochberg_fdr(temp_perf_graph_paths):
    perf_path, graph_path = temp_perf_graph_paths
    merged = load_and_merge_metrics(performance_path=perf_path, graph_path=graph_path)

    raw_corr = compute_spearman_correlations(merged)
    corrected = apply_benjamini_hochberg_fdr(raw_corr, alpha=0.05)

    # With only a few tests, the adjusted p‑values should equal the raw p‑values
    pd.testing.assert_series_equal(
        corrected["p_value"], corrected["adj_p_value"], check_names=False
    )
    # The known significant pair (t1_mean vs avg_shortest_path) should be flagged as significant
    sig_row = corrected[
        (corrected["metric_a"] == "t1_mean") & (corrected["metric_b"] == "avg_shortest_path")
    ].iloc[0]
    assert sig_row["is_significant"] is True
    # All other pairs should have is_significant = False (they have higher p‑values)
    other = corrected[
        ~(
            (corrected["metric_a"] == "t1_mean")
            & (corrected["metric_b"] == "avg_shortest_path")
        )
    ]
    assert other["is_significant"].sum() == 0