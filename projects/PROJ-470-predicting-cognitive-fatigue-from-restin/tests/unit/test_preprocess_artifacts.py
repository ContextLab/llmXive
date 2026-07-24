import os
import pytest
import pandas as pd
import numpy as np
import mne
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Import the function to test
from preprocess import reject_artifacts, setup_logger

class TestArtifactRejection:
    """Unit tests for artifact rejection logic in T011."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sampling_rate = 256
        self.duration = 120 # seconds
        self.n_samples = self.sampling_rate * self.duration
        self.ch_names = ['EEG 001', 'EEG 002', 'EEG 003']
        self.info = mne.create_info(ch_names=self.ch_names, sfreq=self.sampling_rate, ch_types='eeg')
        
        # Create a temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_exclusion_log.csv")

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_valid_segment(self):
        """Test that a valid segment (low amplitude, long duration) passes."""
        # Create data with small amplitude (10 uV)
        data = np.random.normal(0, 1e-6, (len(self.ch_names), self.n_samples))
        raw = mne.io.RawArray(data, self.info)
        
        is_valid, reason, bad_channels = reject_artifacts(
            raw, 
            amplitude_threshold=100.0, 
            min_duration=120.0
        )
        
        assert is_valid is True
        assert reason == "passed"
        assert bad_channels is None

    def test_amplitude_rejection(self):
        """Test rejection when amplitude exceeds threshold (>100uV)."""
        # Create data with high amplitude (150 uV)
        data = np.ones((len(self.ch_names), self.n_samples)) * (150e-6) 
        raw = mne.io.RawArray(data, self.info)
        
        is_valid, reason, bad_channels = reject_artifacts(
            raw, 
            amplitude_threshold=100.0, 
            min_duration=120.0
        )
        
        assert is_valid is False
        assert "amplitude > 100uV" in reason
        assert len(bad_channels) > 0

    def test_duration_rejection(self):
        """Test rejection when segment duration is < 120 seconds."""
        # Create short data (60 seconds)
        short_duration = 60
        short_samples = self.sampling_rate * short_duration
        data = np.random.normal(0, 1e-6, (len(self.ch_names), short_samples))
        raw = mne.io.RawArray(data, self.info)
        
        is_valid, reason, bad_channels = reject_artifacts(
            raw, 
            amplitude_threshold=100.0, 
            min_duration=120.0
        )
        
        assert is_valid is False
        assert "segment < 120s" in reason

    def test_exclusion_log_creation(self):
        """Verify that exclusion_log.csv is created with correct schema."""
        # Setup logger
        logger = setup_logger(os.path.join(self.temp_dir, "test.log"))
        
        # Create a short segment to trigger rejection
        short_samples = self.sampling_rate * 60
        data = np.random.normal(0, 1e-6, (len(self.ch_names), short_samples))
        raw = mne.io.RawArray(data, self.info)
        
        # Trigger rejection
        is_valid, reason, _ = reject_artifacts(raw, amplitude_threshold=100.0, min_duration=120.0)
        assert not is_valid
        
        # Manually log the rejection to simulate the pipeline behavior
        from utils.logging import log_artifact_rejection
        log_artifact_rejection("test_participant_01", reason, self.log_file)
        
        # Verify file exists
        assert os.path.exists(self.log_file), "Exclusion log file was not created."
        
        # Verify schema
        df = pd.read_csv(self.log_file)
        expected_columns = ['participant_id', 'reason', 'timestamp']
        assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
        
        # Verify valid rejection reasons
        valid_reasons = ['amplitude > 100uV', 'segment < 120s']
        assert df['reason'].iloc[0] in valid_reasons, f"Invalid reason: {df['reason'].iloc[0]}"