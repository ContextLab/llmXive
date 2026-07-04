import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path for imports
code_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging_utils import get_logger, LOG_FILE, LOG_DIR, MAX_BYTES, BACKUP_COUNT
from logging.handlers import RotatingFileHandler

class TestLoggingUtils:
    def setup_method(self):
        # Create a temporary directory for logs during testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = LOG_DIR
        self.original_log_file = LOG_FILE
        
        # Override global paths for testing
        import utils.logging_utils
        utils.logging_utils.LOG_DIR = Path(self.temp_dir)
        utils.logging_utils.LOG_FILE = utils.logging_utils.LOG_DIR / "pipeline.log"
        
        # Reset logger cache
        utils.logging_utils._logger = None

    def teardown_method(self):
        # Restore original paths
        import utils.logging_utils
        utils.logging_utils.LOG_DIR = self.original_log_dir
        utils.logging_utils.LOG_FILE = self.original_log_file
        utils.logging_utils._logger = None
        
        # Cleanup temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_creation(self):
        """Test that a logger is created successfully."""
        logger = get_logger("test_pipeline")
        assert logger is not None
        assert logger.name == "test_pipeline"
        assert logger.level == 20  # INFO

    def test_log_file_exists(self):
        """Test that the log file is created after logging."""
        logger = get_logger("test_file_creation")
        logger.info("Test message to create file")
        
        # Force flush
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.flush()
                handler.close()

        assert utils.logging_utils.LOG_FILE.exists()

    def test_rotation_config(self):
        """Test that the handler is configured with correct rotation limits."""
        logger = get_logger("test_rotation")
        
        handler_found = False
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler_found = True
                assert handler.maxBytes == MAX_BYTES
                assert handler.backupCount == BACKUP_COUNT
                break
        
        assert handler_found, "RotatingFileHandler not found in logger handlers"

    def test_disk_usage_limit(self):
        """Verify that the configured limits ensure disk usage stays under 14GB."""
        # Max files = BACKUP_COUNT + 1
        # Max total size = MAX_BYTES * (BACKUP_COUNT + 1)
        max_total_size = MAX_BYTES * (BACKUP_COUNT + 1)
        limit_14gb = 14 * 1024 * 1024 * 1024
        
        assert max_total_size <= limit_14gb, \
            f"Configured max disk usage ({max_total_size} bytes) exceeds 14GB limit ({limit_14gb} bytes)"