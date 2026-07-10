"""
Unit tests for prediction error signal extraction and quantification.

This module tests the metrics extraction functions including:
- Difference wave computation (Oddball - Standard)
- Peak latency extraction
- Mean amplitude extraction

These tests verify the correctness of the analysis pipeline for User Story 2.
"""

import pytest
import numpy as np
import mne
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import metrics
from code.config import get_config


class TestDifferenceWaveComputation:
    """Tests for difference wave computation at specific electrode groups."""

    @pytest.fixture
    def mock_evoked_data(self):
        """Create mock evoked data for testing."""
        # Create mock info structure
        ch_names = [f'EEG {i:03d}' for i in range(1, 65)]
        info = mne.create_info(ch_names=ch_names, sfreq=1000, ch_types='eeg')
        
        # Create mock evoked data arrays
        n_times = 500  # 500ms at 1000Hz
        n_channels = len(ch_names)
        
        # Create time vector: -100ms to 400ms (500 points)
        times = np.linspace(-0.1, 0.4, n_times)
        
        # Mock oddball data: Simulate N1/P2 response at fronto-central electrodes
        oddball_data = np.zeros((n_channels, n_times))
        # Add N1 peak around 100ms at fronto-central channels (indices 0-15)
        for i in range(16):
            oddball_data[i, :] = -5 * np.exp(-((times - 0.1) ** 2) / (2 * 0.02 ** 2))
            # Add P2 peak around 200ms
            oddball_data[i, :] += 3 * np.exp(-((times - 0.2) ** 2) / (2 * 0.03 ** 2))
        
        # Mock standard data: Simulate reduced response
        standard_data = np.zeros((n_channels, n_times))
        for i in range(16):
            standard_data[i, :] = -2 * np.exp(-((times - 0.1) ** 2) / (2 * 0.02 ** 2))
            standard_data[i, :] += 1 * np.exp(-((times - 0.2) ** 2) / (2 * 0.03 ** 2))
        
        oddball_evoked = mne.EvokedArray(oddball_data, info, tmin=-0.1)
        standard_evoked = mne.EvokedArray(standard_data, info, tmin=-0.1)
        
        return oddball_evoked, standard_evoked, times

    @pytest.fixture
    def mock_visual_evoked_data(self):
        """Create mock visual evoked data with occipito-parietal response."""
        ch_names = [f'EEG {i:03d}' for i in range(1, 65)]
        info = mne.create_info(ch_names=ch_names, sfreq=1000, ch_types='eeg')
        
        n_times = 500
        n_channels = len(ch_names)
        times = np.linspace(-0.1, 0.4, n_times)
        
        # Visual response at occipito-parietal electrodes (indices 40-55)
        oddball_data = np.zeros((n_channels, n_times))
        for i in range(40, 56):
            # P1 peak around 100ms
            oddball_data[i, :] = 4 * np.exp(-((times - 0.1) ** 2) / (2 * 0.02 ** 2))
            # N1 peak around 150ms
            oddball_data[i, :] += -3 * np.exp(-((times - 0.15) ** 2) / (2 * 0.02 ** 2))
        
        standard_data = np.zeros((n_channels, n_times))
        for i in range(40, 56):
            standard_data[i, :] = 2 * np.exp(-((times - 0.1) ** 2) / (2 * 0.02 ** 2))
            standard_data[i, :] += -1 * np.exp(-((times - 0.15) ** 2) / (2 * 0.02 ** 2))
        
        oddball_evoked = mne.EvokedArray(oddball_data, info, tmin=-0.1)
        standard_evoked = mne.EvokedArray(standard_data, info, tmin=-0.1)
        
        return oddball_evoked, standard_evoked, times

    def test_auditory_difference_wave(self, mock_evoked_data):
        """Test difference wave computation for auditory modality at fronto-central electrodes."""
        oddball, standard, times = mock_evoked_data
        
        # Compute difference wave
        diff_wave, electrode_indices = metrics.compute_auditory_difference_wave(
            oddball, standard
        )
        
        # Verify output shape
        assert diff_wave.shape[0] == len(electrode_indices), \
            "Difference wave should have same number of channels as selected electrodes"
        assert diff_wave.shape[1] == len(times), \
            "Difference wave should have same time points as input"
        
        # Verify difference wave is oddball - standard
        expected_diff = oddball.get_data()[electrode_indices, :] - standard.get_data()[electrode_indices, :]
        np.testing.assert_array_almost_equal(
            diff_wave, expected_diff, 
            decimal=5,
            err_msg="Difference wave should equal oddball - standard"
        )
        
        # Verify electrode selection (should be fronto-central)
        assert len(electrode_indices) > 0, "Should select at least one fronto-central electrode"

    def test_visual_difference_wave(self, mock_visual_evoked_data):
        """Test difference wave computation for visual modality at occipito-parietal electrodes."""
        oddball, standard, times = mock_visual_evoked_data
        
        # Compute difference wave
        diff_wave, electrode_indices = metrics.compute_visual_difference_wave(
            oddball, standard
        )
        
        # Verify output shape
        assert diff_wave.shape[0] == len(electrode_indices), \
            "Difference wave should have same number of channels as selected electrodes"
        assert diff_wave.shape[1] == len(times), \
            "Difference wave should have same time points as input"
        
        # Verify difference wave is oddball - standard
        expected_diff = oddball.get_data()[electrode_indices, :] - standard.get_data()[electrode_indices, :]
        np.testing.assert_array_almost_equal(
            diff_wave, expected_diff,
            decimal=5,
            err_msg="Difference wave should equal oddball - standard"
        )
        
        # Verify electrode selection (should be occipito-parietal)
        assert len(electrode_indices) > 0, "Should select at least one occipito-parietal electrode"

    def test_difference_wave_mismatch_error(self, mock_evoked_data):
        """Test that mismatched time dimensions raise an error."""
        oddball, standard, times = mock_evoked_data
        
        # Create a standard with different time points
        bad_times = np.linspace(-0.1, 0.3, 400)  # Different length
        bad_info = mne.create_info(ch_names=oddball.ch_names, sfreq=1000, ch_types='eeg')
        bad_standard = mne.EvokedArray(standard.get_data(), bad_info, tmin=-0.1)
        
        with pytest.raises(ValueError, match="Time dimensions must match"):
            metrics.compute_auditory_difference_wave(oddball, bad_standard)

