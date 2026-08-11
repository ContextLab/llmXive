"""
Unit tests for utils/logging.py structured logging functionality.
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, PropertyMock

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
    log_warning
)
from config import get_config, PathConfig


class MockConfig:
    """Mock config for testing without full config initialization."""
    class MockPathConfig:
        logs_dir = ""
        checkpoints_dir = ""

    path_config = MockPathConfig()


class TestLogging(unittest.TestCase):
    """Test suite for logging utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.logs_dir = os.path.join(self.test_dir, "logs")
        self.checkpoints_dir = os.path.join(self.test_dir, "checkpoints")
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)

        # Mock config paths
        self.original_config = None
        try:
            from config import get_config
            self.original_config = get_config()
        except:
            pass

        # Patch config
        mock_path_config = MagicMock()
        mock_path_config.logs_dir = self.logs_dir
        mock_path_config.checkpoints_dir = self.checkpoints_dir

        mock_config = MagicMock()
        mock_config.path_config = mock_path_config

        self.config_patcher = patch('utils.logging.get_config', return_value=mock_config)
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_log_path(self):
        """Test that get_log_path generates correct file paths."""
        path = get_log_path(1)
        self.assertTrue(path.endswith("cycle_1.log"))
        self.assertTrue(os.path.dirname(path).startswith(self.logs_dir))

    def test_init_cycle_logger_creates_file(self):
        """Test that init_cycle_logger creates a log file."""
        logger = init_cycle_logger(1)
        log_path = get_log_path(1)
        self.assertTrue(os.path.exists(log_path))

    def test_update_cycle_log_writes_json(self):
        """Test that update_cycle_log writes structured JSON entries."""
        logger = init_cycle_logger(1)
        update_cycle_log(1, "test_event", {"metric": 0.95}, logger)

        log_path = get_log_path(1)
        with open(log_path, 'r') as f:
            content = f.read().strip()
            entry = json.loads(content)

        self.assertEqual(entry["event"], "test_event")
        self.assertEqual(entry["metrics"]["metric"], 0.95)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["level"], "INFO")

    def test_checkpoint_model_state_saves_file(self):
        """Test that checkpoint_model_state saves model state."""
        model_state = {
            "weights": {"layer1": [1.0, 2.0]},
            "cycle": 1,
            "param_count": 124000000
        }
        path = checkpoint_model_state(1, model_state)

        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            saved_state = json.load(f)

        self.assertEqual(saved_state["cycle"], 1)
        self.assertEqual(saved_state["param_count"], 124000000)

    def test_log_cycle_summary(self):
        """Test log_cycle_summary writes summary data."""
        summary = {
            "status": "completed",
            "duration_seconds": 120.5,
            "final_loss": 0.45
        }
        logger = init_cycle_logger(1)
        log_cycle_summary(1, summary, logger)

        history = get_cycle_history(1)
        summary_entries = [e for e in history if e.get("event") == "CYCLE_SUMMARY"]
        self.assertEqual(len(summary_entries), 1)
        self.assertEqual(summary_entries[0]["metrics"]["status"], "completed")

    def test_get_cycle_history_empty(self):
        """Test get_cycle_history returns empty list for non-existent log."""
        history = get_cycle_history(999)
        self.assertEqual(history, [])

    def test_log_error(self):
        """Test log_error writes error entries."""
        logger = init_cycle_logger(1)
        log_error(1, "Division by zero", "ZeroDivisionError", logger)

        history = get_cycle_history(1)
        error_entries = [e for e in history if e.get("event") == "ERROR"]
        self.assertEqual(len(error_entries), 1)
        self.assertEqual(error_entries[0]["metrics"]["error_message"], "Division by zero")
        self.assertEqual(error_entries[0]["metrics"]["error_type"], "ZeroDivisionError")

    def test_log_warning(self):
        """Test log_warning writes warning entries."""
        logger = init_cycle_logger(1)
        log_warning(1, "RAM usage high", "ResourceWarning", logger)

        history = get_cycle_history(1)
        warning_entries = [e for e in history if e.get("event") == "WARNING"]
        self.assertEqual(len(warning_entries), 1)
        self.assertEqual(warning_entries[0]["metrics"]["warning_message"], "RAM usage high")

    def test_multiple_log_entries(self):
        """Test that multiple log entries are appended correctly."""
        logger = init_cycle_logger(1)
        update_cycle_log(1, "start", {"step": 1}, logger)
        update_cycle_log(1, "process", {"step": 2}, logger)
        update_cycle_log(1, "end", {"step": 3}, logger)

        history = get_cycle_history(1)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["metrics"]["step"], 1)
        self.assertEqual(history[1]["metrics"]["step"], 2)
        self.assertEqual(history[2]["metrics"]["step"], 3)

    def test_json_format_valid(self):
        """Test that all log entries are valid JSON."""
        logger = init_cycle_logger(1)
        update_cycle_log(1, "test", {"data": [1, 2, 3]}, logger)

        log_path = get_log_path(1)
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Should not raise
                    json.loads(line)
