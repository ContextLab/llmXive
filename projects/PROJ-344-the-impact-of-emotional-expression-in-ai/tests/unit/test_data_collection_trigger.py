"""
Unit tests for code/data_collection_trigger.py
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.data_collection_trigger import check_data_availability, trigger_controlled_collection
from code.logging_config import setup_logging

# Setup logging for tests to avoid errors
setup_logging()

def test_check_data_availability_empty():
    """Test that check_data_availability returns False when directories are empty."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project_root to point to our temp dir
        # We need to patch the os.path calls inside the function or the module
        # Since the module calculates project_root relative to itself, we can't easily mock it
        # without refactoring. Instead, we test the logic by manipulating the actual file system
        # if the test runs in the context of the project, or we mock the os.path.exists calls.

        # For this unit test, we will mock the os.path functions
        with patch('code.data_collection_trigger.os.path.exists', return_value=False):
            with patch('code.data_collection_trigger.os.listdir', return_value=[]):
                result = check_data_availability()
                assert result is False

def test_check_data_availability_has_processed():
    """Test that check_data_availability returns True if processed data exists."""
    with patch('code.data_collection_trigger.os.path.exists') as mock_exists:
        with patch('code.data_collection_trigger.os.listdir') as mock_listdir:
            # First call (processed_dir) returns True, listdir returns a file
            mock_exists.side_effect = [True, True] # processed_dir exists, then check raw
            mock_listdir.return_value = ['features.csv']

            result = check_data_availability()
            assert result is True

def test_check_data_availability_has_raw():
    """Test that check_data_availability returns True if raw data exists."""
    with patch('code.data_collection_trigger.os.path.exists') as mock_exists:
        with patch('code.data_collection_trigger.os.listdir') as mock_listdir:
            # First call (processed_dir) returns True, listdir returns empty
            # Second call (raw_dir) returns True, listdir returns a file
            mock_exists.side_effect = [True, True, True] # processed exists, processed listdir, raw exists
            mock_listdir.side_effect = [[], ['raw_data.csv']]

            result = check_data_availability()
            assert result is True

def test_trigger_controlled_collection_exits():
    """Test that trigger_controlled_collection logs and exits."""
    with patch('code.data_collection_trigger.logger') as mock_logger:
        with patch('code.data_collection_trigger.sys.exit') as mock_exit:
            with patch('code.data_collection_trigger.log_state_event'):
                trigger_controlled_collection()
                assert mock_logger.critical.called
                assert mock_exit.called
                assert mock_exit.call_args[0][0] == 66