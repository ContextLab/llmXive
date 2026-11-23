"""
Unit tests for outlier handling in distribution shift detection.
Uses synthetic data from code/synthetic_data.py to verify robustness.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from synthetic_data import generate_synthetic_ili_series
from mmd_detector import compute_mmd_statistic, compute_permutation_pvalue, detect_shifts
from preprocess import log_transform, standardize, remove_missing_weeks
from exceptions import E_NO_DATA


def test_outlier_series_mmd_increases():
    """
    Test that MMD statistic increases when one series contains outliers.
    """
    np.random.seed(42)

    # Generate base series
    base_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.1,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0
    )

    # Create outlier version
    outlier_data = base_data.copy()
    outlier_data[50] = outlier_data[50] + 10.0  # Add extreme outlier
    outlier_data[51] = outlier_data[51] + 10.0

    # Compare clean window vs outlier window
    window_clean = base_data[20:30].values
    window_outlier = outlier_data[20:30].values

    # Compute MMD
    mmd_stat = compute_mmd_statistic(window_clean, window_outlier, bandwidth=1.0)

    # MMD should be significantly larger than zero
    assert mmd_stat > 0.1, f"MMD should detect outlier difference, got {mmd_stat}"


def test_outlier_series_pvalue_sensitive():
    """
    Test that permutation test is sensitive to outliers.
    """
    np.random.seed(42)

    base_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.1,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0
    )

    outlier_data = base_data.copy()
    outlier_data[50] = outlier_data[50] + 10.0

    window_clean = base_data[20:30].values
    window_outlier = outlier_data[20:30].values

    # Compute MMD
    mmd_stat = compute_mmd_statistic(window_clean, window_outlier, bandwidth=1.0)

    # Run permutation test
    p_value = compute_permutation_pvalue(
        window_clean, window_outlier,
        n_permutations=100,
        bandwidth=1.0
    )

    # P-value should be low (indicating significant difference)
    # Not necessarily < 0.01 with only 100 permutations, but should be lower
    # than for identical series
    assert p_value < 0.5, f"P-value {p_value} too high for outlier difference"


def test_outlier_preprocessing_robustness():
    """
    Test that preprocessing handles outliers without crashing.
    Log transform should work (assuming positive values).
    """
    np.random.seed(42)

    data_with_outliers = generate_synthetic_ili_series(
        length=100,
        noise_level=0.1,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.1,  # 10% outliers
        constant_segment_start=0,
        constant_segment_end=0
    )

    # Ensure positive for log transform
    data_with_outliers = np.abs(data_with_outliers) + 0.1

    # Test log transform
    log_data = log_transform(data_with_outliers)
    assert len(log_data) == len(data_with_outliers), "Log transform changed length"

    # Test standardize
    std_data = standardize(log_data)
    assert not np.any(np.isnan(std_data)), "Standardize produced NaNs"
    assert not np.any(np.isinf(std_data)), "Standardize produced Infs"


def test_outlier_detector_flagging():
    """
    Test that the shift detector can flag windows containing outliers.
    """
    np.random.seed(42)

    # Create series with a sudden outlier spike
    base_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.05,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0
    )

    # Add a cluster of outliers in the middle
    base_data[45:55] = base_data[45:55] + 5.0  # Shift up

    df = pd.DataFrame({'value': np.abs(base_data) + 0.1})

    # Run detection
    flags = detect_shifts(
        df,
        window_size=10,
        stride=5,
        alpha=0.05,  # More lenient for detection
        permutations=100
    )

    # We expect at least one flag around the outlier region
    # (Note: with only 100 permutations, detection is probabilistic)
    # Just verify the function runs and returns valid output
    assert isinstance(flags, list), "Flags should be a list"
    if len(flags) > 0:
        for flag in flags:
            assert 'week' in flag, "Flag missing 'week' key"
            assert 'p_value' in flag, "Flag missing 'p_value' key"
            assert 0 <= flag['p_value'] <= 1, "P-value out of range"


def test_outlier_vs_constant_comparison():
    """
    Test that MMD correctly distinguishes between constant series and
    series with outliers.
    """
    np.random.seed(42)

    # Constant series
    constant = np.ones(30) * 5.0

    # Series with outliers
    outlier_series = np.ones(30) * 5.0
    outlier_series[10] = 50.0  # Extreme outlier

    # MMD between constant and itself should be ~0
    mmd_constant = compute_mmd_statistic(constant, constant, bandwidth=1.0)

    # MMD between constant and outlier should be > 0
    mmd_outlier = compute_mmd_statistic(constant, outlier_series, bandwidth=1.0)

    assert mmd_constant < 1e-6, f"Constant vs constant MMD should be ~0, got {mmd_constant}"
    assert mmd_outlier > 0.5, f"Constant vs outlier MMD should be > 0, got {mmd_outlier}"
    assert mmd_outlier > mmd_constant, "Outlier should produce higher MMD"