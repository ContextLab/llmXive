"""
Unit tests for the LODO robustness implementation (T006).

The tests verify that:
  * ``leave_one_device_out`` creates ``robustness_results.csv``.
  * The number of distinct ``omitted_device`` values equals the number of
    devices in the merged dataset.
  * ``robustness_check_bootstrap`` runs without raising when a valid
    ``stability_score.txt`` file is present (the file is generated on‑the‑fly
    if missing, using the fetcher bootstrap routine).
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from stats_engine import (
    load_and_merge_metrics,
    leave_one_device_out,
    robustness_check_bootstrap,
)
from fetcher import compare_current_vs_historical

@pytest.fixture
def merged_df(tmp_path):
    """
    Create a tiny deterministic merged DataFrame for testing.
    The fixture writes temporary performance and graph CSVs, then loads
    them via ``load_and_merge_metrics``.
    """
    # Performance CSV
    perf = pd.DataFrame(
        {
            "device_id": ["devA", "devB", "devC"],
            "t1_mean": [12.0, 24.0, 36.0],
            "t2_mean": [5.0, 5.0, 5.0],
            "cx_error_mean": [0.01, 0.02, 0.03],
            "readout_error_mean": [0.02, 0.02, 0.02],
            "chip_family": ["famX", "famX", "famY"],
        }
    )
    perf_path = tmp_path / "performance_metrics.csv"
    perf.to_csv(perf_path, index=False)

    # Graph CSV (long format)
    graph = pd.DataFrame(
        {
            "device_id": ["devA", "devB", "devC", "devA", "devB", "devC"],
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
    graph.to_csv(graph_path, index=False)

    # Monkey‑patch the default paths inside stats_engine for this test
    # by temporarily changing the working directory to ``tmp_path``.
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Load via the public helper (which reads the CSVs we just created)
        merged = load_and_merge_metrics(
            performance_path=str(perf_path), graph_path=str(graph_path)
        )
        yield merged
    finally:
        os.chdir(cwd)

def test_leave_one_device_out_creates_csv(merged_df, tmp_path):
    """
    ``leave_one_device_out`` should write a CSV file with one row per
    omitted device per metric pair.  The file must exist and contain the
    expected columns.
    """
    # Ensure the output directory is inside the temporary directory
    out_path = tmp_path / "robustness_results.csv"
    # Call the function with an explicit output path to avoid side‑effects
    lodo_df = leave_one_device_out(
        merged_df,
        numeric_cols=merged_df.select_dtypes(include=[float, int]).columns.tolist(),
        output_path=str(out_path),
    )
    # The function returns the DataFrame and also writes the CSV.
    assert out_path.is_file(), "robustness_results.csv was not created"

    # Verify required columns are present
    expected_cols = {
        "omitted_device",
        "metric_a",
        "metric_b",
        "rho",
        "p_value",
        "max_influence",
    }
    assert set(lodo_df.columns) == expected_cols

    # The number of distinct omitted devices should equal the number of devices
    device_count = merged_df["device_id"].nunique()
    assert lodo_df["omitted_device"].nunique() == device_count

def test_bootstrap_stability_check(tmp_path):
    """
    ``robustness_check_bootstrap`` must succeed when a valid
    ``stability_score.txt`` file exists with a value ≥ 0.7.
    The test creates such a file (using the real bootstrap routine) and
    then calls the checker.
    """
    # Generate a realistic stability score using the fetcher routine.
    # This writes ``data/processed/stability_score.txt`` relative to the
    # project root.  We run it inside the temporary directory to keep the
    # repository clean.
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # ``compare_current_vs_historical`` creates the required file.
        compare_current_vs_historical()
        # Now run the robustness guard – it will raise if the score is < 0.7.
        robustness_check_bootstrap()
    finally:
        os.chdir(cwd)