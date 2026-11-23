import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest
import time

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from preprocess import setup_logging, log_preprocessing_deviations

class TestPreprocessingLogging:
    """
    Integration tests for preprocessing deviation logging.
    Verifies that deviations are correctly written to preprocessing.log.
    """

    def test_setup_logging_creates_file(self):
        """Test that setup_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_preprocessing.log"
            logger = setup_logging(log_path)
            
            # Log a test message
            logger.info("Test initialization")
            
            # Verify file exists and contains the message
            assert log_path.exists()
            content = log_path.read_text()
            assert "Test initialization" in content

    def test_log_preprocessing_deviations(self):
        """Test that deviations are correctly appended to the log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_preprocessing.log"
            
            # Create initial log content
            log_path.write_text("Initial content\n")
            
            deviations = [
                "Subject sub-01: Docker not available",
                "Subject sub-02: Motion threshold exceeded",
                "Subject sub-03: fmriprep failed"
            ]
            
            log_preprocessing_deviations(log_path, deviations)
            
            content = log_path.read_text()
            assert "Initial content" in content
            
            for dev in deviations:
                assert dev in content
                # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
                assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', content)

    def test_log_preprocessing_deviations_creates_file_if_missing(self):
        """Test that log_preprocessing_deviations creates the file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "new_preprocessing.log"
            
            assert not log_path.exists()
            
            deviations = ["Test deviation"]
            log_preprocessing_deviations(log_path, deviations)
            
            assert log_path.exists()
            content = log_path.read_text()
            assert "Test deviation" in content

    def test_log_format_consistency(self):
        """Test that all log entries follow the expected format."""
        import re
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "format_test.log"
            
            deviations = ["Test 1", "Test 2"]
            log_preprocessing_deviations(log_path, deviations)
            
            content = log_path.read_text()
            lines = content.strip().split('\n')
            
            # Check format: YYYY-MM-DD HH:MM:SS - DEV - message
            pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - DEV - .+'
            for line in lines:
                assert re.match(pattern, line), f"Line does not match format: {line}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])