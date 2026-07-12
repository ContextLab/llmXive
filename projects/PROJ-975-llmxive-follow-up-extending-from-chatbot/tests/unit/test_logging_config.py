"""
Unit tests for logging_config.py (T007).

Verifies:
1. The logger configuration writes to the correct CSV path.
2. A log entry is written successfully.
3. The file exists after writing.
"""
import os
import csv
import json
import tempfile
import shutil
import pytest
from datetime import datetime

# We need to temporarily override the module-level constants to use a temp directory
# to avoid polluting the project data directory during tests.
import code.logging_config as logging_config

class TestLoggingConfig:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup a temporary directory for logs and teardown afterwards.
        We monkeypatch the module's constants for the duration of the test.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_results_dir = logging_config.RESULTS_DIR
        self.original_log_file_path = logging_config.LOG_FILE_PATH
        
        logging_config.RESULTS_DIR = self.temp_dir
        logging_config.LOG_FILE_PATH = os.path.join(self.temp_dir, "experiment_log.csv")
        
        yield
        
        # Restore original values
        logging_config.RESULTS_DIR = self.original_results_dir
        logging_config.LOG_FILE_PATH = self.original_log_file_path
        
        # Cleanup temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_writes_to_csv(self):
        """Test that get_logger creates a CSV file and writes a record."""
        # Clear any existing handlers to ensure clean state
        logger = logging_config.get_logger("test_logger")
        # Remove handlers to force re-creation with new path
        logger.handlers.clear()
        
        # Re-get logger to ensure it picks up the monkeypatched path
        logger = logging_config.get_logger("test_logger")
        
        test_msg = "Test log entry for T007 verification"
        logger.info(test_msg)
        
        # Verify file existence
        assert os.path.exists(logging_config.LOG_FILE_PATH), "Log file was not created."
        
        # Verify content
        with open(logging_config.LOG_FILE_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) >= 1, "No rows were written to the CSV."
        
        last_row = rows[-1]
        assert last_row['level'] == 'INFO'
        assert test_msg in last_row['message']
        assert 'timestamp' in last_row
        assert 'metadata_json' in last_row

    def test_log_experiment_entry_structure(self):
        """Test that log_experiment_entry writes all required fields."""
        logger = logging_config.get_logger("test_entry_logger")
        logger.handlers.clear()
        logger = logging_config.get_logger("test_entry_logger")
        
        logging_config.log_experiment_entry(
            task_id="T007-TEST",
            success=True,
            latency=0.123,
            tokens=100,
            retrieval_precision=0.85,
            retrieval_diversity=0.45,
            pruning_risk_count=0,
            library_size=10,
            pruning_enabled=False
        )
        
        assert os.path.exists(logging_config.LOG_FILE_PATH)
        
        with open(logging_config.LOG_FILE_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) >= 1
        last_row = rows[-1]
        
        # Verify metadata JSON contains the keys
        metadata = json.loads(last_row['metadata_json'])
        assert metadata['task_id'] == 'T007-TEST'
        assert metadata['success'] is True
        assert abs(metadata['latency'] - 0.123) < 0.001
        assert metadata['tokens'] == 100
        assert abs(metadata['retrieval_precision'] - 0.85) < 0.01
        assert metadata['library_size'] == 10
        assert metadata['pruning_enabled'] is False

    def test_verify_log_file_exists(self):
        """Test the verify_log_file_exists helper function."""
        # Initially file shouldn't exist if we just cleared handlers and haven't logged
        # But to be safe, let's log one entry first
        logger = logging_config.get_logger("verify_logger")
        logger.handlers.clear()
        logger = logging_config.get_logger("verify_logger")
        logger.info("Initial log")
        
        assert logging_config.verify_log_file_exists() is True
        
        # Remove the file manually to test False case
        if os.path.exists(logging_config.LOG_FILE_PATH):
            os.remove(logging_config.LOG_FILE_PATH)
            
        assert logging_config.verify_log_file_exists() is False
