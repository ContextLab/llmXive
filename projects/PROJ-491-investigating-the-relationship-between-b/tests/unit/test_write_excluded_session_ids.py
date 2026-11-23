"""
Unit tests for T013c: write_excluded_session_ids logic.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.write_excluded_session_ids import write_excluded_subjects_csv, run_validation_if_needed, load_validation_state

class TestWriteExcludedSessionIds:
    def setup_method(self):
        """Setup a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_processed = Path(self.temp_dir) / "data" / "processed"
        self.data_processed.mkdir(parents=True)
        
        # Mock the PROJECT_ROOT behavior for this test
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Cleanup temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_write_empty_list(self):
        """Test writing an empty list of excluded subjects."""
        output_path = self.data_processed / "excluded_session_ids.csv"
        
        write_excluded_subjects_csv([])
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1  # Header only
            assert rows[0] == ['subject_id', 'exclusion_reason']

    def test_write_non_empty_list(self):
        """Test writing a list of excluded subjects."""
        excluded_ids = ["100307", "100408", "100604"]
        output_path = self.data_processed / "excluded_session_ids.csv"
        
        write_excluded_subjects_csv(excluded_ids)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == len(excluded_ids) + 1  # Header + data
            
            # Check header
            assert rows[0] == ['subject_id', 'exclusion_reason']
            
            # Check data
            for i, row in enumerate(rows[1:]):
                assert row[0] == excluded_ids[i]
                assert row[1] == 'session ID mismatch'

    def test_overwrite_existing_file(self):
        """Test that the function overwrites an existing file."""
        output_path = self.data_processed / "excluded_session_ids.csv"
        
        # Write initial data
        write_excluded_subjects_csv(["111111"])
        
        # Write new data
        write_excluded_subjects_csv(["222222"])
        
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[1][0] == "222222"

    def test_validation_state_persistence(self):
        """Test that run_validation_if_needed saves and loads state correctly."""
        # Create a mock state file
        state_file = self.data_processed / ".validation_state.json"
        mock_state = {
            "total_subjects": 10,
            "valid_subjects": ["100307"],
            "excluded_subjects": ["100408"]
        }
        
        with open(state_file, 'w') as f:
            json.dump(mock_state, f)
        
        # Load state
        loaded_state = load_validation_state()
        
        assert loaded_state == mock_state
        assert len(loaded_state["excluded_subjects"]) == 1

    @patch('code.write_excluded_session_ids.fetch_subject_list')
    @patch('code.write_excluded_session_ids.validate_session_distinctness')
    def test_run_validation_if_needed_no_state(self, mock_validate, mock_fetch):
        """Test that validation runs when no state file exists."""
        # Ensure no state file exists
        state_file = self.data_processed / ".validation_state.json"
        if state_file.exists():
            state_file.unlink()
        
        mock_fetch.return_value = ["100307", "100408"]
        mock_validate.return_value = (["100307"], ["100408"])
        
        result = run_validation_if_needed()
        
        assert result["total_subjects"] == 2
        assert result["excluded_subjects"] == ["100408"]
        assert mock_fetch.called
        assert mock_validate.called
        assert state_file.exists()