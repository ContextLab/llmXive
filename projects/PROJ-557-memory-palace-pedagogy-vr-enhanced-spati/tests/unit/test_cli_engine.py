"""
Unit tests for CLI z-score calculation and 0.5 SD thresholding.

This module validates the core logic of the Cognitive Load Index (CLI) engine,
specifically focusing on the computation of moving average z-scores and the
identification of high-load windows based on the 0.5 standard deviation threshold.

These tests assume that T005 (Data Model) and T005b (Luminance Algorithm) are complete.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the project root to the path to allow imports from 'code'
# In a real execution environment, this is handled by PYTHONPATH or setup.py
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_cli_threshold, get_outlier_threshold
from code.cli_engine import compute_moving_average_zscore, identify_high_load_windows

# Fixtures for test data
@pytest.fixture
def sample_pupil_data():
    """
    Generates a synthetic time-series of pupil diameter data.
    Includes a baseline period, a high-load spike, and a return to baseline.
    """
    n = 1000
    time = np.linspace(0, 100, n)
    
    # Baseline: mean ~ 3.5mm, std ~ 0.1mm
    baseline = 3.5 + np.random.normal(0, 0.1, n)
    
    # Inject a high-load event at the middle (indices 400-600)
    # Simulate a dilation of ~0.5mm above baseline
    load_event = np.zeros(n)
    load_event[400:600] = 0.5
    
    data = baseline + load_event
    
    df = pd.DataFrame({
        'timestamp': time,
        'pupil_diameter': data
    })
    return df

@pytest.fixture
def window_size():
    return 50  # 50 samples for moving average window

@pytest.fixture
def threshold_sd():
    """Standard threshold for high-load identification (0.5 SD)"""
    return 0.5

def test_compute_moving_average_zscore_basic(sample_pupil_data, window_size):
    """
    Test that compute_moving_average_zscore returns a DataFrame with
    expected columns and correct shape relative to input.
    """
    result = compute_moving_average_zscore(
        sample_pupil_data, 
        window_size=window_size
    )
    
    assert isinstance(result, pd.DataFrame)
    assert 'timestamp' in result.columns
    assert 'pupil_diameter' in result.columns
    assert 'ma_pupil' in result.columns
    assert 'z_score' in result.columns
    
    # The first (window_size - 1) rows might be NaN depending on implementation,
    # but the total length should match input
    assert len(result) == len(sample_pupil_data)

def test_compute_moving_average_zscore_values(sample_pupil_data, window_size):
    """
    Verify that z-scores are centered around 0 for baseline periods
    and spike positively during the injected high-load event.
    """
    result = compute_moving_average_zscore(
        sample_pupil_data, 
        window_size=window_size
    )
    
    # Check baseline period (first 200 samples, well before the event)
    baseline_z = result['z_score'].iloc[:200].dropna()
    assert len(baseline_z) > 0
    assert np.abs(baseline_z.mean()) < 0.5  # Should be close to 0
    
    # Check high-load period (indices 400-600)
    # We expect a significant positive shift
    load_z = result['z_score'].iloc[400:600].dropna()
    assert len(load_z) > 0
    # Since we injected a 0.5mm shift and baseline std is 0.1mm,
    # we expect a z-score around 5.0 (0.5 / 0.1)
    assert load_z.mean() > 2.0 

def test_identify_high_load_windows_threshold(sample_pupil_data, window_size, threshold_sd):
    """
    Test that identify_high_load_windows correctly flags windows
    exceeding the 0.5 SD threshold.
    """
    z_scores = compute_moving_average_zscore(sample_pupil_data, window_size=window_size)
    high_load = identify_high_load_windows(z_scores, threshold_sd=threshold_sd)
    
    assert isinstance(high_load, pd.DataFrame)
    assert 'is_high_load' in high_load.columns
    
    # Verify boolean type
    assert high_load['is_high_load'].dtype == bool

def test_identify_high_load_windows_detection(sample_pupil_data, window_size, threshold_sd):
    """
    Verify that the high-load event injected in the data is correctly detected.
    The event is between indices 400 and 600.
    """
    z_scores = compute_moving_average_zscore(sample_pupil_data, window_size=window_size)
    high_load = identify_high_load_windows(z_scores, threshold_sd=threshold_sd)
    
    # We expect a contiguous block of True values around the event
    # The event starts at 400. Due to moving average lag, detection might start slightly later.
    # We check the range 400 to 600.
    event_mask = high_load['is_high_load'].iloc[400:600]
    true_count = event_mask.sum()
    
    # We expect a significant portion of this window to be flagged as high load
    # Given the strong signal (5 SD vs 0.5 SD threshold), most should be True
    assert true_count > (len(event_mask) * 0.8), "Expected high load detection in the injected event region."

def test_identify_high_load_windows_baseline_false(sample_pupil_data, window_size, threshold_sd):
    """
    Verify that baseline periods are NOT flagged as high load.
    """
    z_scores = compute_moving_average_zscore(sample_pupil_data, window_size=window_size)
    high_load = identify_high_load_windows(z_scores, threshold_sd=threshold_sd)
    
    # Check a safe baseline region (indices 0 to 200)
    baseline_mask = high_load['is_high_load'].iloc[:200]
    true_count = baseline_mask.sum()
    
    # Should be very few or no false positives in the baseline
    assert true_count == 0 or true_count < 2, "Expected no high load flags in baseline period."

def test_threshold_config_consistency():
    """
    Ensure that the default threshold used in tests matches the global config.
    """
    config_threshold = get_cli_threshold()
    # The task spec defines 0.5 SD as the threshold
    assert config_threshold == 0.5, f"Config threshold {config_threshold} does not match expected 0.5 SD"

def test_edge_case_constant_signal():
    """
    Test behavior when input signal is constant (std = 0).
    Z-score calculation should handle division by zero gracefully (likely resulting in NaN or 0).
    """
    df = pd.DataFrame({
        'timestamp': np.arange(100),
        'pupil_diameter': np.ones(100) * 3.5
    })
    
    # This should not raise a ZeroDivisionError
    try:
        result = compute_moving_average_zscore(df, window_size=10)
        # Z-scores should be NaN or 0 if handled
        assert 'z_score' in result.columns
    except Exception as e:
        pytest.fail(f"compute_moving_average_zscore raised an exception on constant signal: {e}")

def test_edge_case_short_signal():
    """
    Test behavior when input signal is shorter than window size.
    """
    df = pd.DataFrame({
        'timestamp': np.arange(5),
        'pupil_diameter': np.random.normal(3.5, 0.1, 5)
    })
    
    result = compute_moving_average_zscore(df, window_size=10)
    # Should return DataFrame, likely with NaN z-scores
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5