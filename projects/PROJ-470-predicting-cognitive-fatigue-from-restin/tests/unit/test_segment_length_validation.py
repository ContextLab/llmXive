import os
import sys
import pytest
import pandas as pd
import numpy as np
import mne
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess import reject_short_segments, save_exclusion_log

class TestSegmentLengthValidation:
    """Tests for T014: Segment Length Validation"""
    
    def test_reject_short_segments_rejects(self):
        """Test that segments shorter than 120s are rejected."""
        # Create a mock raw object with short duration
        # We'll simulate by creating a minimal raw object
        sfreq = 250  # Hz
        n_times = 1000  # 4 seconds at 250Hz
        
        # Create dummy data
        data = np.random.randn(1, n_times)
        info = mne.create_info(ch_names=['EEG 001'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)
        
        # Test rejection
        is_valid, reason = reject_short_segments(raw, 120.0, "test_participant", None)
        
        assert not is_valid
        assert reason == "segment_too_short"
    
    def test_reject_short_segments_accepts(self):
        """Test that segments >= 120s are accepted."""
        sfreq = 250  # Hz
        n_times = 30000  # 120 seconds at 250Hz
        
        # Create dummy data
        data = np.random.randn(1, n_times)
        info = mne.create_info(ch_names=['EEG 001'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)
        
        # Test acceptance
        is_valid, reason = reject_short_segments(raw, 120.0, "test_participant", None)
        
        assert is_valid
        assert reason == ""
    
    def test_exclusion_log_contains_short_segment_entries(self, tmp_path):
        """
        Verification for T014: Assert exclusion_log.csv contains entries 
        for rejected segments with reason 'segment_too_short'.
        """
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exclusion_log_path = output_dir / "exclusion_log.csv"
        
        # Create test records including segment_too_short
        records = [
            {
                'participant_id': 'sub-001',
                'reason': 'segment_too_short',
                'timestamp': datetime.now().isoformat()
            },
            {
                'participant_id': 'sub-002',
                'reason': 'amplitude_threshold (1 channels)',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        save_exclusion_log(records, str(exclusion_log_path))
        
        # Verify file exists
        assert exclusion_log_path.exists(), "exclusion_log.csv was not created"
        
        # Read and verify content
        df = pd.read_csv(exclusion_log_path)
        
        # Check required columns
        assert 'participant_id' in df.columns
        assert 'reason' in df.columns
        assert 'timestamp' in df.columns
        
        # Check for segment_too_short entries
        short_segment_entries = df[df['reason'] == 'segment_too_short']
        assert len(short_segment_entries) > 0, "No entries with reason 'segment_too_short' found"
        
        # Verify participant_id is present
        assert short_segment_entries['participant_id'].iloc[0] == 'sub-001'