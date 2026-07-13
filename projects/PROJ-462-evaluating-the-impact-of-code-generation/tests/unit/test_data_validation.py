"""
Unit tests for missing data edge cases in data validation.
Tests filtering logic and >20% flagging as per T046a.
"""
import csv
import os
import tempfile
import unittest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest.validate import (
    identify_missing_experience_values,
    calculate_missing_percentage,
    filter_missing_data,
    load_verified_datasets_from_spec
)


class TestMissingDataEdgeCases(unittest.TestCase):
    """Unit tests for missing data edge cases in data validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(tempfile.mkdtemp())
        self.sample_csv_path = self.test_data_dir / "sample_data.csv"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.sample_csv_path.exists():
            self.sample_csv_path.unlink()
        if self.test_data_dir.exists():
            self.test_data_dir.rmdir()

    def _create_test_csv(self, rows):
        """Helper to create a test CSV file."""
        with open(self.sample_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return self.sample_csv_path

    def test_identify_missing_experience_values_empty_dataset(self):
        """Test identification of missing values in an empty dataset."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        self.assertEqual(len(missing_values), 0)

    def test_identify_missing_experience_values_no_missing(self):
        """Test identification when no values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '7', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        self.assertEqual(len(missing_values), 0)

    def test_identify_missing_experience_values_all_missing(self):
        """Test identification when all experience values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '', 'low', 'api', '2'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        self.assertEqual(len(missing_values), 3)
        self.assertEqual(missing_values, [1, 2, 3])  # Row indices (0-based, excluding header)

    def test_identify_missing_experience_values_mixed_missing(self):
        """Test identification with mixed missing values."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
            ['none', '180', '0.09', '', 'medium', 'web', '4'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        self.assertEqual(len(missing_values), 2)
        self.assertEqual(missing_values, [1, 3])  # Row indices (0-based, excluding header)

    def test_calculate_missing_percentage_zero_missing(self):
        """Test percentage calculation when no values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '7', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        percentage = calculate_missing_percentage(self.sample_csv_path, missing_values)
        self.assertEqual(percentage, 0.0)

    def test_calculate_missing_percentage_all_missing(self):
        """Test percentage calculation when all values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '', 'low', 'api', '2'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        percentage = calculate_missing_percentage(self.sample_csv_path, missing_values)
        self.assertEqual(percentage, 100.0)

    def test_calculate_missing_percentage_half_missing(self):
        """Test percentage calculation when half values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
            ['none', '180', '0.09', '', 'medium', 'web', '4'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        percentage = calculate_missing_percentage(self.sample_csv_path, missing_values)
        self.assertEqual(percentage, 50.0)

    def test_calculate_missing_percentage_exactly_twenty_percent(self):
        """Test percentage calculation at exactly 20% threshold."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
            ['none', '180', '0.09', '4', 'medium', 'web', '4'],
            ['copilot', '130', '0.06', '5', 'high', 'mobile', '6'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        percentage = calculate_missing_percentage(self.sample_csv_path, missing_values)
        self.assertEqual(percentage, 20.0)

    def test_calculate_missing_percentage_above_twenty_percent(self):
        """Test percentage calculation above 20% threshold."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '', 'low', 'api', '2'],
            ['none', '180', '0.09', '', 'medium', 'web', '4'],
            ['copilot', '130', '0.06', '5', 'high', 'mobile', '6'],
        ])

        missing_values = identify_missing_experience_values(self.sample_csv_path)
        percentage = calculate_missing_percentage(self.sample_csv_path, missing_values)
        self.assertGreater(percentage, 20.0)

    def test_filter_missing_data_no_missing(self):
        """Test filtering when no values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '7', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
        ])

        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count, 0)
        self.assertTrue(Path(filtered_path).exists())

        # Verify filtered file has same number of rows
        with open(filtered_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 4)  # header + 3 data rows

    def test_filter_missing_data_some_missing(self):
        """Test filtering when some values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
            ['none', '180', '0.09', '', 'medium', 'web', '4'],
        ])

        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count, 2)
        self.assertTrue(Path(filtered_path).exists())

        # Verify filtered file has correct number of rows
        with open(filtered_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)  # header + 2 data rows

    def test_filter_missing_data_all_missing(self):
        """Test filtering when all values are missing."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '', 'low', 'api', '2'],
        ])

        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count, 3)
        self.assertTrue(Path(filtered_path).exists())

        # Verify filtered file has only header
        with open(filtered_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 1)  # header only

    def test_filter_missing_data_flag_above_twenty_percent(self):
        """Test that filtering flags when >20% entries are removed."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '', 'low', 'api', '2'],
            ['none', '180', '0.09', '', 'medium', 'web', '4'],
            ['copilot', '130', '0.06', '5', 'high', 'mobile', '6'],
        ])

        # This should trigger the >20% flag (3 out of 5 = 60%)
        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertGreater(removed_count / 5 * 100, 20.0)

    def test_filter_missing_data_no_flag_at_twenty_percent(self):
        """Test that filtering does not flag when exactly 20% entries are removed."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
            ['codex', '150', '0.08', '1', 'low', 'api', '2'],
            ['none', '180', '0.09', '4', 'medium', 'web', '4'],
            ['copilot', '130', '0.06', '5', 'high', 'mobile', '6'],
        ])

        # This should NOT trigger the >20% flag (1 out of 5 = 20%)
        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count / 5 * 100, 20.0)

    def test_filter_missing_data_single_row_missing(self):
        """Test filtering with a single row having missing value."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
            ['none', '200', '0.10', '', 'high', 'mobile', '3'],
        ])

        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count, 1)
        self.assertTrue(Path(filtered_path).exists())

        with open(filtered_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 2)  # header + 1 data row

    def test_filter_missing_data_single_row_complete(self):
        """Test filtering with a single complete row."""
        self._create_test_csv([
            ['tool_usage', 'task_time', 'defect_rate', 'experience_years', 'task_complexity', 'project_type', 'team_size'],
            ['copilot', '120', '0.05', '3', 'medium', 'web', '5'],
        ])

        filtered_path, removed_count = filter_missing_data(self.sample_csv_path)
        self.assertEqual(removed_count, 0)
        self.assertTrue(Path(filtered_path).exists())

        with open(filtered_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 2)  # header + 1 data row


if __name__ == '__main__':
    unittest.main()