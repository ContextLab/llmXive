"""
Unit tests for utils/logging.py
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from utils.logging import (
    get_log_path,
    init_cycle_logger,
    update_cycle_log,
    checkpoint_model_state,
    log_cycle_summary,
    get_cycle_history,
    log_error,
    log_warning,
)
from config import get_config, set_config, PathConfig


class TestLogging(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.results_path = os.path.join(self.test_dir, "results")
        os.makedirs(self.results_path)

        # Patch config to use our temp directory
        self.original_config = get_config()
        test_config = PathConfig(
            code_path=self.test_dir,
            data_raw_path=os.path.join(self.test_dir, "data", "raw"),
            data_processed_path=os.path.join(self.test_dir, "data", "processed"),
            results_path=self.results_path,
            specs_path=os.path.join(self.test_dir, "specs"),
            tests_path=os.path.join(self.test_dir, "tests"),
        )
        # Mock the config object
        mock_config = MagicMock()
        mock_config.results_path = self.results_path
        self.mock_config = mock_config

    def tearDown(self):
        # Clean up temp directory
        shutil.rmtree(self.test_dir)

    @patch("utils.logging.get_config")
    def test_get_log_path(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        path = get_log_path()
        expected = os.path.join(self.results_path, "logs")
        self.assertEqual(path, expected)

    @patch("utils.logging.get_config")
    def test_init_cycle_logger_creates_file(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        logger = init_cycle_logger(1)
        log_file = os.path.join(self.results_path, "logs", "cycle_1.log")
        self.assertTrue(os.path.exists(log_file))
        self.assertIsInstance(logger, MagicMock) or hasattr(logger, "info")

    @patch("utils.logging.get_config")
    def test_init_cycle_logger_json_format(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        logger = init_cycle_logger(2)
        update_cycle_log(logger, "Test message", {"key": "value"})

        log_file = os.path.join(self.results_path, "logs", "cycle_2.log")
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, "r") as f:
            line = f.readline().strip()
            entry = json.loads(line)

        self.assertEqual(entry["message"], "Test message")
        self.assertEqual(entry["key"], "value")
        self.assertEqual(entry["cycle"], 2)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["level"], "INFO")

    @patch("utils.logging.get_config")
    def test_checkpoint_model_state(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        model_state = {"layer1.weight": [1, 2, 3], "layer2.bias": [0.5]}
        path = checkpoint_model_state(3, model_state)

        expected_path = os.path.join(
            self.results_path, "checkpoints", "cycle_3_model.pt"
        )
        self.assertEqual(path, expected_path)
        self.assertTrue(os.path.exists(path))

    @patch("utils.logging.get_config")
    def test_log_cycle_summary(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        logger = init_cycle_logger(4)

        metrics = {"GSM8K": 0.85, "ARC": 0.92}
        log_cycle_summary(
            logger,
            cycle_number=4,
            metrics=metrics,
            modification_type="layer_add",
            param_count=120000000,
            training_time_seconds=3600.5,
            status="completed"
        )

        log_file = os.path.join(self.results_path, "logs", "cycle_4.log")
        with open(log_file, "r") as f:
            lines = f.readlines()

        # Find the summary line
        summary_line = None
        for line in lines:
            entry = json.loads(line.strip())
            if entry.get("cycle") == 4 and "metrics" in entry:
                summary_line = entry
                break

        self.assertIsNotNone(summary_line)
        self.assertEqual(summary_line["metrics"]["GSM8K"], 0.85)
        self.assertEqual(summary_line["modification_type"], "layer_add")
        self.assertEqual(summary_line["status"], "completed")

    @patch("utils.logging.get_config")
    def test_get_cycle_history(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        # Create some mock log files
        log_dir = os.path.join(self.results_path, "logs")
        os.makedirs(log_dir)

        with open(os.path.join(log_dir, "cycle_1.log"), "w") as f:
            f.write('{"message": "start", "cycle": 1}\n')
            f.write('{"message": "end", "cycle": 1}\n')

        with open(os.path.join(log_dir, "cycle_2.log"), "w") as f:
            f.write('{"message": "start", "cycle": 2}\n')

        history = get_cycle_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["message"], "start")
        self.assertEqual(history[0]["cycle"], 1)
        self.assertEqual(history[2]["message"], "start")
        self.assertEqual(history[2]["cycle"], 2)

    @patch("utils.logging.get_config")
    def test_log_error(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        logger = init_cycle_logger(5)
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_error(logger, "Something went wrong", e)

        log_file = os.path.join(self.results_path, "logs", "cycle_5.log")
        with open(log_file, "r") as f:
            lines = f.readlines()

        error_entry = None
        for line in lines:
            entry = json.loads(line.strip())
            if entry.get("level") == "ERROR":
                error_entry = entry
                break

        self.assertIsNotNone(error_entry)
        self.assertEqual(error_entry["message"], "Something went wrong")
        self.assertEqual(error_entry["exception_type"], "ValueError")
        self.assertEqual(error_entry["exception_message"], "Test error")

    @patch("utils.logging.get_config")
    def test_log_warning(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        logger = init_cycle_logger(6)
        log_warning(logger, "This is a warning")

        log_file = os.path.join(self.results_path, "logs", "cycle_6.log")
        with open(log_file, "r") as f:
            line = f.readline().strip()
            entry = json.loads(line)

        self.assertEqual(entry["level"], "WARNING")
        self.assertEqual(entry["message"], "This is a warning")

    @patch("utils.logging.get_config")
    def test_malformed_json_skipped_in_history(self, mock_get_config):
        mock_get_config.return_value = self.mock_config
        log_dir = os.path.join(self.results_path, "logs")
        os.makedirs(log_dir)

        with open(os.path.join(log_dir, "cycle_7.log"), "w") as f:
            f.write('{"valid": true}\n')
            f.write('this is not json\n')
            f.write('{"also_valid": true}\n')

        history = get_cycle_history()
        # Should only include the two valid JSON lines
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["valid"], True)
        self.assertEqual(history[1]["also_valid"], True)
