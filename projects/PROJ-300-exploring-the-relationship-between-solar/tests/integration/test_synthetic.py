"""
Integration test for T037: Synthetic dataset validation for US-2 (Optimal Propagation Lag).

This test verifies that the pipeline correctly identifies a known lag (45 minutes)
in a synthetic dataset where Ey is generated from Vsw with a fixed 45-minute delay.
It satisfies the US-2 Independent Test requirement:
"Execute the lag-search on a known synthetic dataset where the true lag is min;
the pipeline must report 45 min (±1 min) as the optimal lag."

The test generates synthetic data with a known ground-truth lag, runs the full
lag-search pipeline, and asserts the detected optimal lag is within 1 minute of
the true lag.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from code.data.clean import clean_and_resample
from code.data.lag import apply_lag_shift, calculate_physics_lag
from code.analysis.correlation import calculate_correlation, circular_block_permutation
from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, EARTH_RADIUS_KM, TAIL_DISTANCE_RE


def create_synthetic_lagged_data(
    true_lag_minutes: int = 45,
    n_hours: int = 72,
    cadence_minutes: int = 5,
    noise_level: float = 0.1
):
    """
    Create a synthetic dataset with a known ground-truth lag between Vsw and Ey.

    Args:
        true_lag_minutes: The exact lag in minutes to embed in the data.
        n_hours: Total duration of the dataset in hours.
        cadence_minutes: Time resolution in minutes.
        noise_level: Standard deviation of Gaussian noise added to Ey.

    Returns:
        Tuple of (vsw_df, ey_df) with aligned timestamps.
    """
    n_samples = int((n_hours * 60) / cadence_minutes)
    timestamps = [datetime(2023, 6, 15) + timedelta(minutes=i * cadence_minutes) for i in range(n_samples)]

    # Generate Vsw: realistic solar wind speed with variation
    t = np.arange(n_samples)
    # Base speed ~450 km/s with sinusoidal variation and noise
    vsw = 450 + 150 * np.sin(2 * np.pi * t / (n_samples / 3)) + np.random.normal(0, 20, n_samples)
    vsw = np.clip(vsw, 300, 900)  # Physically realistic bounds

    # Generate Ey with true lag applied to Vsw
    # Ey is driven by Vsw with a delay (lag_steps corresponds to true_lag_minutes)
    lag_steps = int(true_lag_minutes / cadence_minutes)
    
    # Shift Vsw forward in time to create the lagged relationship
    # If Ey at time t depends on Vsw at time t - lag, we shift Vsw right
    vsw_shifted = np.roll(vsw, lag_steps)
    # The first 'lag_steps' values are now invalid (from the end due to roll)
    vsw_shifted[:lag_steps] = np.nan
    
    # Add noise to Ey
    ey = vsw_shifted + np.random.normal(0, noise_level * np.std(vsw), n_samples)

    vsw_df = pd.DataFrame({'timestamp': timestamps, 'Vsw': vsw})
    ey_df = pd.DataFrame({'timestamp': timestamps, 'Ey': ey})

    return vsw_df, ey_df


def test_synthetic_lag_45min():
    """
    US-2 Independent Test: Verify the pipeline identifies 45 min lag within ±1 min.

    Scenario:
    1. Create synthetic data with a known 45-minute lag between Vsw and Ey.
    2. Run the full pipeline (clean, resample, lag search).
    3. Verify the reported optimal lag is 45 ± 1 minutes.
    """
    # 1. Create synthetic data with known ground truth
    true_lag = 45  # minutes
    vsw_df, ey_df = create_synthetic_lagged_data(true_lag_minutes=true_lag)

    # 2. Clean and resample data (as per pipeline)
    vsw_clean, ey_clean = clean_and_resample(vsw_df, ey_df)

    assert len(vsw_clean) > 10, "Cleaned Vsw data should have sufficient samples"
    assert len(ey_clean) > 10, "Cleaned Ey data should have sufficient samples"
    assert not vsw_clean['Vsw'].isna().any(), "NaN values should be removed"
    assert not ey_clean['Ey'].isna().any(), "NaN values should be removed"

    # 3. Run lag search to find optimal lag
    optimal_lag, max_corr, lag_values, corr_values = find_optimal_lag(
        vsw_clean,
        ey_clean,
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )

    # 4. Verify the optimal lag is within tolerance of the true lag
    tolerance = 1  # minute
    assert abs(optimal_lag - true_lag) <= tolerance, (
        f"Optimal lag {optimal_lag} min is outside tolerance of true lag {true_lag} min. "
        f"Difference: {abs(optimal_lag - true_lag)} min"
    )

    # 5. Verify the correlation at optimal lag is strong (expected for synthetic data)
    assert abs(max_corr) > 0.5, (
        f"Correlation at optimal lag ({max_corr:.4f}) is unexpectedly weak. "
        "Check synthetic data generation or lag search logic."
    )

    # 6. Verify the lag search explored the expected window
    assert min_lag in lag_values or min(lag_values) <= min_lag, "Lag search should include window minimum"
    assert max_lag in lag_values or max(lag_values) >= max_lag, "Lag search should include window maximum"

    # 7. Log results for inspection
    print(f"\n=== Synthetic Lag Test Results ===")
    print(f"True Lag: {true_lag} min")
    print(f"Detected Optimal Lag: {optimal_lag} min")
    print(f"Difference: {abs(optimal_lag - true_lag)} min (tolerance: {tolerance} min)")
    print(f"Max Correlation: {max_corr:.4f}")
    print(f"Lag Search Range: {min(lag_values)} to {max(lag_values)} min")
    print(f"=== Test Passed ===\n")

    # 8. Return result dictionary for potential further inspection
    result = {
        'true_lag': true_lag,
        'detected_lag': optimal_lag,
        'difference': abs(optimal_lag - true_lag),
        'max_correlation': max_corr,
        'within_tolerance': abs(optimal_lag - true_lag) <= tolerance
    }

    assert result['within_tolerance'], "Detected lag not within tolerance"


def test_synthetic_lag_sensitivity_to_noise():
    """
    Verify the pipeline is robust to moderate noise levels.

    Tests that even with increased noise, the optimal lag remains close to the true lag.
    """
    true_lag = 45
    # Test with higher noise
    vsw_df, ey_df = create_synthetic_lagged_data(
        true_lag_minutes=true_lag,
        noise_level=0.3  # Higher noise
    )

    vsw_clean, ey_clean = clean_and_resample(vsw_df, ey_df)

    optimal_lag, max_corr, _, _ = find_optimal_lag(
        vsw_clean, ey_clean,
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )

    # Even with noise, we expect the lag to be detected within 5 minutes
    tolerance = 5
    assert abs(optimal_lag - true_lag) <= tolerance, (
        f"With high noise, optimal lag {optimal_lag} deviated too much from true lag {true_lag}"
    )


def test_synthetic_lag_boundary_conditions():
    """
    Test pipeline behavior when true lag is near the search window boundaries.
    """
    # Test with true lag near minimum
    true_lag_min = 30
    vsw_df, ey_df = create_synthetic_lagged_data(true_lag_minutes=true_lag_min)
    vsw_clean, ey_clean = clean_and_resample(vsw_df, ey_df)
    
    optimal_lag, _, _, _ = find_optimal_lag(
        vsw_clean, ey_clean,
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )
    
    assert abs(optimal_lag - true_lag_min) <= LAG_STEP, "Should detect lag near minimum"

    # Test with true lag near maximum
    true_lag_max = 90
    vsw_df, ey_df = create_synthetic_lagged_data(true_lag_minutes=true_lag_max)
    vsw_clean, ey_clean = clean_and_resample(vsw_df, ey_df)
    
    optimal_lag, _, _, _ = find_optimal_lag(
        vsw_clean, ey_clean,
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )
    
    assert abs(optimal_lag - true_lag_max) <= LAG_STEP, "Should detect lag near maximum"