"""
Unit tests for the timestamp recorder module.
"""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from experiment.timestamp_recorder import (
    get_current_utc_timestamp,
    get_current_utc_timestamp_unix,
    record_timestamp,
    record_problem_view,
    record_code_submission,
    record_condition_switch,
    get_elapsed_time,
    validate_timestamp_format
)


class TestTimestampRecorder(unittest.TestCase):
    """Test cases for timestamp recording functionality."""

    def test_get_current_utc_timestamp_format(self):
        """Test that current UTC timestamp is in correct ISO 8601 format."""
        timestamp = get_current_utc_timestamp()
        
        # Should contain T separator and timezone info
        self.assertIn("T", timestamp)
        self.assertIn("+00:00", timestamp)
        
        # Should be parseable
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsNotNone(parsed)

    def test_get_current_utc_timestamp_unix(self):
        """Test that Unix timestamp is a valid float."""
        timestamp = get_current_utc_timestamp_unix()
        
        self.assertIsInstance(timestamp, float)
        self.assertGreater(timestamp, 0)

    def test_validate_timestamp_format_valid(self):
        """Test validation of valid timestamp formats."""
        valid_timestamps = [
            "2024-01-15T14:30:45+00:00",
            "2024-01-15T14:30:45.123456+00:00",
            "2024-01-15T14:30:45.123456-05:00"
        ]
        
        for ts in valid_timestamps:
            self.assertTrue(validate_timestamp_format(ts), f"Failed for {ts}")

    def test_validate_timestamp_format_invalid(self):
        """Test validation of invalid timestamp formats."""
        invalid_timestamps = [
            "2024-01-15 14:30:45",
            "2024/01/15T14:30:45",
            "not a timestamp",
            ""
        ]
        
        for ts in invalid_timestamps:
            self.assertFalse(validate_timestamp_format(ts), f"Should be invalid: {ts}")

    def test_get_elapsed_time(self):
        """Test elapsed time calculation."""
        start = "2024-01-15T14:30:00+00:00"
        end = "2024-01-15T14:35:30+00:00"
        
        elapsed = get_elapsed_time(start, end)
        
        # Should be 5 minutes and 30 seconds = 330 seconds
        self.assertEqual(elapsed, 330.0)

    def test_get_elapsed_time_negative(self):
        """Test that elapsed time is negative if end is before start."""
        start = "2024-01-15T14:35:30+00:00"
        end = "2024-01-15T14:30:00+00:00"
        
        elapsed = get_elapsed_time(start, end)
        
        self.assertLess(elapsed, 0)

    @patch('experiment.timestamp_recorder.log_experiment_event')
    @patch('experiment.timestamp_recorder.get_logger')
    def test_record_timestamp(self, mock_logger, mock_log_event):
        """Test timestamp recording with all parameters."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        record_id = record_timestamp(
            participant_id="test_participant",
            session_id="test_session",
            event_type="test_event",
            problem_id="test_problem",
            metadata={"key": "value"}
        )
        
        # Should return a non-empty string
        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)
        
        # Should have called log_experiment_event
        mock_log_event.assert_called_once()

    @patch('experiment.timestamp_recorder.record_timestamp')
    def test_record_problem_view(self, mock_record):
        """Test problem view recording."""
        mock_record.return_value = "test_record_id"
        
        result = record_problem_view(
            participant_id="test_participant",
            session_id="test_session",
            problem_id="test_problem",
            problem_source="HumanEval"
        )
        
        mock_record.assert_called_once_with(
            participant_id="test_participant",
            session_id="test_session",
            event_type="problem_viewed",
            problem_id="test_problem",
            metadata={"problem_source": "HumanEval"}
        )
        self.assertEqual(result, "test_record_id")

    @patch('experiment.timestamp_recorder.record_timestamp')
    def test_record_code_submission(self, mock_record):
        """Test code submission recording."""
        mock_record.return_value = "test_record_id"
        
        result = record_code_submission(
            participant_id="test_participant",
            session_id="test_session",
            problem_id="test_problem",
            submission_id="test_submission",
            language="python",
            condition="LLM-assisted"
        )
        
        mock_record.assert_called_once_with(
            participant_id="test_participant",
            session_id="test_session",
            event_type="code_submitted",
            problem_id="test_problem",
            metadata={
                "submission_id": "test_submission",
                "language": "python",
                "condition": "LLM-assisted"
            }
        )
        self.assertEqual(result, "test_record_id")

    @patch('experiment.timestamp_recorder.record_timestamp')
    def test_record_condition_switch(self, mock_record):
        """Test condition switch recording."""
        mock_record.return_value = "test_record_id"
        
        result = record_condition_switch(
            participant_id="test_participant",
            session_id="test_session",
            old_condition="baseline",
            new_condition="LLM-assisted"
        )
        
        mock_record.assert_called_once_with(
            participant_id="test_participant",
            session_id="test_session",
            event_type="condition_switch",
            metadata={
                "old_condition": "baseline",
                "new_condition": "LLM-assisted"
            }
        )
        self.assertEqual(result, "test_record_id")


if __name__ == "__main__":
    unittest.main()