"""
Unit tests for the experiment logging infrastructure.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from logs.experiment import ExperimentLogger, reset_logger


class TestExperimentLogger(TestCase):
    """Tests for the ExperimentLogger class."""

    def setUp(self):
        """Set up a temporary directory for test logs."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_experiment.log"
        self.logger = ExperimentLogger(self.log_file)

    def tearDown(self):
        """Clean up temporary files."""
        if self.log_file.exists():
            self.log_file.unlink()
        os.rmdir(self.temp_dir)

    def test_log_session_start(self):
        """Test logging a session start event."""
        self.logger.log_session_start("P001", "llm_assisted", 42)

        with open(self.log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)

        self.assertEqual(entry['event_type'], 'session_start')
        self.assertEqual(entry['participant_id'], 'P001')
        self.assertEqual(entry['condition'], 'llm_assisted')
        self.assertEqual(entry['seed'], 42)
        self.assertIn('session_id', entry['data'])

    def test_log_problem_presented(self):
        """Test logging a problem presentation event."""
        self.logger.log_problem_presented(
            participant_id="P001",
            condition="baseline",
            seed=123,
            problem_id="HumanEval/5",
            language="python",
            difficulty="medium"
        )

        with open(self.log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)

        self.assertEqual(entry['event_type'], 'problem_presented')
        self.assertEqual(entry['participant_id'], 'P001')
        self.assertEqual(entry['condition'], 'baseline')
        self.assertEqual(entry['data']['problem_id'], 'HumanEval/5')
        self.assertEqual(entry['data']['language'], 'python')
        self.assertEqual(entry['data']['difficulty'], 'medium')

    def test_log_submission(self):
        """Test logging a submission event."""
        self.logger.log_submission(
            participant_id="P001",
            condition="llm_assisted",
            seed=42,
            submission_id="sub_001",
            problem_id="HumanEval/0",
            completion_time_seconds=185.5,
            code_length=256
        )

        with open(self.log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)

        self.assertEqual(entry['event_type'], 'submission')
        self.assertEqual(entry['data']['submission_id'], 'sub_001')
        self.assertEqual(entry['data']['completion_time_seconds'], 185.5)
        self.assertEqual(entry['data']['code_length'], 256)

    def test_invalid_condition(self):
        """Test that invalid condition raises ValueError."""
        with self.assertRaises(ValueError):
            self.logger.log_session_start("P001", "invalid_condition", 42)

    def test_multiple_entries(self):
        """Test that multiple entries are appended correctly."""
        self.logger.log_session_start("P001", "llm_assisted", 42)
        self.logger.log_session_end("P001", "llm_assisted", 42)

        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verify both entries are valid JSON
        for line in lines:
            json.loads(line)

    def test_timestamp_format(self):
        """Test that timestamps are in ISO-8601 format."""
        self.logger.log_session_start("P001", "llm_assisted", 42)

        with open(self.log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)

        # Basic check for ISO format (contains 'T' and timezone)
        self.assertIn('T', entry['timestamp'])
        self.assertIn('+', entry['timestamp'])  # UTC offset

    def test_log_file_creation(self):
        """Test that the log file is created if it doesn't exist."""
        new_log_file = Path(self.temp_dir) / "new_log.log"
        self.assertFalse(new_log_file.exists())

        logger = ExperimentLogger(new_log_file)
        logger.log_session_start("P001", "llm_assisted", 42)

        self.assertTrue(new_log_file.exists())
        self.assertGreater(new_log_file.stat().st_size, 0)

    def test_append_mode(self):
        """Test that new logs are appended, not overwritten."""
        # Write initial content
        with open(self.log_file, 'w') as f:
            f.write('{"existing": "data"}\n')

        self.logger.log_session_start("P001", "llm_assisted", 42)

        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)
        self.assertIn('{"existing": "data"}', lines[0])

    def test_get_log_file_path(self):
        """Test that get_log_file_path returns the correct path."""
        path = self.logger.get_log_file_path()
        self.assertEqual(path, self.log_file)
        self.assertIsInstance(path, Path)