import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import numpy as np
import mne
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import reject_artifacts, save_rejection_log, load_config
from utils.logging import save_exclusion_log_csv

class TestArtifactRejection:
    """Tests for T011: Artifact rejection logic."""

    def setup_method(self):
        """Create temporary directory for test logs."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, 'exclusion_log.csv')

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_mock_raw(self, duration=130, amplitude=50e-6):
        """Create a mock MNE Raw object for testing."""
        sfreq = 250
        n_samples = int(duration * sfreq)
        # Create data with specified amplitude
        data = np.random.randn(1, n_samples) * amplitude
        info = mne.create_info(ch_names=['EEG001'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)
        return raw

    def test_amplitude_rejection(self):
        """Test that segments > 100uV are rejected."""
        # Create signal with 150uV amplitude (should be rejected)
        raw = self.create_mock_raw(duration=130, amplitude=150e-6)
        
        clean_raw, rejections = reject_artifacts(raw, amplitude_threshold=100e-6, min_duration=120)
        
        assert clean_raw is None, "Signal with amplitude > 100uV should be rejected."
        assert len(rejections) == 1
        assert rejections[0]['reason'] == 'amplitude > 100uV'

    def test_duration_rejection(self):
        """Test that segments < 120s are rejected."""
        # Create signal with 100s duration (should be rejected)
        raw = self.create_mock_raw(duration=100, amplitude=50e-6)
        
        clean_raw, rejections = reject_artifacts(raw, amplitude_threshold=100e-6, min_duration=120)
        
        assert clean_raw is None, "Signal with duration < 120s should be rejected."
        assert len(rejections) == 1
        assert rejections[0]['reason'] == 'segment < 120s'

    def test_accept_clean_segment(self):
        """Test that clean segments are accepted."""
        # Create signal with 130s duration and 50uV amplitude
        raw = self.create_mock_raw(duration=130, amplitude=50e-6)
        
        clean_raw, rejections = reject_artifacts(raw, amplitude_threshold=100e-6, min_duration=120)
        
        assert clean_raw is not None, "Clean signal should be accepted."
        assert len(rejections) == 0

    def test_log_file_format(self):
        """Test that exclusion log has correct columns and valid reasons."""
        # Simulate log entries
        entries = [
            {"participant_id": "sub-001", "reason": "amplitude > 100uV", "timestamp": "2023-01-01T00:00:00", "details": "Max: 150uV"},
            {"participant_id": "sub-002", "reason": "segment < 120s", "timestamp": "2023-01-01T00:01:00", "details": "Dur: 100s"}
        ]
        
        save_rejection_log(self.log_path, entries)
        
        assert os.path.exists(self.log_path), "Exclusion log file should exist."
        
        with open(self.log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2, "Log should contain 2 entries."
        
        # Check required columns
        required_cols = ['participant_id', 'reason', 'timestamp']
        for col in required_cols:
            assert col in rows[0], f"Column {col} missing in log."
        
        # Check valid reasons
        valid_reasons = ['amplitude > 100uV', 'segment < 120s']
        for row in rows:
            assert row['reason'] in valid_reasons, f"Invalid reason found: {row['reason']}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])