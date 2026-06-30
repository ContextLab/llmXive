"""
Integration tests for User Story 2: Identify Optimal Propagation Lag.
Verifies that the lag-sweep reports L* and corresponding correlation values (FR-010).
"""
import os
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Ensure we can import from the project code directory
import sys
import pathlib
project_root = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from main import run_pipeline
from analysis.lag_search import find_optimal_lag
from data.clean import clean_and_resample
from data.lag import apply_lag_shift, calculate_physics_lag
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

RESULTS_DIR = project_root / "results"
OUTPUT_FILE = RESULTS_DIR / "us1_correlation.json"

@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup if necessary, though we overwrite

def test_lag_sweep_reports_optimal_lag_and_correlation():
    """
    Verify the lag-sweep reports L* and corresponding correlation values.
    This test runs the pipeline on a small synthetic dataset to ensure
    the logic for finding the optimal lag and recording it works.
    """
    # Create a synthetic dataset with a known correlation structure
    # We will simulate a lag of 45 minutes.
    n_points = 100
    base_time = datetime(2023, 1, 1)
    timestamps = [base_time + timedelta(minutes=i*5) for i in range(n_points)]
    
    # Create Vsw with a trend
    vsw_values = np.linspace(400, 600, n_points) + np.random.normal(0, 10, n_points)
    
    # Create Ey that correlates with Vsw but shifted by 9 steps (45 mins)
    # Ey[t] ~ Vsw[t - 9]
    ey_values = np.zeros(n_points)
    for i in range(9, n_points):
        # Simple linear relationship with noise
        ey_values[i] = 0.5 * vsw_values[i-9] + np.random.normal(0, 5)
    
    df_vsw = pd.DataFrame({
        "timestamp": timestamps,
        "Vsw": vsw_values
    })
    df_ey = pd.DataFrame({
        "timestamp": timestamps,
        "Ey": ey_values
    })

    # Run the lag search directly to verify the function works
    # We pass the raw data, but the function expects it to be clean/resampled
    # For this test, we assume the data is already at the correct cadence (5 min)
    optimal_lag, lag_correlation_value = find_optimal_lag(
        df_vsw["Vsw"],
        df_ey["Ey"],
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )

    # Assertions
    assert optimal_lag is not None, "Optimal lag should be found"
    assert isinstance(optimal_lag, (int, float)), "Optimal lag should be numeric"
    assert optimal_lag >= LAG_WINDOW_MIN, f"Optimal lag {optimal_lag} should be >= {LAG_WINDOW_MIN}"
    assert optimal_lag <= LAG_WINDOW_MAX, f"Optimal lag {optimal_lag} should be <= {LAG_WINDOW_MAX}"
    
    assert lag_correlation_value is not None, "Correlation value should be found"
    assert isinstance(lag_correlation_value, (int, float)), "Correlation value should be numeric"
    assert abs(lag_correlation_value) <= 1.0, "Correlation value should be between -1 and 1"

    # Verify the optimal lag is close to our injected lag of 45 minutes
    # Allow for some variance due to noise, but it should be the peak
    # Since we injected exactly 45 mins (9 steps * 5 min), we expect the peak there.
    # However, noise might shift it slightly to 40 or 50.
    assert abs(optimal_lag - 45) <= 5, f"Optimal lag {optimal_lag} should be close to 45 (injected lag)"

def test_full_pipeline_output_contains_lag_fields():
    """
    Verify that the full pipeline (via main.py) produces the JSON report
    containing 'optimal_lag' and 'lag_correlation_value'.
    """
    # We will run the pipeline with a very short, synthetic date range
    # to avoid external API calls if possible, or use a mock.
    # Since the main.py likely calls fetch functions, we need to ensure
    # we don't hit rate limits or fail on missing data.
    # For this integration test, we assume the environment has connectivity
    # or we mock the fetch functions.
    # Given the constraints, we will run the pipeline on a tiny synthetic window
    # by patching the ingest functions if necessary, or relying on the fact
    # that the previous tasks (T020-T023) set up the pipeline to handle this.
    
    # To make this robust without external dependencies, we will patch the fetch functions
    # to return our synthetic data.
    from unittest.mock import patch
    
    synthetic_vsw = pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=50, freq="5min"),
        "Vsw": np.linspace(400, 600, 50)
    })
    synthetic_ey = pd.DataFrame({
        "timestamp": pd.date_range(start="2023-01-01", periods=50, freq="5min"),
        "Ey": np.linspace(0.5, 2.0, 50) # Simple correlation
    })

    with patch('main.fetch_omni_sw', return_value=synthetic_vsw), \
         patch('main.fetch_themis_ey', return_value=synthetic_ey):
        
        try:
            run_pipeline(
                start_date="2023-01-01",
                end_date="2023-01-02",
                output_dir=str(RESULTS_DIR)
            )
        except Exception as e:
            # If the pipeline fails due to other reasons, we check if the file exists
            # and if not, we fail the test.
            if not OUTPUT_FILE.exists():
                pytest.fail(f"Pipeline failed to generate output file: {e}")
            raise

    # Check if the output file exists
    assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} was not created"

    # Load and verify content
    with open(OUTPUT_FILE, 'r') as f:
        report = json.load(f)

    # Verify required keys exist
    assert "optimal_lag" in report, "Report must contain 'optimal_lag'"
    assert "lag_correlation_value" in report, "Report must contain 'lag_correlation_value'"

    # Verify types
    assert isinstance(report["optimal_lag"], (int, float)), "optimal_lag must be numeric"
    assert isinstance(report["lag_correlation_value"], (int, float)), "lag_correlation_value must be numeric"

    # Verify constraints from config
    assert LAG_WINDOW_MIN <= report["optimal_lag"] <= LAG_WINDOW_MAX, \
        f"optimal_lag {report['optimal_lag']} out of bounds [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}]"
    assert -1.0 <= report["lag_correlation_value"] <= 1.0, \
        f"lag_correlation_value {report['lag_correlation_value']} out of bounds [-1, 1]"