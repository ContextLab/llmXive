import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path if running from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.preprocess import (
    linear_interpolate_missing,
    bandpass_filter,
    notch_filter,
    preprocess_signal,
    segment_into_epochs,
    extract_transition_windows,
    extract_pre_transition_windows,
    preprocess_subject
)

class TestPreprocess:
    @pytest.fixture
    def sample_signal(self):
        # 10 seconds of 100Hz data
        fs = 100
        t = np.arange(0, 10, 1/fs)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
        return signal, fs

    def test_linear_interpolate_missing_no_nans(self, sample_signal):
        signal, fs = sample_signal
        result = linear_interpolate_missing(signal)
        np.testing.assert_array_equal(result, signal)

    def test_linear_interpolate_missing_with_nans(self, sample_signal):
        signal, fs = sample_signal
        signal_with_nans = signal.copy()
        signal_with_nans[10:20] = np.nan
        result = linear_interpolate_missing(signal_with_nans)
        assert not np.any(np.isnan(result))
        # Check that values around the gap are reasonable (interpolated)
        assert result[9] != result[20] # Should be different

    def test_bandpass_filter(self, sample_signal):
        signal, fs = sample_signal
        filtered = bandpass_filter(signal, fs, lowcut=5, highcut=30)
        assert len(filtered) == len(signal)
        # Check that DC component is removed (if any)
        assert np.mean(filtered) < 1.0 # Should be close to 0

    def test_notch_filter(self, sample_signal):
        signal, fs = sample_signal
        # Add 50Hz noise
        noise = 0.5 * np.sin(2 * np.pi * 50 * np.arange(0, len(signal)/fs, 1/fs))
        noisy_signal = signal + noise
        filtered = notch_filter(noisy_signal, fs, freq=50)
        # The 50Hz component should be significantly attenuated
        # Simple check: variance should be lower than original noisy signal
        assert np.var(filtered) < np.var(noisy_signal)

    def test_segment_into_epochs(self, sample_signal):
        signal, fs = sample_signal
        epochs = segment_into_epochs(signal, fs, epoch_duration=2.0)
        assert epochs.shape[0] == 5 # 10 seconds / 2 seconds
        assert epochs.shape[1] == 200 # 2 seconds * 100 Hz

    def test_extract_transition_windows(self):
        # Create synthetic data: 4 epochs, stage change at epoch 2
        fs = 100
        epochs = np.random.randn(4, 300) # 4 epochs, 3s each (300 samples)
        hypnogram = np.array([1, 1, 2, 2]) # Change at index 2
        
        windows, indices = extract_transition_windows(epochs, hypnogram, fs, window_duration=2.0)
        
        assert len(indices) == 1
        assert indices[0] == 2
        assert windows.shape[0] == 1
        assert windows.shape[1] == 200 # 2s window

    def test_extract_pre_transition_windows(self):
        # Create synthetic data: 4 epochs, stage change at epoch 2
        fs = 100
        epochs = np.random.randn(4, 300) # 4 epochs, 3s each (300 samples)
        hypnogram = np.array([1, 1, 2, 2]) # Change at index 2
        
        # 60s window, ending 30s before transition
        # Transition is at start of epoch 2 (sample 600)
        # Window ends at 600 - 3000 (30s) = -2400 (out of bounds for this small example)
        # Let's create a larger example
        
        fs = 100
        num_epochs = 10
        samples_per_epoch = 3000 # 30s epochs
        epochs_large = np.random.randn(num_epochs, samples_per_epoch)
        hypnogram_large = np.array([1]*5 + [2]*5) # Change at index 5
        
        # 60s window, ending 30s before transition
        windows, targets, indices = extract_pre_transition_windows(
            epochs_large, hypnogram_large, fs, window_duration=60.0, lead_time=30.0
        )
        
        # Transition at epoch 5 (start sample 5 * 3000 = 15000)
        # Window ends at 15000 - 3000 = 12000
        # Window starts at 12000 - 6000 = 6000
        # Should be valid
        
        assert len(indices) == 1
        assert indices[0] == 5
        assert targets[0] == 2
        assert windows.shape[0] == 1
        assert windows.shape[1] == 6000 # 60s * 100Hz

    def test_preprocess_subject(self):
        # Mock subject data
        fs = 100
        signal = np.random.randn(2, 1000) # 2 channels, 10s
        hypnogram = np.array([1, 1, 2, 2])
        
        subject_data = {
            'signal': signal,
            'hypnogram': hypnogram,
            'fs': fs,
            'subject_id': 'test_subject'
        }
        
        result = preprocess_subject(subject_data)
        
        assert 'signal' in result
        assert 'hypnogram' in result
        assert result['fs'] == fs
        assert result['subject_id'] == 'test_subject'
        assert result['signal'].shape == signal.shape
        # Check that preprocessing was applied (no NaNs)
        assert not np.any(np.isnan(result['signal']))
