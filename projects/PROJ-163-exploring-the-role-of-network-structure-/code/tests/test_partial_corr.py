"""
Unit test for the full‑covariate partial correlation analysis.

The test creates a minimal synthetic dataset that includes the required
covariate columns, runs ``partial_correlation_full`` and checks that:
1. The output CSV file is created.
2. The resulting DataFrame contains the expected columns.
3. All specified covariates are present in the input DataFrame (otherwise
   the function would raise).
"""

import os
import pandas as pd
import pytest
from pathlib import Path

from code.stats_engine import partial_correlation_full, load_and_merge_metrics

@pytest.fixture
def temp_data(tmp_path):
    """
    Create temporary performance and graph CSV files with the necessary
    covariate columns.
    """
    # Performance CSV with covariates
    perf_df = pd.DataFrame(
        {
            "device_id": ["devA", "devB", "devC"],
            "t1_mean": [10.0, 20.0, 30.0],
            "t2_mean": [5.0, 5.0, 5.0],
            "cx_error_mean": [0.01, 0.02, 0.03],
            "readout_error_mean": [0.02, 0.02, 0.02],
            # Covariate columns
            "chip_generation": [1, 2, 1],
            "qubit_count": [5, 5, 5],
            "device_age_days": [100, 200, 150],
            "readout_architecture": [0, 1, 0],
        }
    )
    perf_path = tmp_path / "performance_metrics.csv"
    perf_df.to_csv(perf_path, index=False)

    # Graph CSV (wide format after pivot)
    graph_long = pd.DataFrame(
        {
            "device_id": ["devA", "devB", "devC"],
            "metric_name": ["avg_shortest_path"] * 3,
            "value": [5.0, 4.0, 3.0],
        }
    )
    graph_path = tmp_path / "graph_metrics.csv"
    graph_long.to_csv(graph_path, index=False)

    return str(perf_path), str(graph_path), tmp_path

def test_partial_correlation_produces_csv(temp_data):
    perf_path, graph_path, tmp_dir = temp_data

    # Merge the data using the public helper
    merged_df = load_and_merge_metrics(performance_path=perf_path, graph_path=graph_path)

    # Run the partial correlation analysis
    output_path = os.path.join(tmp_dir, "partial_correlations.csv")
    result_df = partial_correlation_full(
        merged_df,
        covariates=[
            "chip_generation",
            "qubit_count",
            "device_age_days",
            "readout_architecture",
        ],
        output_path=output_path,
    )

    # Verify that the CSV file was written
    assert os.path.isfile(output_path), "partial_correlations.csv was not created"

    # Verify the DataFrame structure
    expected_columns = {"metric_a", "metric_b", "partial_rho", "p_value"}
    assert set(result_df.columns) == expected_columns

    # Ensure at least one result row exists (with three numeric metrics we have
    # at least one pair to correlate)
    assert not result_df.empty, "Resulting partial correlation DataFrame is empty"

    # Verify that the covariate columns are indeed present in the merged input
    for cov in [
        "chip_generation",
        "qubit_count",
        "device_age_days",
        "readout_architecture",
    ]:
        assert cov in merged_df.columns, f"Covariate {cov} missing from merged DataFrame"