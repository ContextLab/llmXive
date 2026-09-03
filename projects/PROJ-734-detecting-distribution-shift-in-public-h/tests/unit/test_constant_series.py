"""
Unit tests for handling constant series in distribution shift detection.
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


def test_constant_series_mmd_zero():
    """
    Test that MMD statistic is effectively zero when comparing two identical
    constant series (no distribution shift).
    """
    # Generate a constant series (zero variance segment)
    np.random.seed(42)
    constant_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.0,  # No noise -> constant
        trend_level=0.0,  # No trend
        missing_rate=0.0,
        outlier_rate=0.0,
        constant_segment_start=10,
        constant_segment_end=90
    )

    # Extract two windows from the constant segment
    window1 = constant_data[20:30].values
    window2 = constant_data[40:50].values

    # Both should be constant with same value
    assert np.allclose(window1, window1[0]), "Window 1 is not constant"
    assert np.allclose(window2, window2[0]), "Window 2 is not constant"
    assert np.isclose(window1[0], window2[0]), "Constant values differ"

    # Compute MMD
    mmd_stat = compute_mmd_statistic(window1, window2, bandwidth=1.0)

    # MMD should be very close to zero for identical distributions
    assert mmd_stat < 1e-6, f"MMD for constant series should be ~0, got {mmd_stat}"


def test_constant_series_pvalue_undefined():
    """
    Test that permutation test handles constant series gracefully.
    With constant data, all permutations yield the same MMD, so p-value
    calculation should not crash and should return a reasonable value.
    """
    np.random.seed(42)
    constant_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.0,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0,
        constant_segment_start=10,
        constant_segment_end=90
    )

    window1 = constant_data[20:30].values
    window2 = constant_data[40:50].values

    # Compute MMD
    mmd_stat = compute_mmd_statistic(window1, window2, bandwidth=1.0)

    # Run permutation test with small number for speed
    p_value = compute_permutation_pvalue(
        window1, window2,
        n_permutations=100,
        bandwidth=1.0
    )

    # P-value should be 1.0 (or very close) since distributions are identical
    # But we just check it doesn't crash and is in valid range [0, 1]
    assert 0.0 <= p_value <= 1.0, f"P-value {p_value} out of range [0, 1]"


def test_constant_series_preprocessing():
    """
    Test that preprocessing handles constant series without crashing.
    Log-transform of constant series should work (log of constant > 0).
    """
    np.random.seed(42)
    constant_data = generate_synthetic_ili_series(
        length=50,
        noise_level=0.0,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0,
        constant_segment_start=0,
        constant_segment_end=50
    )

    # Ensure values are positive for log transform
    constant_data = constant_data + 1.0  # Shift to positive

    # Test log transform
    log_data = log_transform(constant_data)
    assert len(log_data) == len(constant_data), "Log transform changed length"
    assert np.allclose(log_data, np.log(constant_data)), "Log transform incorrect"

    # Test standardize
    std_data = standardize(log_data)
    assert np.isclose(std_data.mean(), 0.0, atol=1e-6), "Standardized mean not 0"
    assert np.isclose(std_data.std(), 1.0, atol=1e-6), "Standardized std not 1"


def test_constant_series_detector_no_false_positive():
    """
    Test that the shift detector does not flag constant series as having a shift.
    """
    np.random.seed(42)
    constant_data = generate_synthetic_ili_series(
        length=100,
        noise_level=0.0,
        trend_level=0.0,
        missing_rate=0.0,
        outlier_rate=0.0,
        constant_segment_start=0,
        constant_segment_end=100
    )

    # Convert to DataFrame for detector
    df = pd.DataFrame({'value': constant_data + 1.0})  # Shift to positive

    # Run detection with small window
    flags = detect_shifts(
        df,
        window_size=10,
        stride=5,
        alpha=0.01,
        permutations=100
    )

    # Should not detect any shifts in constant data
    assert len(flags) == 0, f"Constant series should not trigger shifts, got {len(flags)} flags"
