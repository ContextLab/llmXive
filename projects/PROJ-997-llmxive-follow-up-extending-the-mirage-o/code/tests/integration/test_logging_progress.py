import pytest
import logging
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from src.config.logging_config import setup_logger, log_sample_progress, LOG_FILE

class TestT017LoggingProgress:
    """
    Integration test for T017: Add logging for data generation progress.
    
    Verifies that:
    1. logs/pipeline.log is created.
    2. Entries are in JSON lines format.
    3. Each entry contains sample_id, status, and optionally error_code.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        # Setup: Create a temporary log directory and file for testing
        self.temp_log_dir = tmp_path / "logs"
        self.temp_log_dir.mkdir()
        self.temp_log_file = self.temp_log_dir / "pipeline.log"
        
        # Patch the LOG_FILE constant in logging_config
        with patch('src.config.logging_config.LOG_FILE', self.temp_log_file):
            yield
        
        # Cleanup: Remove temp log file if it exists
        if self.temp_log_file.exists():
            self.temp_log_file.unlink()

    def test_log_sample_progress_success(self):
        """Test logging a successful sample processing."""
        logger = setup_logger("test_success")
        
        sample_id = "sample_123"
        log_sample_progress(logger, sample_id, "success")
        
        assert self.temp_log_file.exists()
        
        with open(self.temp_log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        log_entry = json.loads(lines[0])
        
        assert log_entry['sample_id'] == sample_id
        assert log_entry['status'] == 'success'
        assert 'error_code' not in log_entry or log_entry.get('error_code') is None
        assert 'message' in log_entry

    def test_log_sample_progress_error(self):
        """Test logging an error sample processing with error_code."""
        logger = setup_logger("test_error")
        
        sample_id = "sample_456"
        error_code = "INFERENCE_ERROR_Timeout"
        
        log_sample_progress(logger, sample_id, "error", error_code=error_code)
        
        with open(self.temp_log_file, 'r') as f:
            lines = f.readlines()
        
        # Should append to existing log
        assert len(lines) >= 1
        
        # Check the last line
        log_entry = json.loads(lines[-1])
        
        assert log_entry['sample_id'] == sample_id
        assert log_entry['status'] == 'error'
        assert log_entry['error_code'] == error_code

    def test_log_sample_progress_skipped(self):
        """Test logging a skipped sample processing."""
        logger = setup_logger("test_skipped")
        
        sample_id = "sample_789"
        error_code = "INFERENCE_SKIPPED_INT4"
        
        log_sample_progress(logger, sample_id, "skipped", error_code=error_code)
        
        with open(self.temp_log_file, 'r') as f:
            lines = f.readlines()
        
        log_entry = json.loads(lines[-1])
        
        assert log_entry['sample_id'] == sample_id
        assert log_entry['status'] == 'skipped'
        assert log_entry['error_code'] == error_code

    def test_json_lines_format(self):
        """Verify that the log file is valid JSON Lines."""
        logger = setup_logger("test_format")
        
        log_sample_progress(logger, "id1", "success")
        log_sample_progress(logger, "id2", "error", error_code="ERR")
        
        with open(self.temp_log_file, 'r') as f:
            for line in f:
                # Each line must be valid JSON
                json.loads(line)