"""
Unit tests for preprocessing pipeline.
Verifies bandpass filtering and 50Hz line noise attenuation.
"""
import os
import tempfile
import numpy as np
import mne
import pytest
from scipy.signal import welch

# Import functions to test
from preprocess import apply_filters, validate_segment_length, process_segment, load_config


def create_synthetic_eeg_with_noise(
    duration_sec: float = 120.0,
    sfreq: int = 250,
    n_channels: int = 19,
    noise_freq: float = 50.0,
    noise_amplitude: float = 50.0  # microvolts
) -> mne.io.Raw:
    """
    Create a synthetic EEG signal with 50Hz noise for testing.
    
    Returns:
        MNE Raw object with synthetic data.
    """
    # Create time vector
    times = np.arange(0, duration_sec, 1/sfreq)
    
    # Generate random background EEG (pink noise approximation)
    # Simple white noise for simplicity in test
    data = np.random.randn(n_channels, len(times)) * 10.0  # 10 uV std dev
    
    # Add 50Hz sine wave noise to all channels
    noise = noise_amplitude * np.sin(2 * np.pi * noise_freq * times)
    data += noise
    
    # Create info structure
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    
    # Create Raw object
    raw = mne.io.RawArray(data, info)
    
    return raw


def test_apply_filters_attenuates_50hz():
    """
    Test that the apply_filters function attenuates 50Hz noise by >20dB.
    """
    # Create synthetic signal with strong 50Hz noise
    raw = create_synthetic_eeg_with_noise(
        duration_sec=10.0,  # Short for faster test
        sfreq=250,
        n_channels=1,
        noise_freq=50.0,
        noise_amplitude=100.0  # Strong noise
    )
    
    # Load config
    config = load_config()
    
    # Apply filters
    filtered = apply_filters(
        raw,
        filter_low=config.get('filter_low', 1.0),
        filter_high=config.get('filter_high', 40.0),
        notch_freq=config.get('notch_frequency', 50.0)
    )
    
    # Compute PSD for raw and filtered
    # Use the first channel
    f_raw, p_raw = welch(raw.get_data()[0], fs=250, nperseg=1024)
    f_filt, p_filt = welch(filtered.get_data()[0], fs=250, nperseg=1024)
    
    # Find power at 50Hz
    # Interpolate to find exact power at 50Hz if needed
    def get_power_at_freq(frequencies, powers, target_freq):
        # Simple nearest neighbor
        idx = np.argmin(np.abs(frequencies - target_freq))
        return powers[idx]
    
    power_raw_50 = get_power_at_freq(f_raw, p_raw, 50.0)
    power_filt_50 = get_power_at_freq(f_filt, p_filt, 50.0)
    
    # Calculate attenuation in dB
    # Avoid log(0)
    if power_filt_50 < 1e-10:
        attenuation_db = 100.0  # Assume very high attenuation if near zero
    else:
        attenuation_db = 10 * np.log10(power_raw_50 / power_filt_50)
    
    print(f"Raw power at 50Hz: {power_raw_50:.2e}")
    print(f"Filtered power at 50Hz: {power_filt_50:.2e}")
    print(f"Attenuation: {attenuation_db:.2f} dB")
    
    # Assert attenuation is > 20dB
    assert attenuation_db > 20.0, f"Expected >20dB attenuation, got {attenuation_db:.2f}dB"


def test_validate_segment_length():
    """Test segment length validation."""
    # Create a short segment
    raw_short = create_synthetic_eeg_with_noise(duration_sec=60.0)
    is_valid_short, duration_short = validate_segment_length(raw_short, min_duration_sec=120.0)
    assert not is_valid_short
    assert duration_short == 60.0
    
    # Create a long segment
    raw_long = create_synthetic_eeg_with_noise(duration_sec=150.0)
    is_valid_long, duration_long = validate_segment_length(raw_long, min_duration_sec=120.0)
    assert is_valid_long
    assert duration_long == 150.0


def test_process_segment():
    """Test the full process_segment pipeline."""
    raw = create_synthetic_eeg_with_noise(duration_sec=120.0)
    config = load_config()
    
    processed, events = process_segment(raw, config)
    
    # Check that processing returns a Raw object
    assert isinstance(processed, mne.io.Raw)
    
    # Check that events is a list
    assert isinstance(events, list)
    
    # Check that duration is correct
    assert processed.times[-1] >= 120.0


def test_preprocess_integration(tmp_path):
    """
    Integration test: Run preprocessing on a synthetic file and verify output.
    """
    import json
    from preprocess import preprocess_eeg, save_cleaned_data
    
    # Create a temporary manifest
    manifest_data = [
        {
            "participant_id": "test_001",
            "segment_id": "0",
            "file_path": None  # Will be set below
        }
    ]
    
    # Create a temporary EEG file
    raw = create_synthetic_eeg_with_noise(duration_sec=120.0)
    test_eeg_path = str(tmp_path / "test_001_raw.fif")
    save_cleaned_data(raw, test_eeg_path)
    
    # Update manifest
    manifest_data[0]["file_path"] = test_eeg_path
    
    manifest_path = str(tmp_path / "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    output_dir = str(tmp_path / "cleaned")
    exclusion_log_path = str(tmp_path / "exclusion_log.csv")
    
    config = load_config()
    
    # Run preprocessing
    preprocess_eeg(
        manifest_path=manifest_path,
        output_dir=output_dir,
        exclusion_log_path=exclusion_log_path,
        config=config
    )
    
    # Verify output file exists
    output_file = os.path.join(output_dir, "test_001_0.fif")
    assert os.path.exists(output_file), f"Output file not found: {output_file}"
    
    # Verify exclusion log exists
    assert os.path.exists(exclusion_log_path), f"Exclusion log not found: {exclusion_log_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
