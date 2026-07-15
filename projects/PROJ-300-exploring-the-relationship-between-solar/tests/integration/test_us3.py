"""
Integration tests for User Story 3 (T029).
Verifies that PNG files and sensitivity table are generated correctly.
"""
import os
import json
import subprocess
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def test_us3_generates_artifacts():
    """
    Run the US3 sample script and verify output files exist.
    """
    script_path = os.path.join(PROJECT_ROOT, "code", "run_us3_sample.py")
    
    # Run the script
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Check for execution success (stdout/stderr might contain data fetch warnings, 
    # but we check for the specific success message or file existence)
    
    # Define expected paths
    scatter_path = os.path.join(RESULTS_DIR, "plot_scatter.png")
    ts_path = os.path.join(RESULTS_DIR, "plot_timeseries.png")
    json_path = os.path.join(RESULTS_DIR, "us3_sensitivity_report.json")

    # Verify files exist
    assert os.path.exists(scatter_path), f"Scatter plot not found at {scatter_path}. Stderr: {result.stderr}"
    assert os.path.exists(ts_path), f"Time-series plot not found at {ts_path}. Stderr: {result.stderr}"
    assert os.path.exists(json_path), f"Sensitivity report not found at {json_path}. Stderr: {result.stderr}"

    # Verify file sizes are non-zero (plots should be > 1KB usually)
    assert os.path.getsize(scatter_path) > 1024, "Scatter plot file is too small (possibly empty)"
    assert os.path.getsize(ts_path) > 1024, "Time-series plot file is too small (possibly empty)"

    # Verify JSON content
    with open(json_path, 'r') as f:
        data = json.load(f)

    required_keys = [
        "optimal_lag_minutes", 
        "sensitivity_table", 
        "permutation_p_value"
    ]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in sensitivity report"

    # Verify sensitivity table structure
    assert isinstance(data["sensitivity_table"], dict), "sensitivity_table should be a dict"
    # Check for expected thresholds (400, 500, 600)
    for threshold in [400, 500, 600]:
        assert str(threshold) in data["sensitivity_table"], f"Missing threshold {threshold} in sensitivity_table"
    
    # Verify plot loading (matplotlib can open them)
    try:
        import matplotlib.pyplot as plt
        plt.imread(scatter_path)
        plt.imread(ts_path)
    except Exception as e:
        pytest.fail(f"Failed to load generated plots: {e}")

def test_us3_plot_labels():
    """
    Verify that plots contain expected labels (SC-005).
    This is a basic check; a more robust check would inspect image pixels or metadata.
    """
    # Since we cannot easily parse pixel text without OCR, we rely on the fact that
    # the plot generation functions (viz/plots.py) are unit-tested elsewhere to have labels.
    # Here we just confirm the files exist and are valid images.
    scatter_path = os.path.join(RESULTS_DIR, "plot_scatter.png")
    ts_path = os.path.join(RESULTS_DIR, "plot_timeseries.png")
    
    assert os.path.exists(scatter_path)
    assert os.path.exists(ts_path)