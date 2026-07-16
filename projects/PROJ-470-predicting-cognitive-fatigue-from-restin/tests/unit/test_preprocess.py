"""
Unit test for bandpass filter attenuation.

Verifies that a 1-40 Hz bandpass filter attenuates 50 Hz line noise by > 20dB.
"""

import numpy as np
import mne
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import apply_bandpass_filter

def create_test_signal(length=1000, sfreq=256, noise_freq=50, noise_amp=1.0):
    """Create a synthetic signal with 50Hz noise for testing."""
    t = np.arange(length) / sfreq
    # Base signal (low frequency, 10Hz)
    signal = np.sin(2 * np.pi * 10 * t)
    # Add 50Hz noise
    noise = noise_amp * np.sin(2 * np.pi * noise_freq * t)
    return signal + noise, t

def test_bandpass_attenuation_50hz():
    """
    Test that the 1-40 Hz filter attenuates 50 Hz by > 20dB.
    
    20dB attenuation corresponds to a power ratio of 100 (amplitude ratio 10).
    """
    sfreq = 256
    length = sfreq * 10 # 10 seconds
    signal, t = create_test_signal(length, sfreq, noise_freq=50, noise_amp=1.0)
    
    # Create MNE Raw object
    info = mne.create_info(ch_names=['EEG'], sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal.reshape(1, -1), info)
    
    # Apply filter
    filtered_raw = apply_bandpass_filter(raw, l_freq=1.0, h_freq=40.0)
    filtered_data = filtered_raw.get_data()[0]
    
    # Analyze frequency content
    # We expect the 50Hz component to be significantly reduced.
    
    # FFT
    fft_signal = np.fft.rfft(signal)
    fft_filtered = np.fft.rfft(filtered_data)
    freqs = np.fft.rfftfreq(length, 1/sfreq)
    
    # Find index for 50Hz
    idx_50 = np.argmin(np.abs(freqs - 50))
    
    # Power at 50Hz (magnitude squared)
    power_before = np.abs(fft_signal[idx_50]) ** 2
    power_after = np.abs(fft_filtered[idx_50]) ** 2
    
    # Avoid division by zero
    if power_before == 0:
        pytest.skip("Input signal has no 50Hz component")
            
    # Attenuation in dB
    # dB = 10 * log10(P_after / P_before)
    # We want attenuation > 20dB, meaning P_after / P_before < 0.01
    # Or 20 * log10(After/Before) < -20
    
    if power_after == 0:
        attenuation_db = -np.inf
    else:
        attenuation_db = 10 * np.log10(power_after / power_before)
            
    logger_msg = f"Attenuation at 50Hz: {attenuation_db:.2f} dB"
    print(logger_msg)
    
    # Assert > 20dB attenuation (i.e., value < -20)
    assert attenuation_db < -20.0, f"Filter failed to attenuate 50Hz by >20dB. Got {attenuation_db:.2f} dB"

def test_bandpass_preserves_10hz():
    """Test that the filter preserves 10Hz signal."""
    sfreq = 256
    length = sfreq * 10
    t = np.arange(length) / sfreq
    signal = np.sin(2 * np.pi * 10 * t)
    
    info = mne.create_info(ch_names=['EEG'], sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(signal.reshape(1, -1), info)
    
    filtered_raw = apply_bandpass_filter(raw, l_freq=1.0, h_freq=40.0)
    filtered_data = filtered_raw.get_data()[0]
    
    # Correlation should be high
    corr = np.corrcoef(signal, filtered_data)[0, 1]
    assert corr > 0.9, "Filter distorted the 10Hz signal too much"