class TestPeakLatencyExtraction:
    """Tests for peak latency extraction in specified time windows."""

    @pytest.fixture
    def mock_diff_wave(self):
        """Create mock difference wave with known peaks."""
        n_times = 500
        times = np.linspace(-0.1, 0.4, n_times)  # -100ms to 400ms
        
        # Create signal with known peak at 120ms (0.12s)
        signal = np.zeros((5, n_times))  # 5 channels
        peak_time_idx = np.where(np.isclose(times, 0.12, atol=0.01))[0][0]
        
        for i in range(5):
            # Gaussian peak at 120ms
            signal[i, :] = 10 * np.exp(-((times - 0.12) ** 2) / (2 * 0.015 ** 2))
        
        return signal, times

    def test_auditory_peak_latency_extraction(self, mock_diff_wave):
        """Test peak latency extraction for auditory modality (N1 window: 80-150ms)."""
        diff_wave, times = mock_diff_wave
        
        # Define N1 window: 80ms to 150ms
        window_start = 0.08
        window_end = 0.15
        
        # Extract peak latency
        peak_latency_ms, peak_amplitude_uv = metrics.extract_auditory_peak_latency(
            diff_wave, times, window_start, window_end
        )
        
        # Verify output types
        assert isinstance(peak_latency_ms, (list, np.ndarray)), "Peak latency should be a list/array"
        assert isinstance(peak_amplitude_uv, (list, np.ndarray)), "Peak amplitude should be a list/array"
        assert len(peak_latency_ms) == diff_wave.shape[0], \
            "Should return one latency per channel"
        
        # Verify peak is within expected window
        for lat in peak_latency_ms:
            assert 80 <= lat <= 150, f"Peak latency {lat}ms should be within 80-150ms window"
        
        # Verify peak is close to known 120ms
        assert np.allclose(peak_latency_ms, 120, atol=10), \
            f"Extracted peak {np.mean(peak_latency_ms)}ms should be close to 120ms"

    def test_visual_peak_latency_extraction(self, mock_diff_wave):
        """Test peak latency extraction for visual modality (P1 window: 80-140ms)."""
        diff_wave, times = mock_diff_wave
        
        # Define P1 window: 80ms to 140ms
        window_start = 0.08
        window_end = 0.14
        
        # Extract peak latency
        peak_latency_ms, peak_amplitude_uv = metrics.extract_visual_peak_latency(
            diff_wave, times, window_start, window_end
        )
        
        # Verify output types
        assert isinstance(peak_latency_ms, (list, np.ndarray))
        assert isinstance(peak_amplitude_uv, (list, np.ndarray))
        assert len(peak_latency_ms) == diff_wave.shape[0]
        
        # Verify peak is within expected window
        for lat in peak_latency_ms:
            assert 80 <= lat <= 140, f"Peak latency {lat}ms should be within 80-140ms window"
        
        # Verify peak is close to known 120ms
        assert np.allclose(peak_latency_ms, 120, atol=10), \
            f"Extracted peak {np.mean(peak_latency_ms)}ms should be close to 120ms"

    def test_peak_latency_empty_window(self):
        """Test that an empty time window raises an error."""
        n_times = 500
        times = np.linspace(-0.1, 0.4, n_times)
        diff_wave = np.zeros((5, n_times))
        
        # Window outside data range
        with pytest.raises(ValueError, match="No data points in specified time window"):
            metrics.extract_auditory_peak_latency(diff_wave, times, 2.0, 3.0)  # 2000-3000ms

