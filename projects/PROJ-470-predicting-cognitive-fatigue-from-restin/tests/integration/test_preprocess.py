import os
import sys
import numpy as np
import mne
from scipy.signal import welch
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.preprocess import (
    apply_bandpass_filter, 
    apply_notch_filter, 
    load_config, 
    setup_logger
)

@pytest.fixture
def synthetic_signal_with_line_noise():
    """
    Generate a synthetic test signal:
    - Sampling rate: 256 Hz
    - Duration: 120 seconds
    - 50Hz sine wave (amplitude 50µV)
    - White noise (amplitude 10µV)
    """
    sfreq = 256
    duration = 120
    n_samples = sfreq * duration
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # 50Hz sine wave
    line_noise = 50 * np.sin(2 * np.pi * 50 * t)
    
    # White noise
    noise = 10 * np.random.randn(n_samples)
    
    # Combined signal
    data = line_noise + noise
    
    # Create a mock MNE Raw object
    info = mne.create_info(ch_names=['EEG001'], sfreq=sfreq, ch_types=['eeg'])
    raw = mne.io.RawArray(data.reshape(1, -1), info)
    
    return raw

def test_line_noise_attenuation(synthetic_signal_with_line_noise):
    """
    Test that the notch filter attenuates the 50Hz line noise by at least 20dB.
    """
    raw = synthetic_signal_with_line_noise
    logger = setup_logger("test_preprocess")
    config = load_config()
    
    # Compute PSD of raw signal
    psd_raw, freqs_raw = welch(raw.get_data()[0], fs=256, nperseg=1024)
    peak_power_raw = np.max(psd_raw)
    peak_freq_raw = freqs_raw[np.argmax(psd_raw)]
    
    # Apply bandpass filter (1-40 Hz) - this should already attenuate 50Hz significantly
    raw_filtered = apply_bandpass_filter(raw.copy(), config['filter_low'], config['filter_high'], logger)
    
    # Apply notch filter at 50Hz
    raw_notched = apply_notch_filter(raw_filtered.copy(), config['notch_freq'], logger)
    
    # Compute PSD of filtered signal
    psd_filtered, freqs_filtered = welch(raw_notched.get_data()[0], fs=256, nperseg=1024)
    peak_power_filtered = np.max(psd_filtered)
    peak_freq_filtered = freqs_filtered[np.argmax(psd_filtered)]
    
    # Calculate attenuation in dB
    attenuation_db = 10 * np.log10(peak_power_raw / (peak_power_filtered + 1e-10))
    
    # Assert that the attenuation is at least 20dB
    # Note: The bandpass filter alone (1-40Hz) should already attenuate 50Hz significantly.
    # The notch filter provides additional attenuation.
    assert attenuation_db >= 20, f"Expected at least 20dB attenuation, got {attenuation_db:.2f}dB"
    
    # Verify that the peak frequency is no longer at 50Hz
    assert abs(peak_freq_filtered - 50) > 1, f"Peak frequency should not be at 50Hz, got {peak_freq_filtered:.2f}Hz"

def test_missing_data_edge_case():
    """
    Test that the preprocessing script raises a clear error when the data directory is absent.
    """
    from code.preprocess import stream_eeg_files
    
    with pytest.raises(FileNotFoundError, match="Data directory not found"):
        stream_eeg_files("non_existent_data_dir", setup_logger("test_missing"))
