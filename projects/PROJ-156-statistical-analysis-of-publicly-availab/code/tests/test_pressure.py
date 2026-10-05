"""
Tests for the calculate_lagged_pressure function.

These tests verify that the lagged competitive pressure calculation
works correctly with mock data.
"""
import unittest
import sys
import os
from datetime import datetime, timedelta
from scripts.utils.pressure import calculate_lagged_pressure

class TestLaggedCalc(unittest.TestCase):
    """Test cases for lagged pressure calculation."""

    def test_empty_input(self):
        """Test that empty input returns empty output."""
        result = calculate_lagged_pressure([])
        self.assertEqual(result, [])

    def test_single_record(self):
        """Test that a single record has zero lagged pressure."""
        records = [
            {
                'submission_date': datetime(2023, 1, 15),
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            }
        ]
        result = calculate_lagged_pressure(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['lagged_competitive_pressure'], 0)

    def test_two_runners_no_overlap(self):
        """Test two runners with no overlapping dates."""
        records = [
            {
                'submission_date': datetime(2023, 1, 1),
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            },
            {
                'submission_date': datetime(2023, 3, 1),  # 60 days later
                'runner_id': 'runner2',
                'run_time_seconds': 95.0
            }
        ]
        result = calculate_lagged_pressure(records, window_days=30)
        # First record: 0 pressure (no prior runs)
        self.assertEqual(result[0]['lagged_competitive_pressure'], 0)
        # Second record: 0 pressure (runner1 is 60 days ago, outside 30-day window)
        self.assertEqual(result[1]['lagged_competitive_pressure'], 0)

    def test_two_runners_with_overlap(self):
        """Test two runners with overlapping dates within window."""
        records = [
            {
                'submission_date': datetime(2023, 1, 1),
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            },
            {
                'submission_date': datetime(2023, 1, 15),  # 14 days later
                'runner_id': 'runner2',
                'run_time_seconds': 95.0
            }
        ]
        result = calculate_lagged_pressure(records, window_days=30)
        # First record: 0 pressure
        self.assertEqual(result[0]['lagged_competitive_pressure'], 0)
        # Second record: 1 pressure (runner1 is within 30-day window)
        self.assertEqual(result[1]['lagged_competitive_pressure'], 1)

    def test_multiple_runners_same_day(self):
        """Test multiple runners on the same day."""
        base_date = datetime(2023, 1, 15)
        records = [
            {
                'submission_date': base_date - timedelta(days=10),
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            },
            {
                'submission_date': base_date - timedelta(days=5),
                'runner_id': 'runner2',
                'run_time_seconds': 95.0
            },
            {
                'submission_date': base_date,
                'runner_id': 'runner3',
                'run_time_seconds': 90.0
            }
        ]
        result = calculate_lagged_pressure(records, window_days=30)
        # First record: 0 pressure
        self.assertEqual(result[0]['lagged_competitive_pressure'], 0)
        # Second record: 1 pressure (runner1)
        self.assertEqual(result[1]['lagged_competitive_pressure'], 1)
        # Third record: 2 pressure (runner1 and runner2)
        self.assertEqual(result[2]['lagged_competitive_pressure'], 2)

    def test_string_date_parsing(self):
        """Test that string dates are parsed correctly."""
        records = [
            {
                'submission_date': '2023-01-01T00:00:00',
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            },
            {
                'submission_date': '2023-01-15T00:00:00',
                'runner_id': 'runner2',
                'run_time_seconds': 95.0
            }
        ]
        result = calculate_lagged_pressure(records, window_days=30)
        # First record: 0 pressure
        self.assertEqual(result[0]['lagged_competitive_pressure'], 0)
        # Second record: 1 pressure
        self.assertEqual(result[1]['lagged_competitive_pressure'], 1)

    def test_custom_window_size(self):
        """Test with a custom window size."""
        records = [
            {
                'submission_date': datetime(2023, 1, 1),
                'runner_id': 'runner1',
                'run_time_seconds': 100.0
            },
            {
                'submission_date': datetime(2023, 1, 20),  # 19 days later
                'runner_id': 'runner2',
                'run_time_seconds': 95.0
            }
        ]
        # With 15-day window, runner1 should not be counted
        result_15 = calculate_lagged_pressure(records, window_days=15)
        self.assertEqual(result_15[1]['lagged_competitive_pressure'], 0)
        
        # With 25-day window, runner1 should be counted
        result_25 = calculate_lagged_pressure(records, window_days=25)
        self.assertEqual(result_25[1]['lagged_competitive_pressure'], 1)

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValueError."""
        records = [
            {
                'submission_date': datetime(2023, 1, 1),
                # Missing runner_id
                'run_time_seconds': 100.0
            }
        ]
        with self.assertRaises(ValueError):
            calculate_lagged_pressure(records)

    def test_signature_correct(self):
        """Verify the function has the correct signature."""
        import inspect
        sig = inspect.signature(calculate_lagged_pressure)
        params = list(sig.parameters.keys())
        
        self.assertIn('run_records', params)
        self.assertIn('window_days', params)
        
        # Check default value
        self.assertEqual(sig.parameters['window_days'].default, 30)

if __name__ == '__main__':
    unittest.main()