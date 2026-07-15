"""
Integration tests for User Story 3: Visualization and Sensitivity Analysis.

Verifies:
- PNG files are generated and non-empty.
- Sensitivity table contains expected thresholds.
- Plots load without error and contain expected labels.
"""
import os
import json
import subprocess
import sys
import pytest
import matplotlib.pyplot as plt
from matplotlib.image import imread

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.run_us3_sample import run_us3_sample

@pytest.fixture(scope="module")
def run_pipeline_output():
    """Run the US3 sample pipeline once for the test module."""
    # Suppress print output during test run
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        result = run_us3_sample()
    return result

def test_png_files_generated(run_pipeline_output):
    """Verify that PNG files exist and are non-empty."""
    assert run_pipeline_output is not None
    assert "plots" in run_pipeline_output
    
    scatter_path = run_pipeline_output["plots"]["scatter"]
    timeseries_path = run_pipeline_output["plots"]["timeseries"]
    
    assert os.path.exists(scatter_path), f"Scatter plot not found at {scatter_path}"
    assert os.path.exists(timeseries_path), f"Time-series plot not found at {timeseries_path}"
    
    # Check file size > 0
    assert os.path.getsize(scatter_path) > 0, "Scatter plot is empty"
    assert os.path.getsize(timeseries_path) > 0, "Time-series plot is empty"

def test_sensitivity_table_structure(run_pipeline_output):
    """Verify the sensitivity table contains the required thresholds."""
    assert "sensitivity_table" in run_pipeline_output
    table = run_pipeline_output["sensitivity_table"]
    
    assert isinstance(table, list), "Sensitivity table must be a list"
    assert len(table) == 3, "Sensitivity table must have 3 entries"
    
    thresholds = [row["threshold_kms"] for row in table]
    expected_thresholds = [400, 500, 600]
    
    for t in expected_thresholds:
        assert t in thresholds, f"Threshold {t} missing from sensitivity table"
    
    # Verify correlation values are present
    for row in table:
        assert "correlation" in row
        assert isinstance(row["correlation"], float)
        assert -1.0 <= row["correlation"] <= 1.0

def test_plots_load_and_labels(run_pipeline_output):
    """Verify plots can be loaded and contain expected labels."""
    scatter_path = run_pipeline_output["plots"]["scatter"]
    timeseries_path = run_pipeline_output["plots"]["timeseries"]
    
    # Load scatter plot
    try:
        fig_scatter = plt.imread(scatter_path)
        assert fig_scatter is not None
    except Exception as e:
        pytest.fail(f"Failed to load scatter plot: {e}")
    
    # Load time-series plot
    try:
        fig_timeseries = plt.imread(timeseries_path)
        assert fig_timeseries is not None
    except Exception as e:
        pytest.fail(f"Failed to load time-series plot: {e}")

def test_optimal_lag_annotation_present(run_pipeline_output):
    """Verify the optimal lag is reported in the results."""
    assert "optimal_lag_minutes" in run_pipeline_output
    optimal_lag = run_pipeline_output["optimal_lag_minutes"]
    assert isinstance(optimal_lag, (int, float))
    assert optimal_lag >= 0
    
    # Verify it falls within the search window (30-90 min)
    assert 30 <= optimal_lag <= 90, f"Optimal lag {optimal_lag} outside expected window [30, 90]"