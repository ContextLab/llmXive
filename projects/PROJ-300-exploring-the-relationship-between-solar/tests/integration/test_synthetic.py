"""
Integration test for T026: US-2 Independent Test.
Verifies that the lag-search pipeline correctly identifies a known optimal lag (45 min)
on a synthetic dataset, within a tolerance of ±1 minute.

This test creates a controlled synthetic dataset where:
- Solar wind speed (Vsw) is a time series.
- Reconnection proxy (Ey) is a delayed copy of Vsw with a 45-minute lag + noise.
- The pipeline's `find_optimal_lag` function must recover ~45 minutes.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys

# Add project root to path if running from test directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

# Constants for synthetic generation
TRUE_LAG_MINUTES = 45
TOLERANCE_MINUTES = 1
SAMPLE_SIZE = 1000  # 5-minute steps -> ~83 hours
START_TIME = "2023-01-01"

def create_synthetic_lagged_dataset(lag_minutes: int, n_points: int = SAMPLE_SIZE) -> tuple:
    """
    Creates a synthetic dataset where Ey is Vsw shifted by `lag_minutes`.
    Returns (df_sw, df_ey) with columns ['timestamp', 'Vsw'] and ['timestamp', 'Ey'].
    """
    timestamps = pd.date_range(start=START_TIME, periods=n_points, freq='5min')
    
    # Generate Vsw as a noisy sine wave + trend to ensure correlation structure
    t = np.arange(n_points)
    vsw_base = 400 + 100 * np.sin(2 * np.pi * t / 200) + np.random.normal(0, 10, n_points)
    
    # Create Ey as Vsw shifted by the known lag + noise
    # We simulate the shift by aligning indices
    ey_base = np.roll(vsw_base, shift=lag_minutes // 5) 
    # Add some noise to Ey
    ey_noisy = ey_base + np.random.normal(0, 5, n_points)
    
    # Handle the rolled-in values at the start (set to NaN or repeat end)
    # For simplicity in this test, we just let them be the "wrapped" values or NaN
    # A cleaner way: generate longer and slice, but roll is sufficient for correlation peak detection
    
    df_sw = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw_base
    })
    df_ey = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey_noisy
    })
    
    return df_sw, df_ey

def test_synthetic_lag_45min():
    """
    US-2 Independent Test:
    Execute the lag-search on a synthetic dataset (true lag 45 min) and verify 
    the pipeline reports 45 min (±1 min).
    """
    # 1. Generate synthetic data with known lag
    df_sw, df_ey = create_synthetic_lagged_dataset(TRUE_LAG_MINUTES)
    
    # Ensure indices are aligned and set as index for lag functions
    df_sw.set_index('timestamp', inplace=True)
    df_ey.set_index('timestamp', inplace=True)
    
    # 2. Run the lag search
    # The function expects Series or DataFrames with time index
    result = find_optimal_lag(
        df_sw['Vsw'], 
        df_ey['Ey'], 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    
    reported_lag = result['optimal_lag']
    
    # 3. Verify the reported lag is within tolerance
    assert reported_lag is not None, "Optimal lag was not found."
    assert isinstance(reported_lag, (int, float)), f"Optimal lag must be numeric, got {type(reported_lag)}"
    
    diff = abs(reported_lag - TRUE_LAG_MINUTES)
    assert diff <= TOLERANCE_MINUTES, (
        f"Optimal lag {reported_lag} min differs from true lag {TRUE_LAG_MINUTES} min "
        f"by {diff} min (tolerance: {TOLERANCE_MINUTES} min)."
    )
    
    # 4. Log the result for verification artifacts
    results_dir = os.path.join(project_root, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    output_path = os.path.join(results_dir, 'us2_synthetic_lag_test.json')
    with open(output_path, 'w') as f:
        json.dump({
            'true_lag_minutes': TRUE_LAG_MINUTES,
            'reported_lag_minutes': reported_lag,
            'difference_minutes': diff,
            'tolerance_minutes': TOLERANCE_MINUTES,
            'passed': diff <= TOLERANCE_MINUTES,
            'lag_correlation_value': result.get('max_correlation'),
            'all_lag_correlations': result.get('lag_correlation_values', {})
        }, f, indent=2)
    
    print(f"Test passed. Reported lag: {reported_lag} min (True: {TRUE_LAG_MINUTES} min).")
    print(f"Results saved to: {output_path}")
    
    # Final assertion to ensure pytest marks it as passed
    assert diff <= TOLERANCE_MINUTES

if __name__ == '__main__':
    test_synthetic_lag_45min()