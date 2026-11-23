"""
Tests for HRV preprocessing pipeline.
"""

import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.hrv_utils import SignalQualityError, reject_artifacts
from utils.hrv_utils import validate_signal_structure, compute_clean_rr_stats

# Import functions to test
from code_02_preprocess_hrv import (
    detect_peaks,
    compute_rr_intervals,
    compute_hrv_metrics,
    process_subject_signals
)

# Mock data for testing
def create_mock_ecg_signal(n_samples=10000, sample_rate=700, n_beats=100):
    """Create a mock ECG signal with known R-peaks."""
    t = np.arange(n_samples) / sample_rate
    signal = np.random.normal(0, 0.5, n_samples)  # Base noise

    # Add synthetic QRS complexes
    beat_interval = n_samples / n_beats
    for i in range(n_beats):
        peak_idx = int(i * beat_interval)
        # Add a QRS-like spike
        signal[peak_idx] = 5.0
        if peak_idx + 1 < n_samples:
            signal[peak_idx + 1] = -2.0
        if peak_idx + 2 < n_samples:
            signal[peak_idx + 2] = 1.0

    return signal

class TestDetectPeaks:
    """Tests for peak detection."""

    def test_detect_peaks_basic(self):
        """Test basic peak detection on mock signal."""
        signal = create_mock_ecg_signal(n_samples=7000, n_beats=70)
        peaks = detect_peaks(signal, sample_rate=700)

        assert len(peaks) > 0, "No peaks detected"
        assert len(peaks) < 100, "Too many peaks detected (expected ~70)"

    def test_detect_peaks_empty_signal(self):
        """Test peak detection on empty signal."""
        signal = np.zeros(1000)
        peaks = detect_peaks(signal, sample_rate=700)

        assert len(peaks) == 0, "Peaks detected in flat signal"

class TestComputeRRIntervals:
    """Tests for RR interval computation."""

    def test_compute_rr_intervals_basic(self):
        """Test RR interval computation."""
        peaks = np.array([100, 200, 300, 400, 500])
        sample_rate = 700

        rr_intervals = compute_rr_intervals(peaks, sample_rate)

        assert len(rr_intervals) == len(peaks) - 1
        assert np.all(rr_intervals > 0), "Negative RR intervals found"

    def test_compute_rr_intervals_single_peak(self):
        """Test RR interval computation with single peak."""
        peaks = np.array([100])
        sample_rate = 700

        rr_intervals = compute_rr_intervals(peaks, sample_rate)

        assert len(rr_intervals) == 0

class TestComputeHRVMetrics:
    """Tests for HRV metric computation."""

    def test_compute_hrv_metrics_basic(self):
        """Test basic HRV metric computation."""
        rr_intervals = np.array([0.8, 0.85, 0.75, 0.82, 0.78])

        metrics = compute_hrv_metrics(rr_intervals)

        assert 'RMSSD' in metrics
        assert 'SDNN' in metrics
        assert metrics['RMSSD'] > 0
        assert metrics['SDNN'] > 0

    def test_compute_hrv_metrics_minimum_intervals(self):
        """Test HRV metric computation with minimum intervals."""
        rr_intervals = np.array([0.8, 0.9])

        metrics = compute_hrv_metrics(rr_intervals)

        assert metrics['RMSSD'] > 0
        assert metrics['SDNN'] > 0

    def test_compute_hrv_metrics_insufficient_data(self):
        """Test HRV metric computation with insufficient data."""
        rr_intervals = np.array([0.8])

        with pytest.raises(ValueError):
            compute_hrv_metrics(rr_intervals)

class TestProcessSubjectSignals:
    """Tests for subject signal processing."""

    def test_process_subject_signals_valid(self):
        """Test processing of valid subject signals."""
        signal = create_mock_ecg_signal(n_samples=7000, n_beats=70)

        subject_data = {
            'baseline': {
                'signal': signal,
                'timestamps': None
            }
        }

        results = process_subject_signals(subject_data)

        assert len(results) > 0, "No results returned"
        assert 'RMSSD' in results[0]
        assert 'SDNN' in results[0]

    def test_process_subject_signals_noisy(self):
        """Test processing of noisy subject signals."""
        # Create very noisy signal
        signal = np.random.normal(0, 10, 7000)

        subject_data = {
            'baseline': {
                'signal': signal,
                'timestamps': None
            }
        }

        results = process_subject_signals(subject_data)

        # Should either return results or handle gracefully
        # (might return empty list if signal quality is too poor)
        assert isinstance(results, list)

class TestArtifactRejection:
    """Tests for artifact rejection."""

    def test_reject_artifacts_basic(self):
        """Test basic artifact rejection."""
        # Create RR intervals with some outliers
        rr_intervals = np.array([0.8, 0.85, 0.75, 0.82, 0.78, 2.5, 0.81, 0.79])

        clean_rr, valid_ratio = reject_artifacts(rr_intervals)

        assert len(clean_rr) <= len(rr_intervals)
        assert valid_ratio <= 1.0
        assert valid_ratio >= 0.0

    def test_reject_artifacts_all_outliers(self):
        """Test artifact rejection when all values are outliers."""
        # Create RR intervals with all extreme values
        rr_intervals = np.array([0.1, 0.1, 0.1, 0.1, 5.0, 5.0, 5.0])

        clean_rr, valid_ratio = reject_artifacts(rr_intervals)

        assert valid_ratio < 1.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
