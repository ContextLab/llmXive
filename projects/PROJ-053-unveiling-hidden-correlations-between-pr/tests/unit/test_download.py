"""
Unit tests for manual data placement validation in T014A.

This test validates that the download module correctly checks for the existence
of the raw data file and raises a SystemExit with the expected error message
when the file is missing.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import check_data_availability, main
from code.config import get_raw_data_dir, get_project_root


class TestManualDataPlacementValidation:
    """Tests for the manual data placement validation logic."""
    
    def test_data_exists_no_exception(self):
        """Test that no exception is raised when data file exists."""
        # Create a temporary directory structure for testing
        test_root = Path(__file__).parent.parent.parent
        test_raw_dir = test_root / "data" / "raw"
        test_raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy data file
        dummy_file = test_raw_dir / "am_data.csv"
        dummy_file.touch()
        
        try:
            # This should NOT raise an exception
            check_data_availability()
        except SystemExit:
            pytest.fail("check_data_availability() raised SystemExit when data file exists")
        finally:
            # Cleanup
            if dummy_file.exists():
                dummy_file.unlink()
    
    def test_data_missing_raises_system_exit(self):
        """Test that SystemExit is raised when data file is missing."""
        # Ensure the file does not exist
        test_root = Path(__file__).parent.parent.parent
        test_raw_dir = test_root / "data" / "raw"
        test_raw_dir.mkdir(parents=True, exist_ok=True)
        
        dummy_file = test_raw_dir / "am_data.csv"
        if dummy_file.exists():
            dummy_file.unlink()
        
        # Mock sys.exit to capture the exit call
        with patch('sys.exit') as mock_exit:
            check_data_availability()
            
            # Verify sys.exit was called
            mock_exit.assert_called_once()
            
            # Get the error message passed to sys.exit
            call_args = mock_exit.call_args
            exit_code = call_args[0][0] if call_args[0] else call_args[1].get('code', 1)
            
            # Verify exit code is 1 (failure)
            assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    
    def test_error_message_content(self):
        """Test that the error message contains the expected content."""
        # Ensure the file does not exist
        test_root = Path(__file__).parent.parent.parent
        test_raw_dir = test_root / "data" / "raw"
        test_raw_dir.mkdir(parents=True, exist_ok=True)
        
        dummy_file = test_raw_dir / "am_data.csv"
        if dummy_file.exists():
            dummy_file.unlink()
        
        # Capture the log output to verify error message
        import logging
        from io import StringIO
        
        # Create a string buffer to capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.CRITICAL)
        
        # Get the logger used by download module
        import code.data.download as download_module
        original_logger = download_module.logger
        
        # Replace logger with one that captures output
        test_logger = logging.getLogger('test_download_logger')
        test_logger.setLevel(logging.CRITICAL)
        test_logger.addHandler(handler)
        download_module.logger = test_logger
        
        try:
            with patch('sys.exit'):
                check_data_availability()
        finally:
            # Restore original logger
            download_module.logger = original_logger
            test_logger.removeHandler(handler)
        
        # Get the logged message
        log_output = log_capture.getvalue()
        
        # Verify expected content in error message
        assert "Manual data placement required" in log_output, \
            f"Expected 'Manual data placement required' in log message, got: {log_output}"
        assert "data/raw/am_data.csv" in log_output, \
            f"Expected 'data/raw/am_data.csv' in log message, got: {log_output}"
        assert "not found" in log_output, \
            f"Expected 'not found' in log message, got: {log_output}"
    
    def test_main_function_raises_system_exit_on_missing_data(self):
        """Test that main() also raises SystemExit when data is missing."""
        # Ensure the file does not exist
        test_root = Path(__file__).parent.parent.parent
        test_raw_dir = test_root / "data" / "raw"
        test_raw_dir.mkdir(parents=True, exist_ok=True)
        
        dummy_file = test_raw_dir / "am_data.csv"
        if dummy_file.exists():
            dummy_file.unlink()
        
        # Mock sys.exit to capture the exit call
        with patch('sys.exit') as mock_exit:
            main()
            
            # Verify sys.exit was called
            mock_exit.assert_called_once()
            
            # Get the error message passed to sys.exit
            call_args = mock_exit.call_args
            exit_code = call_args[0][0] if call_args[0] else call_args[1].get('code', 1)
            
            # Verify exit code is 1 (failure)
            assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    
    def test_error_message_format_matches_specification(self):
        """Test that the error message format matches the specification in T014A."""
        # Ensure the file does not exist
        test_root = Path(__file__).parent.parent.parent
        test_raw_dir = test_root / "data" / "raw"
        test_raw_dir.mkdir(parents=True, exist_ok=True)
        
        dummy_file = test_raw_dir / "am_data.csv"
        if dummy_file.exists():
            dummy_file.unlink()
        
        # Capture the log output
        import logging
        from io import StringIO
        
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.CRITICAL)
        
        import code.data.download as download_module
        original_logger = download_module.logger
        
        test_logger = logging.getLogger('test_download_logger_format')
        test_logger.setLevel(logging.CRITICAL)
        test_logger.addHandler(handler)
        download_module.logger = test_logger
        
        try:
            with patch('sys.exit'):
                check_data_availability()
        finally:
            download_module.logger = original_logger
            test_logger.removeHandler(handler)
        
        log_output = log_capture.getvalue()
        
        # Check for the exact message format specified in T014A
        expected_message = "Manual data placement required: `data/raw/am_data.csv` not found. Please place the dataset file manually."
        
        # The log message should contain the key components
        assert "Manual data placement required" in log_output
        assert "data/raw/am_data.csv" in log_output
        assert "not found" in log_output
        assert "Please place the dataset file manually" in log_output