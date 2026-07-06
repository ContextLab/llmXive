import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import logging

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import extract_mfn_features, calculate_angular_deviation

def test_angular_deviation_handles_zero_vectors():
    """Verify that calculate_angular_deviation logs a warning and returns None when input vectors are zero-length."""
    # Setup logging to capture warnings
    logging.basicConfig(level=logging.WARNING)
    
    # Test case 1: heading is zero vector
    heading = np.array([0.0, 0.0])
    optimal = np.array([1.0, 1.0])
    result = calculate_angular_deviation(heading, optimal)
    assert result is None

    # Test case 2: optimal is zero vector
    heading = np.array([1.0, 1.0])
    optimal = np.array([0.0, 0.0])
    result = calculate_angular_deviation(heading, optimal)
    assert result is None

    # Test case 3: both are zero vectors
    heading = np.array([0.0, 0.0])
    optimal = np.array([0.0, 0.0])
    result = calculate_angular_deviation(heading, optimal)
    assert result is None

    # Test with valid vectors (sanity check)
    heading = np.array([1.0, 0.0])
    optimal = np.array([0.0, 1.0])
    result = calculate_angular_deviation(heading, optimal)
    assert result is not None
    assert abs(result - 90.0) < 1e-6

def test_mfn_extraction_mean_vs_peak():
    """Verify that extract_mfn_features returns a mean_amplitude value that is the average of the window 
    and a peak_amplitude value that is the minimum, ensuring both are calculated correctly."""
    
    # Create synthetic data for one trial
    # 1000 Hz sampling rate, so 1 sample = 1 ms
    # Time from -200 to 800 ms
    times = np.arange(-200, 801)
    n_points = len(times)
    
    # Create a signal: baseline 0, event at 0, negative deflection (MFN)
    # We'll make a simple negative pulse from 200 to 400 ms
    signal = np.zeros(n_points)
    # Add a negative deflection in the 200-400ms window
    # Let's say -5 uV
    mean_window_indices = (times >= 200) & (times <= 400)
    signal[mean_window_indices] = -5.0
    
    # Create a DataFrame
    df = pd.DataFrame({
        'participant_id': ['P01'],
        'trial_id': ['T001'],
        'time_ms': times,
        'FCz': signal,
        'Cz': signal,
        'Fz': signal,
        'event_type': 'error'
    })
    
    # Extract features
    features = extract_mfn_features(df, sfreq=1000.0)
    
    assert not features.empty
    assert 'mean_amplitude' in features.columns
    assert 'peak_amplitude' in features.columns
    
    # Check mean amplitude
    # The mean window is 200-400ms, where signal is -5.0
    # Baseline is 0 (no baseline period in this synthetic data, so baseline mean is 0)
    # So mean_amplitude should be -5.0
    mean_amp = features[features['electrode'] == 'FCz']['mean_amplitude'].iloc[0]
    assert abs(mean_amp - (-5.0)) < 1e-6
    
    # Check peak amplitude
    # The minimum value in the epoch (-200 to 800) is -5.0
    peak_amp = features[features['electrode'] == 'FCz']['peak_amplitude'].iloc[0]
    assert abs(peak_amp - (-5.0)) < 1e-6

def test_mfn_extraction_baseline_correction():
    """Verify that baseline correction is applied correctly."""
    # Create synthetic data with a non-zero baseline
    times = np.arange(-200, 801)
    n_points = len(times)
    
    # Baseline period (-200 to 0) has value 10.0
    # Event period (0 to 800) has value 5.0
    # MFN window (200-400) should be 5.0 - 10.0 = -5.0 after correction
    signal = np.ones(n_points) * 10.0
    signal[times >= 0] = 5.0
    
    df = pd.DataFrame({
        'participant_id': ['P01'],
        'trial_id': ['T001'],
        'time_ms': times,
        'FCz': signal,
        'Cz': signal,
        'Fz': signal,
        'event_type': 'error'
    })
    
    features = extract_mfn_features(df, sfreq=1000.0)
    
    # Baseline mean should be 10.0
    # MFN window mean (200-400) is 5.0
    # Corrected mean should be 5.0 - 10.0 = -5.0
    mean_amp = features[features['electrode'] == 'FCz']['mean_amplitude'].iloc[0]
    assert abs(mean_amp - (-5.0)) < 1e-6

def test_mfn_extraction_multiple_electrodes():
    """Verify that features are extracted for all target electrodes."""
    times = np.arange(-200, 801)
    n_points = len(times)
    
    signal = np.zeros(n_points)
    signal[(times >= 200) & (times <= 400)] = -5.0
    
    df = pd.DataFrame({
        'participant_id': ['P01'],
        'trial_id': ['T001'],
        'time_ms': times,
        'FCz': signal,
        'Cz': signal,
        'Fz': signal,
        'event_type': 'error'
    })
    
    features = extract_mfn_features(df, sfreq=1000.0)
    
    electrodes = features['electrode'].unique()
    assert 'FCz' in electrodes
    assert 'Cz' in electrodes
    assert 'Fz' in electrodes
    assert len(electrodes) == 3

def test_mfn_extraction_no_error_events():
    """Verify that an empty DataFrame is returned if no error events are found."""
    times = np.arange(-200, 801)
    n_points = len(times)
    
    signal = np.zeros(n_points)
    
    df = pd.DataFrame({
        'participant_id': ['P01'],
        'trial_id': ['T001'],
        'time_ms': times,
        'FCz': signal,
        'Cz': signal,
        'Fz': signal,
        'event_type': 'correct'  # Not an error
    })
    
    features = extract_mfn_features(df, sfreq=1000.0)
    assert features.empty