import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import validate_and_aggregate, _log_pipeline_error
from config import get_sample_limit

class TestHaltOnZeroValidSubjects:
    """
    Tests for T014c: Halt on Zero Valid Subjects.
    Verifies that the system raises a ValueError with the exact error message
    when no valid subjects with Fluid Intelligence scores are found.
    """

    def test_raises_value_error_on_zero_valid_subjects(self):
        """
        Verify that validate_and_aggregate raises ValueError with the exact message
        when no valid subjects are found.
        """
        # Mock the data directory structure
        mock_data_dir = Path("/mock/data/raw")
        mock_output_dir = Path("/mock/data/processed")
        
        # Mock the validate_and_aggregate from validate_fluid_intelligence
        # to return a result with count=0
        with patch('download.validate_and_aggregate') as mock_validate, \
             patch('download.get_dataset_ids', return_value=['ds000224']), \
             patch('download.get_subject_list', return_value=['sub-01', 'sub-02']), \
             patch('download.enforce_sample_limit', return_value=['sub-01', 'sub-02']), \
             patch('pathlib.Path.mkdir'):
            
            # Simulate zero valid subjects
            mock_validate.return_value = {
                "subjects": [],
                "count": 0
            }
            
            # The function should raise ValueError with the specific message
            with pytest.raises(ValueError) as excinfo:
                validate_and_aggregate(mock_data_dir, mock_output_dir, get_sample_limit())
            
            assert str(excinfo.value) == "No valid Fluid Intelligence data found in specified datasets"

    def test_logs_error_to_pipeline_errors_log(self):
        """
        Verify that when zero valid subjects are found, an error is logged to
        data/processed/pipeline_errors.log.
        """
        mock_data_dir = Path("/mock/data/raw")
        mock_output_dir = Path("/mock/data/processed")
        log_path = mock_output_dir / "pipeline_errors.log"
        
        # Mock file writing to capture the log content
        written_content = []
        
        def mock_file_write(self, content):
            written_content.append(content)
            return MagicMock(__enter__=lambda s: s, __exit__=lambda s, t, v, tb: None)
        
        with patch('download.validate_and_aggregate') as mock_validate, \
             patch('download.get_dataset_ids', return_value=['ds000224']), \
             patch('download.get_subject_list', return_value=['sub-01']), \
             patch('download.enforce_sample_limit', return_value=['sub-01']), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_validate.return_value = {"subjects": [], "count": 0}
            
            with pytest.raises(ValueError):
                validate_and_aggregate(mock_data_dir, mock_output_dir, get_sample_limit())
            
            # Verify that open was called with the log file path
            # and that the file was written to
            assert mock_file.called

    def test_error_message_exact_match(self):
        """
        Verify the error message matches the specification exactly:
        "No valid Fluid Intelligence data found in specified datasets"
        """
        expected_message = "No valid Fluid Intelligence data found in specified datasets"
        
        mock_data_dir = Path("/mock/data/raw")
        mock_output_dir = Path("/mock/data/processed")
        
        with patch('download.validate_and_aggregate') as mock_validate, \
             patch('download.get_dataset_ids', return_value=['ds000224']), \
             patch('download.get_subject_list', return_value=['sub-01']), \
             patch('download.enforce_sample_limit', return_value=['sub-01']), \
             patch('pathlib.Path.mkdir'):
            
            mock_validate.return_value = {"subjects": [], "count": 0}
            
            with pytest.raises(ValueError) as excinfo:
                validate_and_aggregate(mock_data_dir, mock_output_dir, get_sample_limit())
            
            assert str(excinfo.value) == expected_message

    def test_halt_logic_integration(self):
        """
        Integration test: Verify the full flow from data directory to halt.
        """
        mock_data_dir = Path("/mock/data/raw")
        mock_output_dir = Path("/mock/data/processed")
        
        # Simulate a scenario where subjects exist but none have valid scores
        with patch('download.validate_and_aggregate') as mock_validate, \
             patch('download.get_dataset_ids', return_value=['ds000224']), \
             patch('download.get_subject_list', return_value=['sub-01', 'sub-02', 'sub-03']), \
             patch('download.enforce_sample_limit', return_value=['sub-01', 'sub-02']), \
             patch('pathlib.Path.mkdir'):
            
            mock_validate.return_value = {
                "subjects": [],
                "count": 0,
                "reason": "No Fluid Intelligence scores found"
            }
            
            with pytest.raises(ValueError) as excinfo:
                validate_and_aggregate(mock_data_dir, mock_output_dir, get_sample_limit())
            
            assert "No valid Fluid Intelligence data found in specified datasets" in str(excinfo.value)