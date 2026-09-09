"""
Unit tests for code/behavior.py (T031).
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from behavior import (
    setup_logging, 
    load_valid_subjects, 
    find_event_tsv, 
    extract_trial_rts, 
    process_subject_behavior
)

class TestBehaviorExtraction:
    
    @pytest.fixture
    def temp_event_file(self, tmp_path):
        """Creates a temporary events.tsv file with realistic BIDS structure."""
        data = {
            'onset': [0.0, 2.0, 4.0, 6.0],
            'duration': [1.0, 1.0, 1.0, 1.0],
            'trial_type': ['normal', 'delayed', 'pitch-shifted', 'normal'],
            'reaction_time': [0.5, 0.6, 0.55, 0.45] # in seconds
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "sub-01_task-motor_events.tsv"
        df.to_csv(file_path, sep='\t', index=False)
        return file_path

    @pytest.fixture
    def temp_subject_dir(self, tmp_path, temp_event_file):
        """Creates a fake subject directory structure."""
        func_dir = tmp_path / "func"
        func_dir.mkdir()
        # Move event file to func dir
        target = func_dir / "sub-01_task-motor_events.tsv"
        temp_event_file.rename(target)
        return tmp_path

    def test_extract_trial_rts(self, temp_event_file):
        """Test that RTs are extracted and converted to ms."""
        df = extract_trial_rts(temp_event_file)
        
        assert 'rt_ms' in df.columns
        assert 'trial_index' in df.columns
        assert len(df) == 4
        
        # Check conversion (0.5s -> 500ms)
        assert df['rt_ms'].iloc[0] == 500.0
        assert df['rt_ms'].iloc[1] == 600.0

    def test_extract_trial_rts_missing_column(self, tmp_path):
        """Test that extraction fails loudly if RT column is missing."""
        data = {
            'onset': [0.0],
            'duration': [1.0],
            'trial_type': ['normal']
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "sub-01_task-motor_events.tsv"
        df.to_csv(file_path, sep='\t', index=False)

        with pytest.raises(KeyError, match="Could not find 'reaction_time'"):
            extract_trial_rts(file_path)

    def test_process_subject_behavior(self, temp_subject_dir, tmp_path):
        """Test full processing of a subject directory."""
        output_file = tmp_path / "metrics.csv"
        # Setup logging to a temp file to avoid clutter
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)

        success = process_subject_behavior(temp_subject_dir, output_file, logger)
        
        assert success is True
        assert output_file.exists()
        
        result_df = pd.read_csv(output_file)
        assert 'subject_id' in result_df.columns
        assert 'mean_rt' in result_df.columns
        assert result_df['mean_rt'].iloc[0] > 0

    def test_load_valid_subjects(self, tmp_path):
        """Test loading subjects from a text file."""
        valid_file = tmp_path / "valid_subjects.txt"
        valid_file.write_text("sub-01\nsub-02\nsub-03\n")
        
        subjects = load_valid_subjects(valid_file)
        assert subjects == ["sub-01", "sub-02", "sub-03"]

    def test_find_event_tsv_no_func_dir(self, tmp_path):
        """Test finding events when func dir is missing."""
        result = find_event_tsv(tmp_path)
        assert result is None

    def test_find_event_tsv_no_events(self, tmp_path):
        """Test finding events when func dir exists but no events.tsv."""
        func_dir = tmp_path / "func"
        func_dir.mkdir()
        result = find_event_tsv(tmp_path)
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])