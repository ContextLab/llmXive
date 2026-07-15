"""
Integration tests for the lag-adjusted correlation pipeline (US-1 Independent Test).
Verifies that the full pipeline produces the expected JSON output structure
including Pearson/Spearman coefficients, permutation p-values, and significance flags.
"""
import os
import json
import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import run_pipeline
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

# Test constants
TEST_DATE_START = datetime(2023, 6, 15, 0, 0, 0)
TEST_DATE_END = datetime(2023, 6, 15, 23, 59, 59)
# Adjust path to be relative to the project root where the task runs
# The task description says `projects/PROJ-300...` but the code structure
# implies we are running from the project root. We will use a relative path
# that works from the project root `projects/PROJ-300-exploring-the-relationship-between-solar/`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
EXPECTED_OUTPUT_PATH = os.path.join(RESULTS_DIR, "us1_correlation.json")

EXPECTED_KEYS = [
    'pearson', 'spearman', 'p_val_permutation', 'significant_flag', 
    'optimal_lag', 'lag_correlation_value', 'lag_difference'
]

@pytest.fixture
def mock_real_data():
    """
    Mock the data ingestion functions to return realistic synthetic data
    that mimics the structure and range of real solar wind and THEMIS data.
    This allows the pipeline to run without network calls while testing the logic.
    """
    import pandas as pd
    import numpy as np

    # Generate realistic time series
    n_points = 288  # ~5-min resolution for 24 hours
    timestamps = pd.date_range(start=TEST_DATE_START, periods=n_points, freq='5min')

    # Simulate Vsw: 350-750 km/s with some structure
    np.random.seed(42)
    vsw_base = 500 + 100 * np.sin(np.linspace(0, 4*np.pi, n_points))
    vsw_noise = np.random.normal(0, 30, n_points)
    vsw = vsw_base + vsw_noise
    vsw = np.clip(vsw, 300, 900)  # Physical bounds

    # Simulate Bz: -10 to +10 nT
    bz = 5 * np.sin(np.linspace(0, 6*np.pi, n_points)) + np.random.normal(0, 2, n_points)

    # Simulate Ey: -0.5 to +0.5 mV/m, correlated with Vsw and Bz
    # Introduce a lagged relationship: Ey responds to Vsw * Bz with ~45 min lag
    product = vsw * bz
    # Apply a simple lag effect (shifted correlation)
    lag_idx = 9  # ~45 minutes at 5-min resolution
    ey = np.zeros(n_points)
    for i in range(lag_idx, n_points):
        # Ey correlates with Vsw*Bz from ~45 min ago, plus noise
        ey[i] = 0.02 * product[i - lag_idx] + np.random.normal(0, 0.05)

    omni_df = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw,
        'Bz': bz
    })

    themis_df = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey
    })

    return omni_df, themis_df

def test_us1_full_pipeline(mock_real_data):
    """
    US-1 Independent Test: Run the full pipeline on a sample date range
    and verify the output JSON contains all required keys with valid values.
    
    Acceptance Criteria:
    - Pipeline executes without error
    - Output file exists at expected path
    - JSON contains: pearson, spearman, p_val_permutation, significant_flag
    - Numeric values are within expected ranges
    """
    omni_df, themis_df = mock_real_data

    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Mock the data fetch functions to return our realistic synthetic data
    with patch('code.data.ingest.fetch_omni_sw', return_value=omni_df), \
         patch('code.data.ingest.fetch_themis_ey', return_value=themis_df):
        
        # Run the pipeline
        try:
            result = run_pipeline(
                start_date=TEST_DATE_START,
                end_date=TEST_DATE_END,
                output_dir=RESULTS_DIR
            )
        except Exception as e:
            pytest.fail(f"Pipeline execution failed: {str(e)}")

    # Verify output file exists
    assert os.path.exists(EXPECTED_OUTPUT_PATH), f"Output file not found at {EXPECTED_OUTPUT_PATH}"

    # Load and validate JSON structure
    with open(EXPECTED_OUTPUT_PATH, 'r') as f:
        output_data = json.load(f)

    # Check all required keys exist
    missing_keys = [key for key in EXPECTED_KEYS if key not in output_data]
    assert not missing_keys, f"Missing required keys in output: {missing_keys}"

    # Validate numeric values
    assert isinstance(output_data['pearson'], (int, float)), "Pearson coefficient must be numeric"
    assert isinstance(output_data['spearman'], (int, float)), "Spearman coefficient must be numeric"
    assert isinstance(output_data['p_val_permutation'], (int, float)), "P-value must be numeric"
    assert isinstance(output_data['significant_flag'], bool), "Significance flag must be boolean"
    
    # Validate ranges
    assert -1.0 <= output_data['pearson'] <= 1.0, "Pearson coefficient out of range [-1, 1]"
    assert -1.0 <= output_data['spearman'] <= 1.0, "Spearman coefficient out of range [-1, 1]"
    assert 0.0 <= output_data['p_val_permutation'] <= 1.0, "P-value out of range [0, 1]"
    
    # Validate optimal lag is within expected window
    optimal_lag = output_data['optimal_lag']
    assert LAG_WINDOW_MIN <= optimal_lag <= LAG_WINDOW_MAX, \
        f"Optimal lag {optimal_lag} outside expected window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}]"
    
    # Validate lag correlation value
    assert -1.0 <= output_data['lag_correlation_value'] <= 1.0, \
        "Lag correlation value out of range [-1, 1]"
    
    # Validate lag difference is non-negative
    assert output_data['lag_difference'] >= 0, "Lag difference must be non-negative"

    # Clean up test output
    if os.path.exists(EXPECTED_OUTPUT_PATH):
        os.remove(EXPECTED_OUTPUT_PATH)

    # If we reach here, the test passed
    assert True