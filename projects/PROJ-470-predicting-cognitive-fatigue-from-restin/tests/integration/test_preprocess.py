import pytest
import os
import numpy as np
import mne
from pathlib import Path
import tempfile
import shutil
from code.preprocess import load_config, apply_bandpass_filter, apply_notch_filter, process_eeg_stream, save_processed_data

def create_test_raw_data(n_channels=10, n_times=256*60, sfreq=256):
    """Create synthetic raw EEG data with line noise."""
    info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], sfreq=sfreq, ch_types='eeg')
    data = np.random.randn(n_channels, n_times)
    
    # Add 50Hz line noise
    t = np.arange(n_times) / sfreq
    line_noise = 0.5 * np.sin(2 * np.pi * 50 * t)
    data += line_noise[np.newaxis, :]
    
    raw = mne.io.RawArray(data, info)
    return raw

def test_bandpass_attenuation():
    """Test that bandpass filter attenuates frequencies outside 1-40 Hz."""
    raw = create_test_raw_data()
    filtered = apply_bandpass_filter(raw, 1, 40)
    
    # Compute PSD before and after
    psd_raw, freqs_raw = mne.time_frequency.psd_welch(raw, fmin=0, fmax=100)
    psd_filtered, freqs_filtered = mne.time_frequency.psd_welch(filtered, fmin=0, fmax=100)
    
    # Check attenuation at 0.5 Hz (below bandpass)
    idx_low = np.argmin(np.abs(freqs_raw - 0.5))
    attenuation_low = psd_raw.mean(axis=0)[idx_low] - psd_filtered.mean(axis=0)[idx_low]
    
    # Check attenuation at 45 Hz (above bandpass)
    idx_high = np.argmin(np.abs(freqs_raw - 45))
    attenuation_high = psd_raw.mean(axis=0)[idx_high] - psd_filtered.mean(axis=0)[idx_high]
    
    assert attenuation_low > 10, f"Low frequency attenuation insufficient: {attenuation_low} dB"
    assert attenuation_high > 10, f"High frequency attenuation insufficient: {attenuation_high} dB"

def test_line_noise_attenuation():
    """Test that notch filter attenuates line noise by >20dB."""
    raw = create_test_raw_data()
    
    # Compute PSD before notch
    psd_raw, freqs_raw = mne.time_frequency.psd_welch(raw, fmin=40, fmax=60)
    peak_idx_raw = np.argmax(psd_raw.mean(axis=0))
    peak_freq_raw = freqs_raw[peak_idx_raw]
    peak_power_raw = psd_raw.mean(axis=0)[peak_idx_raw]
    
    # Apply notch filter
    config = load_config()
    notch_freq = config.get('notch_freq', 50)
    filtered = apply_notch_filter(raw, notch_freq)
    
    # Compute PSD after notch
    psd_filtered, freqs_filtered = mne.time_frequency.psd_welch(filtered, fmin=40, fmax=60)
    peak_idx_filtered = np.argmax(psd_filtered.mean(axis=0))
    peak_freq_filtered = freqs_filtered[peak_idx_filtered]
    peak_power_filtered = psd_filtered.mean(axis=0)[peak_idx_filtered]
    
    # Calculate attenuation in dB
    attenuation = 10 * np.log10(peak_power_raw / (peak_power_filtered + 1e-10))
    
    assert attenuation > 20, f"Line noise attenuation insufficient: {attenuation} dB"

def test_preprocess_stream():
    """Test full preprocessing stream with synthetic data."""
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    raw_dir = os.path.join(temp_dir, "raw")
    os.makedirs(raw_dir)
    
    try:
        # Create test raw data files
        for i in range(5):
            raw = create_test_raw_data()
            file_path = os.path.join(raw_dir, f"sub-{i:02d}_eeg.fif")
            raw.save(file_path, overwrite=True)
        
        # Run preprocessing
        config = load_config()
        config['min_duration'] = 60  # Shorter for test
        cleaned_data, exclusion_log = process_eeg_stream(raw_dir, config, temp_dir)
        
        # Check outputs
        assert len(cleaned_data) > 0, "No cleaned data produced"
        assert os.path.exists(os.path.join(temp_dir, "cleaned_eeg.fif")), "Output file not created"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
