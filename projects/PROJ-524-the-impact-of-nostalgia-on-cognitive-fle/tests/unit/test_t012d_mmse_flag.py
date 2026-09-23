import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t012d_mmse_flag import load_score_filtered_dataset, validate_mmse_presence, save_mmse_flag

class TestMMSEFlag:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_validate_mmse_present_and_valid(self, temp_dir):
        """Test case where MMSE column exists and has valid values."""
        data = {
            'participant_id': [1, 2, 3],
            'MMSE': [28, 25, 29],
            'score': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        assert validate_mmse_presence(df) is True

    def test_validate_mmse_column_missing(self, temp_dir):
        """Test case where MMSE column does not exist."""
        data = {
            'participant_id': [1, 2, 3],
            'score': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        assert validate_mmse_presence(df) is False

    def test_validate_mmse_all_null(self, temp_dir):
        """Test case where MMSE column exists but all values are null."""
        data = {
            'participant_id': [1, 2, 3],
            'MMSE': [None, None, None],
            'score': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        assert validate_mmse_presence(df) is False

    def test_validate_mmse_some_null(self, temp_dir):
        """Test case where MMSE column exists with some nulls but at least one valid."""
        data = {
            'participant_id': [1, 2, 3],
            'MMSE': [None, 25, None],
            'score': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        assert validate_mmse_presence(df) is True

    def test_save_mmse_flag(self, temp_dir):
        """Test saving the mmse flag to JSON."""
        output_path = os.path.join(temp_dir, "mmse_flag.json")
        
        save_mmse_flag(True, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['has_mmse'] is True
        assert 'timestamp' in data
