import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation
from config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def create_synthetic_gap_dataset():
    """
    Creates a synthetic dataset with intentional NaN gaps to test the pipeline's
    robustness. Returns aligned DataFrames for Vsw (solar wind speed) and Ey (reconnection proxy).
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    n_points = 100
    freq = '5min'

    # Create time index
    timestamps = pd.date_range(start=base_time, periods=n_points, freq=freq)

    # Vsw: Solar wind speed (km/s) - introduce gaps
    vsw_values = np.random.uniform(350, 600, n_points)
    # Inject NaN gaps: remove data at indices 20-25 and 50-55
    vsw_values[20:26] = np.nan
    vsw_values[50:56] = np.nan

    df_vsw = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw_values
    })
    df_vsw.set_index('timestamp', inplace=True)

    # Ey: Reconnection rate proxy (mV/m) - introduce different gaps
    ey_values = np.random.uniform(-5, 5, n_points)
    # Inject NaN gaps: remove data at indices 10-15 and 70-75
    ey_values[10:16] = np.nan
    ey_values[70:76] = np.nan

    df_ey = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey_values
    })
    df_ey.set_index('timestamp', inplace=True)

    return df_vsw, df_ey

def test_us1_handles_nan_gaps():
    """
    US-1 Acceptance Scenario 2: Verify pipeline handles NaN gaps by cleaning,
    resampling, and producing correlation output without error.
    """
    # 1. Create synthetic data with gaps
    df_vsw, df_ey = create_synthetic_gap_dataset()

    # Verify gaps exist before cleaning
    assert df_vsw['Vsw'].isna().sum() > 0, "Test setup failed: No NaNs in Vsw"
    assert df_ey['Ey'].isna().sum() > 0, "Test setup failed: No NaNs in Ey"

    # 2. Clean and resample data
    # This should remove rows with any NaNs and resample to a fixed cadence
    clean_vsw, clean_ey = clean_and_resample(df_vsw, df_ey)

    # Verify cleaning worked
    assert clean_vsw['Vsw'].isna().sum() == 0, "Cleaning failed: NaNs remain in Vsw"
    assert clean_ey['Ey'].isna().sum() == 0, "Cleaning failed: NaNs remain in Ey"
    assert len(clean_vsw) == len(clean_ey), "Alignment failed: Lengths mismatch"
    assert len(clean_vsw) > 0, "Cleaning removed all data"

    # 3. Calculate physics-based lag (using mean Vsw)
    vsw_mean = clean_vsw['Vsw'].mean()
    # Ensure we have a valid mean
    assert vsw_mean > 0, "Invalid Vsw mean for lag calculation"

    lag_minutes = calculate_physics_lag(vsw_mean)
    assert lag_minutes > 0, "Physics lag must be positive"

    # 4. Apply lag shift
    # Shift Ey backwards in time by the calculated lag
    shifted_ey = apply_lag_shift(clean_ey, lag_minutes, 'Ey')

    # 5. Calculate correlations
    pearson_r, spearman_r = calculate_correlation(
        clean_vsw['Vsw'],
        shifted_ey['Ey']
    )

    # Verify correlation outputs are valid numbers
    assert isinstance(pearson_r, (int, float, np.number)), "Pearson r is not numeric"
    assert isinstance(spearman_r, (int, float, np.number)), "Spearman r is not numeric"
    assert -1.0 <= pearson_r <= 1.0, "Pearson r out of bounds"
    assert -1.0 <= spearman_r <= 1.0, "Spearman r out of bounds"

    # 6. Run permutation test for significance
    # Use a smaller number of iterations for faster testing
    p_value = circular_block_permutation(
        clean_vsw['Vsw'],
        shifted_ey['Ey'],
        iterations=100  # Reduced for unit test speed
    )

    assert isinstance(p_value, (int, float, np.number)), "P-value is not numeric"
    assert 0.0 <= p_value <= 1.0, "P-value out of bounds"

    # 7. Assert pipeline completed without raising exceptions
    # If we reach here, the test passes
    assert True

def test_us1_full_pipeline_with_gaps():
    """
    Integration test: Run the full US-1 pipeline logic on data with gaps.
    Verifies the entire flow from cleaning to correlation output.
    """
    # Create data with gaps
    df_vsw, df_ey = create_synthetic_gap_dataset()

    # Clean and resample
    clean_vsw, clean_ey = clean_and_resample(df_vsw, df_ey)

    # Calculate lag
    vsw_mean = clean_vsw['Vsw'].mean()
    lag_minutes = calculate_physics_lag(vsw_mean)

    # Apply lag
    shifted_ey = apply_lag_shift(clean_ey, lag_minutes, 'Ey')

    # Calculate correlations
    pearson_r, spearman_r = calculate_correlation(
        clean_vsw['Vsw'],
        shifted_ey['Ey']
    )

    # Permutation test
    p_value = circular_block_permutation(
        clean_vsw['Vsw'],
        shifted_ey['Ey'],
        iterations=100
    )

    # Determine significance
    significant_flag = p_value < 0.05

    # Build result dictionary (mimicking main.py output)
    result = {
        'pearson': float(pearson_r),
        'spearman': float(spearman_r),
        'p_val_permutation': float(p_value),
        'significant_flag': significant_flag,
        'optimal_lag': float(lag_minutes),
        'n_samples': len(clean_vsw)
    }

    # Verify all required keys are present
    required_keys = ['pearson', 'spearman', 'p_val_permutation', 'significant_flag']
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    # Verify types
    assert isinstance(result['pearson'], float)
    assert isinstance(result['significant_flag'], bool)

    # Verify no errors occurred during processing
    assert result['n_samples'] > 0, "No samples remained after cleaning"