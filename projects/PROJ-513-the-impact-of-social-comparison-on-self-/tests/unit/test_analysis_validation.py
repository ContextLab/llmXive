import pytest
import pandas as pd
import numpy as np
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import (
    validate_completeness, 
    validate_participant_count, 
    MIN_COMPLETENESS, 
    MIN_PARTICIPANTS,
    PROCESSED_DATA_DIR
)

class TestValidateCompleteness:
    def test_passes_with_high_completeness(self):
        """Test that validation passes when all rows are complete."""
        data = {
            'BISS_score': [1.0, 2.0, 3.0],
            'INCOM_score': [10, 20, 30],
            'usage_frequency': [1.5, 2.5, 3.5],
            'is_complete': [True, True, True],
            'origin': ['AI', 'Human', 'AI']
        }
        df = pd.DataFrame(data)
        
        # Should not raise
        result = validate_completeness(df)
        assert result is True

    def test_fails_with_low_completeness(self):
        """Test that validation raises SystemExit when completeness < 95%."""
        # Create a row with 0% completeness (all NaN/empty in check cols)
        # We have 5 check cols. If 1 is missing, 4/5 = 80% < 95%
        data = {
            'BISS_score': [1.0, np.nan, 3.0],
            'INCOM_score': [10, np.nan, 30],
            'usage_frequency': [1.5, np.nan, 3.5],
            'is_complete': [True, np.nan, True],
            'origin': ['AI', np.nan, 'AI']
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_completeness(df)
        
        assert excinfo.value.code == 1

    def test_handles_empty_strings_as_missing(self):
        """Test that empty strings are treated as missing values."""
        data = {
            'BISS_score': [1.0, "", 3.0],
            'INCOM_score': [10, "", 30],
            'usage_frequency': [1.5, "", 3.5],
            'is_complete': [True, "", True],
            'origin': ['AI', "", 'AI']
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_completeness(df)
        
        assert excinfo.value.code == 1

class TestValidateParticipantCount:
    def test_passes_with_enough_participants(self):
        """Test that validation passes when N >= 150."""
        # Create 150 unique participants
        participant_ids = [f"P{i}" for i in range(150)]
        data = {
            'participant_id': participant_ids,
            'BISS_score': [1.0] * 150
        }
        df = pd.DataFrame(data)
        
        result = validate_participant_count(df)
        assert result is True

    def test_fails_with_insufficient_participants(self):
        """Test that validation raises SystemExit when N < 150."""
        # Create 149 unique participants
        participant_ids = [f"P{i}" for i in range(149)]
        data = {
            'participant_id': participant_ids,
            'BISS_score': [1.0] * 149
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(SystemExit) as excinfo:
            validate_participant_count(df)
        
        assert excinfo.value.code == 1

class TestLoadProcessedData:
    @patch('analysis.PROCESSED_DATA_DIR', Path('/tmp/mock_processed'))
    def test_raises_if_file_missing(self):
        """Test that load_processed_data raises FileNotFoundError if file doesn't exist."""
        from analysis import load_processed_data
        import shutil
        
        # Create temp dir
        temp_dir = Path('/tmp/mock_processed')
        temp_dir.mkdir(exist_ok=True)
        
        # Ensure file does not exist
        (temp_dir / "cleaned_sessions.jsonl").unlink(missing_ok=True)
        
        with pytest.raises(FileNotFoundError):
            load_processed_data()
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @patch('analysis.PROCESSED_DATA_DIR', Path('/tmp/mock_processed_valid'))
    def test_loads_valid_jsonl(self):
        """Test that load_processed_data correctly loads a valid JSONL file."""
        from analysis import load_processed_data
        import shutil
        
        temp_dir = Path('/tmp/mock_processed_valid')
        temp_dir.mkdir(exist_ok=True)
        
        # Create a valid JSONL file
        data = [
            {"stimulus_id": "S1", "origin": "AI", "BISS_score": 1.0, "participant_id": "P1", "INCOM_score": 10, "usage_frequency": 1.5, "is_complete": True},
            {"stimulus_id": "S2", "origin": "Human", "BISS_score": 2.0, "participant_id": "P1", "INCOM_score": 10, "usage_frequency": 1.5, "is_complete": True}
        ]
        
        file_path = temp_dir / "cleaned_sessions.jsonl"
        with open(file_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        try:
            df = load_processed_data()
            assert len(df) == 2
            assert list(df.columns) == ['stimulus_id', 'origin', 'BISS_score', 'participant_id', 'INCOM_score', 'usage_frequency', 'is_complete']
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
