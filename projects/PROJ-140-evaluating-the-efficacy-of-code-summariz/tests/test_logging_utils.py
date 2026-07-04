import unittest
import logging
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_utils import setup_logging, get_logger, ErrorHandler

class TestLoggingUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory for log files during tests."""
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.test_dir, "test_logs")
        
        # Reset logger state for each test to avoid handler duplication issues
        # We do this by removing handlers from the root logger
        root_logger = logging.getLogger("llmXive")
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)
        # Also clear any child loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith("llmXive"):
                del logging.Logger.manager.loggerDict[name]

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates console and file handlers."""
        logger = setup_logging(
            log_level=logging.INFO,
            log_dir=self.log_dir,
            log_file="test.log"
        )
        
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 2) # Console + File
        
        # Check file handler exists and file is created
        file_handler = None
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler):
                file_handler = h
                break
        
        self.assertIsNotNone(file_handler)
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, "test.log")))

    def test_setup_logging_default_log_file(self):
        """Test that setup_logging creates a timestamped log file if none provided."""
        logger = setup_logging(
            log_level=logging.DEBUG,
            log_dir=self.log_dir
        )
        
        self.assertEqual(logger.level, logging.DEBUG)
        
        # Find the file handler
        file_handler = None
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler):
                file_handler = h
                break
        
        self.assertIsNotNone(file_handler)
        # Verify file exists (name should start with llmXive_)
        log_files = os.listdir(self.log_dir)
        self.assertTrue(any(f.startswith("llmXive_") and f.endswith(".log") for f in log_files))

    def test_get_logger_creates_child(self):
        """Test that get_logger creates a child logger with the correct name."""
        setup_logging(log_dir=self.log_dir)
        
        child_logger = get_logger("test_module")
        
        self.assertEqual(child_logger.name, "llmXive.test_module")
        self.assertIsInstance(child_logger, logging.Logger)
        
        # Verify it has the same handlers as the root (inherited) or its own
        # Since we set up root, child should inherit or be set up
        self.assertTrue(len(child_logger.handlers) > 0)

    def test_error_handler_handle_error(self):
        """Test that ErrorHandler.handle_error logs the exception correctly."""
        setup_logging(log_dir=self.log_dir, log_file="error_test.log")
        logger = get_logger()
        
        try:
            raise ValueError("Test error message")
        except Exception as e:
            ErrorHandler.handle_error(e, context="test_context")
        
        # Verify log file contains the error
        log_path = os.path.join(self.log_dir, "error_test.log")
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("Error in test_context", content)
        self.assertIn("Test error message", content)
        self.assertIn("ValueError", content)

    def test_error_handler_handle_critical_error(self):
        """Test that ErrorHandler.handle_critical_error logs and re-raises."""
        setup_logging(log_dir=self.log_dir, log_file="critical_test.log")
        
        try:
            ErrorHandler.handle_critical_error(RuntimeError("Critical failure"), "critical_context")
            self.fail("Expected RuntimeError to be raised")
        except RuntimeError as e:
            self.assertEqual(str(e), "Critical failure")
        
        log_path = os.path.join(self.log_dir, "critical_test.log")
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("CRITICAL ERROR in critical_context", content)

    def test_error_handler_log_warning(self):
        """Test that ErrorHandler.log_warning logs a warning."""
        setup_logging(log_dir=self.log_dir, log_file="warning_test.log")
        
        ErrorHandler.log_warning("This is a warning", "warning_context")
        
        log_path = os.path.join(self.log_dir, "warning_test.log")
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("warning_context: This is a warning", content)
        self.assertIn("WARNING", content)

    def test_no_duplicate_handlers(self):
        """Test that calling setup_logging multiple times does not duplicate handlers."""
        logger1 = setup_logging(log_dir=self.log_dir, log_file="dup_test.log")
        initial_count = len(logger1.handlers)
        
        logger2 = setup_logging(log_dir=self.log_dir, log_file="dup_test.log")
        
        self.assertEqual(len(logger2.handlers), initial_count)
        self.assertEqual(logger1, logger2)

if __name__ == '__main__':
    unittest.main()