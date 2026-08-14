"""
Unit tests for T032: Cleaning Pipeline.
Tests the aggregation of cleaning steps and output generation.
"""

import json
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, mock_open

import sys
import pathlib

# Add project root to path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis import remove_pii, handle_incomplete_records, save_cleaned_dataset_csv


class TestCleaningPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_logs_path = os.path.join(self.temp_dir, "raw_logs.json")
        self.validation_report_path = os.path.join(self.temp_dir, "validation_report.json")
        self.cleaned_csv_path = os.path.join(self.temp_dir, "cleaned_dataset.csv")
        self.dropouts_path = os.path.join(self.temp_dir, "dropouts.json")

        # Mock data
        self.raw_logs = [
            {
                "participant_id": "P001",
                "name": "John Doe",  # PII
                "email": "john.doe@example.com",  # PII
                "condition": "llm",
                "time_seconds": 120,
                "questions_count": 2,
                "completed": True
            },
            {
                "participant_id": "P002",
                "name": "Jane Smith",  # PII
                "email": "jane.smith@example.com",  # PII
                "condition": "human",
                "time_seconds": 0,  # Incomplete (time=0)
                "questions_count": 0,
                "completed": False
            },
            {
                "participant_id": "P003",
                "name": "Alice Johnson",  # PII
                "email": "alice@example.org",  # PII
                "condition": "none",
                "time_seconds": 180,
                "questions_count": 1,
                "completed": True
            }
        ]

        self.validation_report = {"status": "passed", "details": "All schemas valid"}

        # Write mock files
        with open(self.raw_logs_path, 'w') as f:
            json.dump(self.raw_logs, f)

        with open(self.validation_report_path, 'w') as f:
            json.dump(self.validation_report, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_pii_removal(self):
        """Test that PII is removed from logs."""
        cleaned = remove_pii(self.raw_logs)
        for entry in cleaned:
            self.assertNotIn("name", entry, "Name should be removed")
            self.assertNotIn("email", entry, "Email should be removed")
            self.assertIn("participant_id", entry, "ID should remain")

    def test_incomplete_record_handling(self):
        """Test that incomplete records are separated."""
        cleaned, dropouts = handle_incomplete_records(self.raw_logs)
        
        # P002 should be in dropouts because completed=False and time_seconds=0
        dropout_ids = [d["participant_id"] for d in dropouts]
        self.assertIn("P002", dropout_ids)

        # P001 and P003 should be in cleaned
        cleaned_ids = [c["participant_id"] for c in cleaned]
        self.assertIn("P001", cleaned_ids)
        self.assertIn("P003", cleaned_ids)
        self.assertNotIn("P002", cleaned_ids)

    def test_save_cleaned_csv(self):
        """Test that cleaned data is saved correctly as CSV."""
        cleaned, _ = handle_incomplete_records(self.raw_logs)
        save_cleaned_dataset_csv(cleaned, self.cleaned_csv_path)
        
        self.assertTrue(os.path.exists(self.cleaned_csv_path))
        
        with open(self.cleaned_csv_path, 'r') as f:
            lines = f.readlines()
        
        # Check header
        self.assertIn("participant_id", lines[0])
        self.assertIn("condition", lines[0])
        
        # Check data rows (should have 2 rows: P001 and P003)
        self.assertEqual(len(lines), 3)  # 1 header + 2 data rows

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_pipeline_logic(self, mock_join, mock_exists, mock_file):
        """Test the high-level logic of the cleaning pipeline."""
        # Mock file existence
        mock_exists.side_effect = lambda p: p in [
            self.validation_report_path,
            self.raw_logs_path
        ]

        # Mock load_json_file and save_json_file
        with patch('analysis.load_json_file') as mock_load, \
             patch('analysis.save_json_file') as mock_save:
            
            mock_load.side_effect = [self.validation_report, self.raw_logs]
            
            # Import the main function logic here to test flow
            # We can't easily test the full script execution without mocking sys.exit,
            # so we test the core logic steps instead.
            
            # Step 1: Validation check
            if self.validation_report.get("status") != "passed":
                self.fail("Validation should pass")
            
            # Step 2: PII Removal
            cleaned = remove_pii(self.raw_logs)
            self.assertEqual(len(cleaned), len(self.raw_logs))
            
            # Step 3: Incomplete handling
            final_cleaned, dropouts = handle_incomplete_records(cleaned)
            self.assertEqual(len(final_cleaned), 2)
            self.assertEqual(len(dropouts), 1)


if __name__ == '__main__':
    unittest.main()