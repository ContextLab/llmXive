import os
import sys
import tempfile
import pytest
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.preprocess import reject_artifacts, apply_bandpass_filter
from code.utils.logging import log_artifact_rejection, get_rejection_counts


class TestArtifactRejection:
    """Unit tests for artifact rejection logic and edge cases."""

    def test_reject_artifacts_all_clean(self, tmp_path):
        """Test artifact rejection when no artifacts are present."""
        # Create clean EEG data (within threshold)
        n_channels = 4
        n_samples = 1000
        sfreq = 250.0
        data = np.random.randn(n_channels, n_samples) * 10  # Small amplitude

        # Apply rejection with strict threshold
        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == 0
        assert len(kept_indices) == n_samples

    def test_reject_artifacts_all_artifacts(self, tmp_path):
        """Test artifact rejection when all data exceeds threshold."""
        n_channels = 4
        n_samples = 1000
        data = np.ones((n_channels, n_samples)) * 200  # All above threshold

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == n_samples
        assert len(kept_indices) == 0

    def test_reject_artifacts_mixed(self, tmp_path):
        """Test artifact rejection with mixed clean and artifact data."""
        n_channels = 4
        n_samples = 1000
        data = np.random.randn(n_channels, n_samples) * 10

        # Inject artifacts in first 100 samples
        data[:, :100] = 150  # Above threshold

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == 100
        assert len(kept_indices) == 900

    def test_reject_artifacts_threshold_boundary(self, tmp_path):
        """Test artifact rejection at exact threshold boundary."""
        n_channels = 4
        n_samples = 100
        data = np.ones((n_channels, n_samples)) * 100.0  # Exactly at threshold

        # Values at threshold should be kept (<= threshold)
        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == 0
        assert len(kept_indices) == n_samples

    def test_reject_artifacts_empty_data(self, tmp_path):
        """Test artifact rejection with empty data."""
        data = np.empty((0, 0))

        with pytest.raises(ValueError):
            reject_artifacts(data, threshold=100.0)

    def test_reject_artifacts_single_sample(self, tmp_path):
        """Test artifact rejection with minimal data size."""
        n_channels = 2
        n_samples = 1
        data = np.array([[50.0], [60.0]])

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == 0
        assert len(kept_indices) == 1

    def test_reject_artifacts_logging(self, tmp_path):
        """Test that artifact rejection is properly logged."""
        log_path = tmp_path / "rejection_log.json"
        data = np.ones((4, 1000)) * 150  # All artifacts

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        # Log the rejection
        log_artifact_rejection(
            participant_id="P001",
            rejected_count=len(rejected_indices),
            kept_count=len(kept_indices),
            reason="amplitude_threshold",
            log_file=str(log_path)
        )

        assert log_path.exists()
        # Verify log contains expected fields
        import json
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        assert "P001" in str(log_data)
        assert log_data.get("rejected_count") == 1000

    def test_reject_artifacts_segment_too_short(self, tmp_path):
        """Test handling when rejected data leaves segment too short."""
        # Create data where rejection would leave < 120 seconds
        n_channels = 4
        sfreq = 250.0
        duration_seconds = 30  # Only 30 seconds
        n_samples = int(sfreq * duration_seconds)

        data = np.random.randn(n_channels, n_samples)
        # Inject artifacts in most of the data
        data[:, :int(n_samples * 0.9)] = 200  # 90% artifacts

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        # Should reject most samples
        assert len(rejected_indices) > len(kept_indices)
        # Remaining samples: 10% of 7500 = 750 samples = 3 seconds
        # This would trigger segment rejection in process_eeg_stream

    def test_reject_artifacts_negative_threshold(self, tmp_path):
        """Test that negative threshold raises error."""
        data = np.random.randn(4, 1000)

        with pytest.raises(ValueError):
            reject_artifacts(data, threshold=-50.0)

    def test_reject_artifacts_zero_threshold(self, tmp_path):
        """Test that zero threshold rejects everything."""
        data = np.random.randn(4, 1000) * 10  # Non-zero values

        rejected_indices, kept_indices = reject_artifacts(data, threshold=0.0)

        # All non-zero values should be rejected
        assert len(rejected_indices) > 0

    def test_reject_artifacts_2d_input(self, tmp_path):
        """Test artifact rejection with 2D input (channels x samples)."""
        data = np.random.randn(10, 5000)
        data[:, :100] = 200  # Artifacts in first 100 samples

        rejected_indices, kept_indices = reject_artifacts(data, threshold=100.0)

        assert len(rejected_indices) == 100
        assert len(kept_indices) == 4900
