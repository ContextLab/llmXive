import os
import sys
import pytest
import numpy as np
import mne
from pathlib import Path
import tempfile
import shutil
import pandas as pd
from datetime import datetime

# Add parent directory to path to import preprocess
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import (
    apply_bandpass_filter, 
    detect_line_noise_peak, 
    apply_notch_filter, 
    process_eeg_stream, 
    load_config,
    main
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with synthetic EEG data for testing."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "raw"
    raw_dir.mkdir()
    
    # Create a synthetic EEG signal with 50Hz noise
    sfreq = 250  # Hz
    duration = 10  # seconds
    n_channels = 2
    n_samples = sfreq * duration
    times = np.linspace(0, duration, n_samples, endpoint=False)
    
    # Clean signal (sine at 10Hz)
    clean_signal = np.sin(2 * np.pi * 10 * times)
    
    # Add 50Hz noise
    noise = 0.5 * np.sin(2 * np.pi * 50 * times)
    signal = clean_signal + noise + 0.1 * np.random.randn(n_samples)
    
    # Create info structure
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002'], sfreq=sfreq, ch_types='eeg')
    
    # Create raw object (2 channels, same signal for simplicity)
    data = np.vstack([signal, signal])
    raw = mne.io.RawArray(data, info)
    
    # Save as EDF
    file_path = raw_dir / "sub-001_raw.edf"
    raw.save(file_path, overwrite=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_bandpass_attenuation(temp_data_dir):
    """Test that the bandpass filter attenuates frequencies outside the passband."""
    raw_dir = Path(temp_data_dir) / "raw"
    output_dir = Path(temp_data_dir) / "processed"
    log_dir = Path(temp_data_dir) / "logs"
    
    # Load config (mock)
    config = {
        'filter_low': 1,
        'filter_high': 40,
        'artifact_threshold': 100e-6,
        'min_duration': 2
    }
    
    # Process
    process_eeg_stream(str(raw_dir), config, str(output_dir), str(log_dir))
    
    # Load result
    result_file = output_dir / "cleaned_eeg.fif"
    if not result_file.exists():
        # Fallback if single file logic didn't trigger (e.g. multiple files)
        result_file = list(output_dir.glob("cleaned_*.fif"))[0]
    
    raw_result = mne.io.read_raw_fif(result_file, preload=True)
    
    # Compute PSD
    psd, freqs = mne.time_frequency.psd_welch(raw_result, fmin=1, fmax=100, n_fft=2048)
    
    # Check attenuation of 50Hz (should be reduced by bandpass if it was the only filter, 
    # but here we also have notch. The bandpass 1-40 should attenuate 50Hz significantly).
    # 50Hz is outside 1-40, so it should be very low.
    idx_50 = np.argmin(np.abs(freqs - 50))
    power_50 = psd[0, idx_50]
    
    # Check power in passband (10Hz)
    idx_10 = np.argmin(np.abs(freqs - 10))
    power_10 = psd[0, idx_10]
    
    # The 50Hz power should be significantly lower than 10Hz power
    # This is a relative check.
    assert power_50 < power_10, "50Hz power should be lower than 10Hz power after bandpass"
    print(f"Bandpass test passed. 10Hz power: {power_10}, 50Hz power: {power_50}")

def test_line_noise_attenuation(temp_data_dir):
    """
    Integration test for line noise attenuation.
    Verifies that if a 50Hz peak is present, it is attenuated by >20dB.
    """
    raw_dir = Path(temp_data_dir) / "raw"
    output_dir = Path(temp_data_dir) / "processed"
    log_dir = Path(temp_data_dir) / "logs"
    
    # Load original raw for comparison
    original_file = raw_dir / "sub-001_raw.edf"
    raw_orig = mne.io.read_raw_edf(original_file, preload=True)
    
    # Compute PSD of original
    psd_orig, freqs_orig = mne.time_frequency.psd_welch(raw_orig, fmin=1, fmax=100, n_fft=2048)
    
    # Get power at 50Hz
    idx_50 = np.argmin(np.abs(freqs_orig - 50))
    power_50_orig = psd_orig[0, idx_50]
    
    # Process
    config = {
        'filter_low': 1,
        'filter_high': 40,
        'artifact_threshold': 100e-6,
        'min_duration': 2
    }
    
    process_eeg_stream(str(raw_dir), config, str(output_dir), str(log_dir))
    
    # Load result
    result_files = list(output_dir.glob("cleaned_*.fif"))
    if not result_files:
        pytest.fail("No processed files found")
    
    result_file = result_files[0]
    raw_res = mne.io.read_raw_fif(result_file, preload=True)
    
    # Compute PSD of result
    psd_res, freqs_res = mne.time_frequency.psd_welch(raw_res, fmin=1, fmax=100, n_fft=2048)
    
    # Get power at 50Hz
    idx_50_res = np.argmin(np.abs(freqs_res - 50))
    power_50_res = psd_res[0, idx_50_res]
    
    # Calculate attenuation in dB
    if power_50_orig > 0 and power_50_res > 0:
        attenuation_db = 10 * np.log10(power_50_orig / power_50_res)
    else:
        # If result is 0 or near 0, attenuation is huge
        attenuation_db = 100 # Assume max attenuation
    
    print(f"Attenuation at 50Hz: {attenuation_db:.2f} dB")
    
    # Assert attenuation > 20dB
    # Note: The bandpass 1-40 alone might not give 20dB at 50Hz depending on filter order.
    # The notch filter should ensure this.
    # If the peak was detected and notch applied, it should be attenuated.
    # If not detected (unlikely with our synthetic data), we might fail.
    # But our synthetic data has strong 50Hz, so it should be detected.
    assert attenuation_db > 20, f"Line noise attenuation ({attenuation_db:.2f} dB) must be > 20 dB"

def test_output_file_exists_and_participants(temp_data_dir):
    """Assert file exists and contains data for >= 30 participants (simulated)."""
    # This test is tricky because our temp_data_dir only has 1 participant.
    # In a real run with 30+ participants, this would pass.
    # For this unit/integration test, we verify the logic works for the available data.
    # We will modify the temp_data_dir to have 30 files to satisfy the requirement.
    
    raw_dir = Path(temp_data_dir) / "raw"
    output_dir = Path(temp_data_dir) / "processed"
    log_dir = Path(temp_data_dir) / "logs"
    
    # Generate 30 synthetic participants
    sfreq = 250
    duration = 5
    n_samples = sfreq * duration
    times = np.linspace(0, duration, n_samples, endpoint=False)
    
    for i in range(30):
        # Create signal with 50Hz noise
        clean = np.sin(2 * np.pi * 10 * times)
        noise = 0.5 * np.sin(2 * np.pi * 50 * times)
        signal = clean + noise + 0.1 * np.random.randn(n_samples)
        
        info = mne.create_info(ch_names=['EEG 001'], sfreq=sfreq, ch_types='eeg')
        data = np.vstack([signal])
        raw = mne.io.RawArray(data, info)
        
        file_path = raw_dir / f"sub-{i:03d}_raw.edf"
        raw.save(file_path, overwrite=True)
    
    # Process
    config = {
        'filter_low': 1,
        'filter_high': 40,
        'artifact_threshold': 100e-6,
        'min_duration': 2
    }
    
    count = process_eeg_stream(str(raw_dir), config, str(output_dir), str(log_dir))
    
    # Check output file
    result_file = output_dir / "cleaned_eeg.fif"
    assert result_file.exists(), "cleaned_eeg.fif must exist"
    
    # Check participant count in the file (if concatenated)
    # Or check that 30 files were processed
    processed_files = list(output_dir.glob("cleaned_*.fif"))
    # If concatenated, we have 1 file. If not, we have 30.
    # The code concatenates if > 1.
    if len(processed_files) == 1:
        raw_combined = mne.io.read_raw_fif(result_file, preload=True)
        # We can't easily count participants from a concatenated FIF without metadata.
        # But we know we processed 30 files.
        assert count == 30, f"Expected 30 processed participants, got {count}"
    else:
        # If not concatenated (logic change?), check count
        assert len(processed_files) >= 30, "Must have processed >= 30 participants"
    
    print(f"Test passed: {count} participants processed.")
