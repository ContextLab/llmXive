"""
Test for Task T012: Preprocessing verification.
Verifies that the preprocessing script runs and attenuates 50Hz noise.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np
import mne
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocess import (
    load_sample_path,
    load_eeg_data,
    apply_filters,
    verify_filtering,
    save_cleaned_data,
    main
)
from config import load_config


@pytest.fixture
def sample_eeg_file(tmp_path):
    """Create a sample EEG file for testing if the real one doesn't exist or to mock."""
    # We rely on the real file created by T012a if it exists, otherwise we might need to mock.
    # But per task instructions, we assume T012a ran.
    real_sample = Path("data/raw/sample_eeg_verification.fif")
    if real_sample.exists():
        return real_sample
    else:
        # Fallback: Create a synthetic sample for the test to run without the full pipeline
        # This is allowed ONLY for the unit test to verify the logic, not for the main pipeline.
        info = mne.create_info(ch_names=['EEG 001', 'EEG 002'], sfreq=250, ch_types='eeg')
        data = np.random.randn(2, 250 * 10) # 10 seconds
        raw = mne.io.RawArray(data, info)
        fake_path = tmp_path / "fake_sample.fif"
        raw.save(fake_path, overwrite=True)
        return fake_path


def test_50hz_attenuation(sample_eeg_file, tmp_path):
    """
    Verify that the 50Hz line noise is attenuated by > 20dB.
    """
    # Load config
    config = load_config("code/config.yaml")
    
    # Load data
    raw = load_eeg_data(sample_eeg_file)
    
    # Inject a 50Hz sine wave to ensure there is something to attenuate
    # This simulates line noise if the original file is clean
    fs = raw.info['sfreq']
    duration = raw.times[-1]
    t = np.arange(0, duration, 1/fs)
    # 50Hz sine wave with amplitude 50uV
    noise_50hz = 50e-6 * np.sin(2 * np.pi * 50 * t)
    
    # Add noise to all channels
    data = raw.get_data()
    for i in range(data.shape[0]):
        data[i, :] += noise_50hz
    
    # Create a new raw object with injected noise
    info = raw.info.copy()
    raw_with_noise = mne.io.RawArray(data, info)
    
    # Apply filters
    raw_filtered = apply_filters(raw_with_noise, config)
    
    # Verify
    passed = verify_filtering(raw_with_noise, raw_filtered)
    
    # Assert the file was created if we were saving
    output_path = tmp_path / "cleaned.fif"
    save_cleaned_data(raw_filtered, output_path)
    assert output_path.exists()
    
    # The verify_filtering function logs the result. 
    # We assert that the function returns True (or that the attenuation is sufficient).
    # Since verify_filtering returns True if attenuation >= 20dB, we assert that.
    # Note: In a real scenario, if the input didn't have 50Hz, the test might be less meaningful,
    # but with injected noise, it should pass.
    assert passed, "50Hz attenuation verification failed."


def test_preprocess_script_runs():
    """
    Test that the main entry point runs without error on the sample file.
    """
    # This test assumes the sample file exists from T012a
    sample_path = Path("data/raw/sample_eeg_verification.fif")
    if not sample_path.exists():
        pytest.skip("Sample file not found. Run T012a first.")
    
    output_path = Path("data/processed/cleaned_eeg_verification.fif")
    if output_path.exists():
        output_path.unlink()
        
    # Run the main function with specific args
    # We can't easily capture sys.exit in a simple way, so we call the logic directly
    # or use subprocess. Here we call the logic directly to avoid sys.exit issues in pytest.
    from preprocess import preprocess_eeg, load_config
    
    config = load_config("code/config.yaml")
    try:
        preprocess_eeg(sample_path, output_path, config)
        assert output_path.exists(), "Output file was not created."
    except Exception as e:
        pytest.fail(f"Preprocessing script failed: {e}")