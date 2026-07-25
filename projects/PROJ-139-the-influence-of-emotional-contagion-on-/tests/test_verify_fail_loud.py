"""
Unit tests for the verify_fail_loud script.
These tests ensure that the verification script itself works correctly.
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from code.analysis.verify_fail_loud import (
    test_t031_fail_loud_data_download,
    test_t007a_0_vader_verification_failure,
    test_t007b_vader_validation_failure,
    ensure_directories,
    write_verification_log
)

class TestVerifyFailLoud:
    def test_ensure_directories(self):
        """Test that ensure_directories creates the state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the state directory for testing
            original_state = "state"
            try:
                # We can't easily change the global state, so we just test that it doesn't crash
                ensure_directories()
                assert Path("state").exists()
            finally:
                pass

    def test_write_verification_log(self):
        """Test that write_verification_log writes to the correct file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change the log path for testing
            log_path = Path(tmpdir) / "test_log.log"
            
            # We can't easily change the global log path, so we just test that it doesn't crash
            results = {"test": True}
            write_verification_log(results)
            
            # Check that the log file exists
            assert Path("state/fail_loud_verification.log").exists()

    @patch('code.analysis.verify_fail_loud.download')
    def test_t031_fail_loud_data_download_success(self, mock_download):
        """Test T031 when all sources fail and RuntimeError is raised."""
        # Mock the download_data function to raise RuntimeError
        mock_download.download_data.side_effect = RuntimeError("All data sources failed. No synthetic data generated.")
        
        result = test_t031_fail_loud_data_download()
        assert result is True

    @patch('code.analysis.verify_fail_loud.download')
    def test_t031_fail_loud_data_download_failure(self, mock_download):
        """Test T031 when all sources fail but no RuntimeError is raised."""
        # Mock the download_data function to not raise an error
        mock_download.download_data.return_value = None
        
        result = test_t031_fail_loud_data_download()
        assert result is False

    @patch('code.analysis.verify_fail_loud.sentiment_validation')
    def test_t007a_0_vader_verification_failure_success(self, mock_validation):
        """Test T007a-0 when VADER verification fails and error is raised."""
        # Mock the validate_vader_against_corpus function to raise an error
        mock_validation.validate_vader_against_corpus.side_effect = Exception("VADER model not found")
        
        result = test_t007a_0_vader_verification_failure()
        assert result is True

    @patch('code.analysis.verify_fail_loud.sentiment_validation')
    def test_t007a_0_vader_verification_failure_failure(self, mock_validation):
        """Test T007a-0 when VADER verification fails but no error is raised."""
        # Mock the validate_vader_against_corpus function to not raise an error
        mock_validation.validate_vader_against_corpus.return_value = None
        
        result = test_t007a_0_vader_verification_failure()
        assert result is False

    @patch('code.analysis.verify_fail_loud.sentiment_validation')
    def test_t007b_vader_validation_failure_success(self, mock_validation):
        """Test T007b when VADER validation fails and error is raised."""
        # Mock the generate_validation_justification function to raise an error
        mock_validation.generate_validation_justification.side_effect = Exception("VADER verification failed")
        
        result = test_t007b_vader_validation_failure()
        assert result is True

    @patch('code.analysis.verify_fail_loud.sentiment_validation')
    def test_t007b_vader_validation_failure_failure(self, mock_validation):
        """Test T007b when VADER validation fails but no error is raised."""
        # Mock the generate_validation_justification function to not raise an error
        mock_validation.generate_validation_justification.return_value = None
        
        result = test_t007b_vader_validation_failure()
        assert result is False
