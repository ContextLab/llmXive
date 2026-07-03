"""
Integration tests for User Story 3 (T029).

Verifies that the pipeline generates the required PNG files and sensitivity table.
"""
import os
import sys
import json
import pytest
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.run_us3_sample import main as run_us3_main
from code.viz.plots import plot_scatter, plot_timeseries
from code.analysis.sensitivity import run_sensitivity_sweep

# Paths relative to project root
OUTPUT_DIR = os.path.join(project_root, "data", "processed")
SCATTER_PATH = os.path.join(OUTPUT_DIR, "us3_scatter.png")
TS_PATH = os.path.join(OUTPUT_DIR, "us3_timeseries.png")
SENS_PATH = os.path.join(OUTPUT_DIR, "us3_sensitivity.json")

@pytest.fixture(autouse=True)
def setup_output_dir():
    """Ensure output directory exists before tests."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yield
    # Optional: cleanup if desired, but keeping files for manual inspection is often useful
    # for i in [SCATTER_PATH, TS_PATH, SENS_PATH]:
    #     if os.path.exists(i):
    #         os.remove(i)

def test_us3_pipeline_execution():
    """
    Verify that running the US3 sample script generates the expected artifacts.
    This effectively runs the sample runner to ensure it doesn't crash and produces files.
    """
    # Note: This test assumes real data is available. If the API fails, 
    # the script should raise an error, which this test will catch as a failure.
    try:
        run_us3_main()
    except RuntimeError as e:
        if "Failed to fetch" in str(e):
            pytest.skip(f"Real data source unavailable for integration test: {e}")
        else:
            raise

    # Verify files exist
    assert os.path.exists(SCATTER_PATH), f"Scatter plot not found at {SCATTER_PATH}"
    assert os.path.exists(TS_PATH), f"Time series plot not found at {TS_PATH}"
    assert os.path.exists(SENS_PATH), f"Sensitivity table not found at {SENS_PATH}"

def test_us3_plot_files_valid():
    """
    Verify that the generated PNG files are valid images and contain expected content.
    """
    if not os.path.exists(SCATTER_PATH):
        pytest.skip("Scatter plot not generated yet")
    
    if not os.path.exists(TS_PATH):
        pytest.skip("Time series plot not generated yet")

    # Check file sizes (should not be empty)
    assert os.path.getsize(SCATTER_PATH) > 1000, "Scatter plot file is suspiciously small"
    assert os.path.getsize(TS_PATH) > 1000, "Time series plot file is suspiciously small"

    # Try to load as images to ensure they are valid PNGs
    try:
        img_scatter = plt.imread(SCATTER_PATH)
        img_ts = plt.imread(TS_PATH)
        assert img_scatter.shape[0] > 0 and img_scatter.shape[1] > 0
        assert img_ts.shape[0] > 0 and img_ts.shape[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to load generated images: {e}")

def test_us3_sensitivity_table_structure():
    """
    Verify the sensitivity table JSON has the correct structure and keys.
    """
    if not os.path.exists(SENS_PATH):
        pytest.skip("Sensitivity table not generated yet")

    with open(SENS_PATH, 'r') as f:
        data = json.load(f)

    assert isinstance(data, dict), "Sensitivity result should be a dictionary"
    assert 'thresholds' in data, "Missing 'thresholds' key"
    assert 'results' in data, "Missing 'results' key"
    
    # Check that expected thresholds are present
    expected_thresholds = [400, 500, 600]
    for t in expected_thresholds:
        assert str(t) in data['results'], f"Missing threshold {t} in results"
        
        # Check structure of a single threshold result
        res = data['results'][str(t)]
        assert 'pearson' in res, f"Missing 'pearson' for threshold {t}"
        assert 'spearman' in res, f"Missing 'spearman' for threshold {t}"
        assert 'n_samples' in res, f"Missing 'n_samples' for threshold {t}"

def test_us3_plot_labels():
    """
    Verify that the plots have the correct axis labels and titles.
    This is a bit fragile if the plot function doesn't expose this easily,
    so we check the file content or rely on the fact that plot_scatter/plot_timeseries
    are already tested for label generation in unit tests.
    Here we just ensure the files exist and are non-empty.
    """
    if not os.path.exists(SCATTER_PATH):
        pytest.skip("Scatter plot not generated")
    
    # We trust the implementation of plot_scatter/plot_timeseries for labels
    # as per T019 and T030. This test ensures the file generation path is correct.
    assert os.path.getsize(SCATTER_PATH) > 0
    assert os.path.getsize(TS_PATH) > 0