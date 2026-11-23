"""
Unit tests for code/generation/generate_summaries_offline.py
"""

import unittest
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generation.generate_summaries_offline import (
    generate_llm_summary_text,
    generate_rule_summary_text,
    load_ground_truth,
    save_summaries_to_csv
)

class TestGenerateSummariesOffline(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data", "raw", "defects4j")
        os.makedirs(self.data_dir, exist_ok=True)
        self.summaries_dir = os.path.join(self.temp_dir, "data", "summaries")
        os.makedirs(self.summaries_dir, exist_ok=True)

        # Create a mock ground_truth.csv
        self.mock_gt_path = os.path.join(self.data_dir, "ground_truth.csv")
        with open(self.mock_gt_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'method_id', 'ground_truth_line', 'project_name'])
            writer.writeheader()
            writer.writerow({
                'task_id': 'T001',
                'method_id': 'method_1',
                'ground_truth_line': '42',
                'project_name': 'Chart'
            })
            writer.writerow({
                'task_id': 'T002',
                'method_id': 'method_2',
                'ground_truth_line': '105',
                'project_name': 'Time'
            })

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    @patch('generation.generate_summaries_offline.INPUT_GROUND_TRUTH')
    @patch('generation.generate_summaries_offline.OUTPUT_DIR')
    def test_load_ground_truth_success(self, mock_output_dir, mock_gt_path):
        """Test loading ground truth from a valid file."""
        mock_gt_path.return_value = self.mock_gt_path
        mock_output_dir.return_value = Path(self.summaries_dir)

        tasks = load_ground_truth()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]['task_id'], 'T001')
        self.assertEqual(tasks[1]['project_name'], 'Time')

    @patch('generation.generate_summaries_offline.INPUT_GROUND_TRUTH')
    def test_load_ground_truth_missing_file(self, mock_gt_path):
        """Test loading ground truth when file does not exist."""
        mock_gt_path.return_value = Path("/nonexistent/file.csv")
        with self.assertRaises(FileNotFoundError):
            load_ground_truth()

    @patch('generation.generate_summaries_offline.INPUT_GROUND_TRUTH')
    def test_load_ground_truth_missing_columns(self, mock_gt_path):
        """Test loading ground truth with missing required columns."""
        temp_file = os.path.join(self.temp_dir, "bad_gt.csv")
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'wrong_col'])
            writer.writeheader()
            writer.writerow({'task_id': 'T001', 'wrong_col': 'val'})

        mock_gt_path.return_value = Path(temp_file)
        with self.assertRaises(ValueError):
            load_ground_truth()

    def test_generate_llm_summary_text(self):
        """Test that LLM summary generation produces non-empty strings."""
        summary = generate_llm_summary_text('T001', 'method_1', 'Chart')
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
        # Check for deterministic behavior
        summary2 = generate_llm_summary_text('T001', 'method_1', 'Chart')
        self.assertEqual(summary, summary2)

    def test_generate_rule_summary_text(self):
        """Test that rule-based summary generation produces non-empty strings."""
        summary = generate_rule_summary_text('T001', 'method_1', 'Chart')
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
        self.assertIn("[Rule-Based]", summary)

    @patch('generation.generate_summaries_offline.OUTPUT_DIR')
    def test_save_summaries_to_csv(self, mock_output_dir):
        """Test saving summaries to CSV."""
        mock_output_dir.return_value = Path(self.summaries_dir)
        summaries = [
            {'task_id': 'T001', 'summary_text': 'Test summary', 'method_id': 'm1'},
            {'task_id': 'T002', 'summary_text': 'Another summary', 'method_id': 'm2'}
        ]
        output_path = os.path.join(self.summaries_dir, "test_output.csv")

        save_summaries_to_csv(summaries, Path(output_path), "Test")

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['task_id'], 'T001')

    @patch('generation.generate_summaries_offline.OUTPUT_DIR')
    def test_save_summaries_empty_list(self, mock_output_dir):
        """Test that saving an empty list raises an error."""
        mock_output_dir.return_value = Path(self.summaries_dir)
        with self.assertRaises(ValueError):
            save_summaries_to_csv([], Path("dummy.csv"), "Test")

    @patch('generation.generate_summaries_offline.OUTPUT_DIR')
    def test_save_summaries_schema_mismatch(self, mock_output_dir):
        """Test that saving with wrong schema raises an error."""
        mock_output_dir.return_value = Path(self.summaries_dir)
        summaries = [
            {'task_id': 'T001', 'wrong_field': 'Test'} # Missing summary_text and method_id
        ]
        with self.assertRaises(ValueError):
            save_summaries_to_csv(summaries, Path("dummy.csv"), "Test")

if __name__ == '__main__':
    unittest.main()