class TestMeanAmplitudeExtraction:
    """Tests for mean amplitude extraction in specified time windows."""

    @pytest.fixture
    def mock_diff_wave_with_baseline(self):
        """Create mock difference wave with baseline and known amplitude."""
        n_times = 500
        times = np.linspace(-0.1, 0.4, n_times)  # -100ms to 400ms
        
        # Create signal with known mean amplitude in window
        signal = np.zeros((5, n_times))
        
        # Add constant amplitude in 100-200ms window
        window_mask = (times >= 0.1) & (times <= 0.2)
        signal[:, window_mask] = 5.0  # 5 µV mean amplitude
        
        # Add noise outside window
        signal[:, ~window_mask] = np.random.normal(0, 0.5, signal[:, ~window_mask].shape)
        
        return signal, times

    def test_auditory_mean_amplitude_extraction(self, mock_diff_wave_with_baseline):
        """Test mean amplitude extraction for auditory modality."""
        diff_wave, times = mock_diff_wave_with_baseline
        
        # Define window: 100ms to 200ms
        window_start = 0.1
        window_end = 0.2
        
        # Extract mean amplitude
        mean_amplitude_uv = metrics.extract_auditory_mean_amplitude(
            diff_wave, times, window_start, window_end
        )
        
        # Verify output
        assert isinstance(mean_amplitude_uv, (list, np.ndarray))
        assert len(mean_amplitude_uv) == diff_wave.shape[0]
        
        # Verify mean amplitude is close to 5 µV
        assert np.allclose(mean_amplitude_uv, 5.0, atol=0.5), \
            f"Mean amplitude {np.mean(mean_amplitude_uv)}µV should be close to 5µV"

    def test_visual_mean_amplitude_extraction(self, mock_diff_wave_with_baseline):
        """Test mean amplitude extraction for visual modality."""
        diff_wave, times = mock_diff_wave_with_baseline
        
        # Define window: 100ms to 200ms
        window_start = 0.1
        window_end = 0.2
        
        # Extract mean amplitude
        mean_amplitude_uv = metrics.extract_visual_mean_amplitude(
            diff_wave, times, window_start, window_end
        )
        
        # Verify output
        assert isinstance(mean_amplitude_uv, (list, np.ndarray))
        assert len(mean_amplitude_uv) == diff_wave.shape[0]
        
        # Verify mean amplitude is close to 5 µV
        assert np.allclose(mean_amplitude_uv, 5.0, atol=0.5)

    def test_mean_amplitude_empty_window(self):
        """Test that an empty time window raises an error."""
        n_times = 500
        times = np.linspace(-0.1, 0.4, n_times)
        diff_wave = np.zeros((5, n_times))
        
        # Window outside data range
        with pytest.raises(ValueError, match="No data points in specified time window"):
            metrics.extract_auditory_mean_amplitude(diff_wave, times, 2.0, 3.0)

