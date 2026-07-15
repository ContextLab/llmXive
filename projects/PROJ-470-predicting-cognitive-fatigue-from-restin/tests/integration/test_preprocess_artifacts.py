import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

import mne
from preprocess import reject_artifacts, load_config
from utils.logging import get_rejection_counts

class TestArtifactRejection:
    """Integration tests for artifact rejection logic in preprocess.py"""

    def create_test_raw(self, duration=180, n_channels=2, sample_rate=100, max_amplitude=50.0):
        """Create a test MNE Raw object with specified properties."""
        # Create time vector
        n_times = int(duration * sample_rate)
        times = np.linspace(0, duration, n_times)
        
        # Create data with controlled amplitude
        # Use sine wave with specified max amplitude
        data = np.zeros((n_channels, n_times))
        for i in range(n_channels):
            data[i, :] = max_amplitude * np.sin(2 * np.pi * 10 * times)  # 10 Hz sine wave
        
        # Create info structure
        info = mne.create_info(
            ch_names=[f'EEG{i:03d}' for i in range(n_channels)],
            sfreq=sample_rate,
            ch_types='eeg'
        )
        
        # Create raw object
        raw = mne.io.RawArray(data, info)
        return raw

    def test_duration_rejection(self):
        """Test that segments < 120 seconds are rejected."""
        # Create a short segment (100 seconds)
        raw = self.create_test_raw(duration=100, max_amplitude=50.0)
        
        # Load config (or create default)
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify rejection
        assert stats['rejected_segments'] == 1, "Short segment should be rejected"
        assert stats['rejected_by_duration'] == 1, "Should be rejected by duration"
        assert any('Duration' in reason for reason in stats['reasons']), "Should have duration reason"

    def test_amplitude_rejection(self):
        """Test that segments with amplitude > ±100µV are rejected."""
        # Create segment with high amplitude (150µV)
        raw = self.create_test_raw(duration=180, max_amplitude=150.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify rejection
        assert stats['rejected_segments'] == 1, "High amplitude segment should be rejected"
        assert stats['rejected_by_amplitude'] == 1, "Should be rejected by amplitude"
        assert any('amplitude' in reason.lower() for reason in stats['reasons']), "Should have amplitude reason"

    def test_both_criteria_rejection(self):
        """Test rejection when both duration and amplitude criteria are violated."""
        # Create short segment with high amplitude
        raw = self.create_test_raw(duration=100, max_amplitude=150.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify rejection
        assert stats['rejected_segments'] == 1, "Segment should be rejected"
        assert stats['rejected_by_both'] == 1, "Should be rejected by both criteria"
        assert len(stats['reasons']) == 2, "Should have two rejection reasons"

    def test_accept_valid_segment(self):
        """Test that valid segments are accepted."""
        # Create valid segment: >120s duration, amplitude <100µV
        raw = self.create_test_raw(duration=180, max_amplitude=50.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify acceptance
        assert stats['rejected_segments'] == 0, "Valid segment should be accepted"
        assert stats['rejected_by_amplitude'] == 0, "Should not be rejected by amplitude"
        assert stats['rejected_by_duration'] == 0, "Should not be rejected by duration"
        assert len(stats['reasons']) == 0, "Should have no rejection reasons"

    def test_boundary_duration(self):
        """Test behavior at the 120 second boundary."""
        # Create segment exactly at 120 seconds
        raw = self.create_test_raw(duration=120, max_amplitude=50.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify acceptance (120s should be acceptable, <120s rejected)
        assert stats['rejected_segments'] == 0, "120s segment should be accepted"

    def test_boundary_amplitude(self):
        """Test behavior at the 100µV amplitude boundary."""
        # Create segment with amplitude exactly at 100µV
        raw = self.create_test_raw(duration=180, max_amplitude=100.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify acceptance (100µV should be acceptable, >100µV rejected)
        assert stats['rejected_segments'] == 0, "100µV segment should be accepted"

    def test_logging_integration(self):
        """Test that rejections are properly logged."""
        # Create invalid segment
        raw = self.create_test_raw(duration=100, max_amplitude=150.0)
        
        # Load config
        config = load_config()
        
        # Apply rejection
        cleaned_raw, stats = reject_artifacts(raw, config)
        
        # Verify that rejection counts are updated
        counts = get_rejection_counts()
        assert counts['total_artifact_rejections'] > 0, "Rejection should be logged"
        assert counts['rejected_by_amplitude'] > 0, "Amplitude rejection should be logged"
        assert counts['rejected_by_duration'] > 0, "Duration rejection should be logged"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
