"""
Integration tests for preprocessing pipeline.
Tests line noise attenuation and real data processing.
"""
import os
import sys
import numpy as np
import mne
import pytest
from scipy.signal import welch
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import (
    load_config, 
    apply_bandpass_filter, 
    apply_notch_filter, 
    process_eeg_stream,
    save_processed_data
)

@pytest.fixture
def synthetic_signal():
    """Generate a synthetic signal with 50Hz line noise."""
    sfreq = 256  # Sampling rate
    duration = 10  # seconds
    t = np.linspace(0, duration, int(sfreq * duration), endpoint=False)
    
    # Base signal: low frequency sine wave (10 Hz)
    base_signal = np.sin(2 * np.pi * 10 * t)
    
    # Add 50Hz line noise
    line_noise = 0.5 * np.sin(2 * np.pi * 50 * t)
    
    # Add white noise
    noise = 0.1 * np.random.randn(len(t))
    
    # Combined signal
    data = base_signal + line_noise + noise
    
    # Create info structure
    info = mne.create_info(ch_names=['EEG001'], sfreq=sfreq, ch_types='eeg')
    
    # Create raw object
    raw = mne.io.RawArray(data.reshape(1, -1), info)
    
    return raw, 50  # Return signal and expected notch frequency

def test_line_noise_attenuation(synthetic_signal):
    """Test that notch filter attenuates 50Hz line noise by >20dB."""
    raw, notch_freq = synthetic_signal
    
    # Compute PSD of raw signal
    freqs_raw, psd_raw = welch(raw.get_data(), fs=raw.info['sfreq'], nperseg=1024)
    peak_idx_raw = np.argmax(psd_raw[0, :])
    peak_power_raw = psd_raw[0, peak_idx_raw]
    
    # Apply notch filter
    raw_filtered = raw.copy()
    raw_filtered.notch_filter(notch_freq, method='iir')
    
    # Compute PSD of filtered signal
    freqs_filt, psd_filt = welch(raw_filtered.get_data(), fs=raw_filtered.info['sfreq'], nperseg=1024)
    peak_idx_filt = np.argmax(psd_filt[0, :])
    peak_power_filt = psd_filt[0, peak_idx_filt]
    
    # Calculate attenuation in dB
    attenuation_db = 10 * np.log10(peak_power_raw / (peak_power_filt + 1e-10))
    
    # Assert attenuation > 20dB
    assert attenuation_db > 20, f"Line noise attenuation ({attenuation_db:.2f}dB) is less than 20dB"

def test_config_notch_frequency():
    """Test that notch frequency is read from config."""
    config = load_config()
    assert 'notch_freq' in config, "notch_freq not found in config"
    assert config['notch_freq'] == 50, f"Expected notch_freq=50, got {config['notch_freq']}"

def test_real_data_integration():
    """Test preprocessing on real data if available."""
    cleaned_eeg_path = Path("data/processed/cleaned_eeg.fif")
    
    if not cleaned_eeg_path.exists():
        pytest.skip("Input file data/processed/cleaned_eeg.fif not found. Ensure T010 completed successfully.")
    
    # Load real data
    raw = mne.io.read_raw_fif(cleaned_eeg_path, preload=True)
    
    # Compute PSD
    freqs, psd = welch(raw.get_data(), fs=raw.info['sfreq'], nperseg=1024)
    
    # Check that 50Hz peak is attenuated (should be lower than surrounding frequencies)
    # This is a simple check; in practice, we'd compare with raw unfiltered data
    idx_50hz = np.argmin(np.abs(freqs - 50))
    idx_45hz = np.argmin(np.abs(freqs - 45))
    idx_55hz = np.argmin(np.abs(freqs - 55))
    
    # The power at 50Hz should be lower than at 45Hz and 55Hz if notch filter worked
    assert psd[0, idx_50hz] < psd[0, idx_45hz], "50Hz power not attenuated compared to 45Hz"
    assert psd[0, idx_50hz] < psd[0, idx_55hz], "50Hz power not attenuated compared to 55Hz"
