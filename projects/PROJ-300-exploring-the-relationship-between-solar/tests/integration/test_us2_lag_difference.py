import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure the project root is in the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import run_pipeline
from data.lag import calculate_physics_lag

@pytest.fixture
def sample_date_range():
    """Return a 3-day sample range for execution."""
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 4)
    return start, end

@pytest.fixture
def results_dir():
    """Return the expected results directory."""
    return os.path.join(PROJECT_ROOT, 'results')

@pytest.fixture
def json_report_path(results_dir):
    """Return the path to the JSON report."""
    return os.path.join(results_dir, 'us1_correlation.json')

def test_us2_lag_difference_calculation(json_report_path, results_dir):
    """
    T025 Verification: Verify the pipeline calculates and reports |L* - L_phys| (SC-002).
    
    This test executes the full pipeline (with real data fetch) and verifies that:
    1. The JSON report file is created.
    2. The 'lag_difference' key exists in the report.
    3. The value is a valid float.
    4. The value matches the absolute difference between the reported optimal_lag and the calculated physics lag.
    """
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    # Run the pipeline
    # We assume the pipeline is robust enough to handle the data fetch.
    # If it fails due to network, this test fails loudly (as required).
    try:
        run_pipeline(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 4),
            output_dir=results_dir
        )
    except Exception as e:
        pytest.fail(f"Pipeline execution failed: {e}")

    # Verify the JSON file exists
    assert os.path.exists(json_report_path), f"JSON report not found at {json_report_path}"

    # Load the report
    with open(json_report_path, 'r') as f:
        report = json.load(f)

    # Verify required keys exist
    assert 'optimal_lag' in report, "Missing 'optimal_lag' in report"
    assert 'l_phys' in report, "Missing 'l_phys' in report"
    assert 'lag_difference' in report, "Missing 'lag_difference' in report (SC-002 failure)"

    # Verify types
    optimal_lag = report['optimal_lag']
    l_phys = report['l_phys']
    lag_difference = report['lag_difference']

    assert isinstance(optimal_lag, (int, float, np.floating)), "optimal_lag is not numeric"
    assert isinstance(l_phys, (int, float, np.floating)), "l_phys is not numeric"
    assert isinstance(lag_difference, (int, float, np.floating)), "lag_difference is not numeric"

    # Verify the calculation: |L* - L_phys|
    expected_diff = abs(optimal_lag - l_phys)
    
    # Allow for floating point tolerance
    assert np.isclose(lag_difference, expected_diff, rtol=1e-5), \
        f"lag_difference ({lag_difference}) does not match |optimal_lag - l_phys| ({expected_diff})"

    print(f"SC-002 Verification Passed:")
    print(f"  Optimal Lag (L*): {optimal_lag} min")
    print(f"  Physics Lag (L_phys): {l_phys} min")
    print(f"  |L* - L_phys|: {lag_difference} min")