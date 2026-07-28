"""
Unit tests for utils/logging.py
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

# We need to ensure the code directory is in the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.logging import (
    get_log_path,
    init_cycle_logger,
    update_cycle_log,
    checkpoint_model_state,
    log_cycle_summary,
    get_cycle_history,
    log_error,
    log_warning,
    LOG_DIR,
    HISTORY_FILE,
    CHECKPOINT_DIR
)

class TestLogging(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Mock config to point to temp dirs if needed, but we use hardcoded relative paths
        # which will resolve to the temp dir.
        # Ensure the config.py uses the temp dir or we mock get_config
        # For simplicity, we rely on the fact that we are in a temp dir and paths are relative.
        # We will manually clean up the files created by the functions.

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_log_path(self):
        """Test that get_log_path constructs the correct path."""
        path = get_log_path(1)
        self.assertEqual(path, os.path.join(LOG_DIR, "cycle_1.log"))
        self.assertTrue(os.path.exists(LOG_DIR)) # Should create the dir

    def test_init_cycle_logger(self):
        """Test that init_cycle_logger creates a logger with handlers."""
        logger = init_cycle_logger(1)
        self.assertEqual(logger.name, "cycle_1")
        self.assertGreater(len(logger.handlers), 0)

    def test_update_cycle_log(self):
        """Test that update_cycle_log writes to the log file."""
        log_path = get_log_path(1)
        init_cycle_logger(1) # Ensure file exists
        update_cycle_log(1, "test_key", "test_value")

        with open(log_path, 'r') as f:
            content = f.read()
        self.assertIn("test_key: test_value", content)

    @patch('utils.logging.torch')
    def test_checkpoint_model_state(self, mock_torch):
        """Test that checkpoint_model_state saves a file."""
        mock_state = {"key": "value"}
        mock_torch.save = MagicMock()

        path = checkpoint_model_state(1, mock_state)
        self.assertTrue(path.endswith(".pt"))
        mock_torch.save.assert_called_once()

    def test_log_cycle_summary(self):
        """Test that log_cycle_summary updates history file."""
        metrics = {"loss": 0.5, "acc": 0.9}
        log_cycle_summary(1, metrics)

        self.assertTrue(os.path.exists(HISTORY_FILE))
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["cycle_number"], 1)
        self.assertEqual(history[0]["metrics"]["loss"], 0.5)

    def test_get_cycle_history_empty(self):
        """Test get_cycle_history returns empty list when no file exists."""
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        history = get_cycle_history()
        self.assertEqual(history, [])

    def test_log_error(self):
        """Test log_error writes to log file."""
        log_path = get_log_path(1)
        init_cycle_logger(1)
        log_error(1, "Test error")

        with open(log_path, 'r') as f:
            content = f.read()
        self.assertIn("ERROR: Test error", content)

    def test_log_warning(self):
        """Test log_warning writes to log file."""
        log_path = get_log_path(1)
        init_cycle_logger(1)
        log_warning(1, "Test warning")

        with open(log_path, 'r') as f:
            content = f.read()
        self.assertIn("WARNING: Test warning", content)

if __name__ == '__main__':
    unittest.main()