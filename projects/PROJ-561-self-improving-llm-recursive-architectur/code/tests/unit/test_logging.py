"""
Unit tests for utils.logging module (T009).
Verifies structured JSON log creation and checkpointing functionality.
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, PropertyMock
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.logging import (
    init_cycle_logger,
    get_logger,
    get_cycle_history,
    log_cycle_summary,
    log_error,
    log_warning,
    checkpoint_model_state,
    update_cycle_log
)
from config import PathConfig, Config, get_config, set_config

class MockConfig:
    def __init__(self, tmp_dir):
        self.paths = PathConfig(
            raw_data=os.path.join(tmp_dir, "raw"),
            processed_data=os.path.join(tmp_dir, "processed"),
            results=os.path.join(tmp_dir, "results"),
            logs=os.path.join(tmp_dir, "logs"),
            checkpoints=os.path.join(tmp_dir, "checkpoints")
        )

class TestLogging(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config = MockConfig(self.temp_dir)
        # Patch get_config to return our mock
        self.patcher = patch('utils.logging.get_config', return_value=self.mock_config)
        self.mock_get_config = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_cycle_logger_creates_file(self):
        """Verify that init_cycle_logger creates the log file with JSON content."""
        cycle_num = 1
        logger = init_cycle_logger(cycle_num)

        expected_path = os.path.join(self.mock_config.paths.results, "logs", f"cycle_{cycle_num}.log")
        self.assertTrue(os.path.exists(expected_path), f"Log file {expected_path} was not created")

        # Verify content is valid JSON
        with open(expected_path, 'r') as f:
            content = f.read()
            # Log file should have at least one entry if we logged something,
            # but the file existence is the primary check for T009.
            # Let's log something to ensure content exists.
            logger.info("Test initialization", extra={'cycle': cycle_num, 'component': 'test'})

        with open(expected_path, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0, "Log file is empty")
            # Verify each line is valid JSON
            for line in lines:
                try:
                    json.loads(line.strip())
                except json.JSONDecodeError:
                    self.fail(f"Line is not valid JSON: {line}")

    def test_log_cycle_summary(self):
        """Verify log_cycle_summary writes structured metrics."""
        cycle_num = 2
        logger = init_cycle_logger(cycle_num)
        metrics = {
            "accuracy": 0.85,
            "loss": 1.23,
            "duration_sec": 10.5
        }

        log_cycle_summary(logger, cycle_num, metrics)

        log_path = os.path.join(self.mock_config.paths.results, "logs", f"cycle_{cycle_num}.log")
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("0.85", content)
            self.assertIn("1.23", content)

    def test_log_error(self):
        """Verify log_error writes structured error."""
        cycle_num = 3
        logger = init_cycle_logger(cycle_num)
        log_error(logger, cycle_num, "Test error message")

        log_path = os.path.join(self.mock_config.paths.results, "logs", f"cycle_{cycle_num}.log")
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("Test error message", content)
            self.assertIn("ERROR", content)

    def test_get_cycle_history(self):
        """Verify get_cycle_history returns parsed log entries."""
        cycle_num = 4
        logger = init_cycle_logger(cycle_num)
        logger.info("Entry 1", extra={'cycle': cycle_num})
        logger.info("Entry 2", extra={'cycle': cycle_num})

        history = get_cycle_history(cycle_num)
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0]["message"], "Entry 1")
        self.assertEqual(history[1]["message"], "Entry 2")

    def test_checkpoint_model_state(self):
        """Verify checkpoint_model_state creates a valid file."""
        cycle_num = 5
        mock_model = MagicMock()
        mock_model.state_dict.return_value = {"layer1.weight": [[1.0, 2.0]]}

        path = checkpoint_model_state(mock_model, cycle_num)

        self.assertTrue(os.path.exists(path))
        self.assertIn(f"cycle_{cycle_num}", path)
        self.assertTrue(path.endswith(".pt"))

    def test_update_cycle_log(self):
        """Verify update_cycle_log appends structured JSON."""
        cycle_num = 6
        update_cycle_log(cycle_num, "start", {"step": 1})
        update_cycle_log(cycle_num, "end", {"step": 10})

        log_path = os.path.join(self.mock_config.paths.results, "logs", f"cycle_{cycle_num}.log")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            entry1 = json.loads(lines[0])
            entry2 = json.loads(lines[1])
            self.assertEqual(entry1["event_type"], "start")
            self.assertEqual(entry2["event_type"], "end")

if __name__ == '__main__':
    unittest.main()