class TestIntegrationMetrics:
    """Integration tests for the full metrics extraction pipeline."""

    @pytest.fixture
    def full_auditory_evoked_pair(self):
        """Create a complete mock auditory evoked pair for integration testing."""
        ch_names = [f'EEG {i:03d}' for i in range(1, 65)]
        info = mne.create_info(ch_names=ch_names, sfreq=1000, ch_types='eeg')
        
        n_times = 600  # 700ms window: -100ms to 600ms
        times = np.linspace(-0.1, 0.6, n_times)
        
        # Simulate realistic N1-P2 response at fronto-central electrodes
        oddball_data = np.zeros((64, n_times))
        standard_data = np.zeros((64, n_times))
        
        # Fz, Cz, FCz, FC1, FC2 (approximate indices 0-15)
        for i in range(16):
            # N1 at 100ms
            oddball_data[i, :] -= 6 * np.exp(-((times - 0.1) ** 2) / (2 * 0.025 ** 2))
            standard_data[i, :] -= 2 * np.exp(-((times - 0.1) ** 2) / (2 * 0.025 ** 2))
            
            # P2 at 200ms
            oddball_data[i, :] += 3 * np.exp(-((times - 0.2) ** 2) / (2 * 0.03 ** 2))
            standard_data[i, :] += 1 * np.exp(-((times - 0.2) ** 2) / (2 * 0.03 ** 2))
        
        oddball = mne.EvokedArray(oddball_data, info, tmin=-0.1)
        standard = mne.EvokedArray(standard_data, info, tmin=-0.1)
        
        return oddball, standard, times

    def test_full_auditory_extraction_pipeline(self, full_auditory_evoked_pair):
        """Test the complete auditory metrics extraction pipeline."""
        oddball, standard, times = full_auditory_evoked_pair
        
        # Step 1: Compute difference wave
        diff_wave, electrode_indices = metrics.compute_auditory_difference_wave(
            oddball, standard
        )
        
        # Step 2: Extract N1 peak (80-150ms)
        n1_latency, n1_amplitude = metrics.extract_auditory_peak_latency(
            diff_wave, times, 0.08, 0.15
        )
        
        # Step 3: Extract mean amplitude in N1 window
        n1_mean_amp = metrics.extract_auditory_mean_amplitude(
            diff_wave, times, 0.08, 0.15
        )
        
        # Verify all outputs
        assert len(n1_latency) == len(electrode_indices)
        assert len(n1_amplitude) == len(electrode_indices)
        assert len(n1_mean_amp) == len(electrode_indices)
        
        # Verify N1 latency is around 100ms
        assert np.allclose(n1_latency, 100, atol=15), \
            f"N1 latency {np.mean(n1_latency)}ms should be around 100ms"
        
        # Verify N1 amplitude is negative (N1 is a negative peak)
        assert np.all(np.array(n1_amplitude) < 0), "N1 amplitude should be negative"

    def test_full_visual_extraction_pipeline(self):
        """Test the complete visual metrics extraction pipeline."""
        # Create visual-specific mock data
        ch_names = [f'EEG {i:03d}' for i in range(1, 65)]
        info = mne.create_info(ch_names=ch_names, sfreq=1000, ch_types='eeg')
        
        n_times = 600
        times = np.linspace(-0.1, 0.6, n_times)
        
        # Visual response at occipito-parietal (indices 40-55)
        oddball_data = np.zeros((64, n_times))
        standard_data = np.zeros((64, n_times))
        
        for i in range(40, 56):
            # P1 at 100ms
            oddball_data[i, :] += 5 * np.exp(-((times - 0.1) ** 2) / (2 * 0.025 ** 2))
            standard_data[i, :] += 2 * np.exp(-((times - 0.1) ** 2) / (2 * 0.025 ** 2))
            
            # N1 at 150ms
            oddball_data[i, :] -= 4 * np.exp(-((times - 0.15) ** 2) / (2 * 0.025 ** 2))
            standard_data[i, :] -= 1.5 * np.exp(-((times - 0.15) ** 2) / (2 * 0.025 ** 2))
        
        oddball = mne.EvokedArray(oddball_data, info, tmin=-0.1)
        standard = mne.EvokedArray(standard_data, info, tmin=-0.1)
        
        # Step 1: Compute difference wave
        diff_wave, electrode_indices = metrics.compute_visual_difference_wave(
            oddball, standard
        )
        
        # Step 2: Extract P1 peak (80-140ms)
        p1_latency, p1_amplitude = metrics.extract_visual_peak_latency(
            diff_wave, times, 0.08, 0.14
        )
        
        # Step 3: Extract N1 peak (120-200ms)
        n1_latency, n1_amplitude = metrics.extract_visual_peak_latency(
            diff_wave, times, 0.12, 0.20
        )
        
        # Verify outputs
        assert len(p1_latency) == len(electrode_indices)
        assert len(n1_latency) == len(electrode_indices)
        
        # Verify P1 latency around 100ms
        assert np.allclose(p1_latency, 100, atol=15)
        
        # Verify N1 latency around 150ms
        assert np.allclose(n1_latency, 150, atol=15)