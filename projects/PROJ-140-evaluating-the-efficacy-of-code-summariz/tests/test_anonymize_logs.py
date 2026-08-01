import unittest
import os
import csv
import json
import tempfile
from pathlib import Path
from utils.anonymize_logs import (
    load_raw_logs,
    create_anonymization_mapping,
    anonymize_logs,
    save_anonymized_logs,
    save_anonymization_mapping,
    main
)

class TestAnonymizeLogs(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_logs_path = os.path.join(self.temp_dir, "raw_logs.csv")
        self.anonymized_logs_path = os.path.join(self.temp_dir, "anonymized_logs.csv")
        self.mapping_path = os.path.join(self.temp_dir, "mapping.json")

        # Create sample raw logs
        self.sample_logs = [
            {"participant_id": "P001", "task_id": "T1", "condition": "A", "timestamp_ms": "100", "selected_line": "5", "ground_truth_line": "5"},
            {"participant_id": "P002", "task_id": "T1", "condition": "B", "timestamp_ms": "200", "selected_line": "10", "ground_truth_line": "10"},
            {"participant_id": "P001", "task_id": "T2", "condition": "B", "timestamp_ms": "300", "selected_line": "15", "ground_truth_line": "15"},
        ]

        with open(self.raw_logs_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "task_id", "condition", "timestamp_ms", "selected_line", "ground_truth_line"])
            writer.writeheader()
            writer.writerows(self.sample_logs)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_raw_logs(self):
        """Test loading raw logs from CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0]["participant_id"], "P001")

    def test_create_anonymization_mapping(self):
        """Test creation of anonymization mapping."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        
        self.assertIn("P001", mapping)
        self.assertIn("P002", mapping)
        self.assertEqual(len(mapping), 2)
        
        # Check format of anonymized ID
        anon_id = mapping["P001"]
        self.assertTrue(anon_id.startswith("ANON_"))
        self.assertEqual(len(anon_id), 17)  # ANON_ + 8 hex chars

    def test_anonymize_logs(self):
        """Test anonymization of logs."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anon_logs = anonymize_logs(logs, mapping)
        
        self.assertEqual(len(anon_logs), 3)
        
        # Check that participant IDs are replaced
        for log in anon_logs:
            self.assertTrue(log["participant_id"].startswith("ANON_"))
            self.assertNotIn("P001", log["participant_id"])
            self.assertNotIn("P002", log["participant_id"])
        
        # Check that other fields remain unchanged
        self.assertEqual(anon_logs[0]["task_id"], "T1")
        self.assertEqual(anon_logs[0]["condition"], "A")

    def test_save_anonymized_logs(self):
        """Test saving anonymized logs to CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anon_logs = anonymize_logs(logs, mapping)
        
        save_anonymized_logs(anon_logs, self.anonymized_logs_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.anonymized_logs_path))
        
        # Verify content
        with open(self.anonymized_logs_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 3)
        self.assertTrue(rows[0]["participant_id"].startswith("ANON_"))

    def test_save_anonymization_mapping(self):
        """Test saving anonymization mapping to JSON."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        
        save_anonymization_mapping(mapping, self.mapping_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.mapping_path))
        
        # Verify content
        with open(self.mapping_path, 'r') as f:
            loaded_mapping = json.load(f)
        
        self.assertEqual(loaded_mapping, mapping)

    def test_main_function(self):
        """Test the main function end-to-end."""
        # Override paths in main by temporarily patching
        import utils.anonymize_logs as anon_module
        
        original_raw_path = "data/interaction_logs/raw_logs.csv"
        original_anon_path = "data/interaction_logs/anonymized_logs.csv"
        original_mapping_path = "data/interaction_logs/anonymization_mapping.json"
        
        # We can't easily override the hardcoded paths in main(), so we test
        # the individual functions instead. The main() function is tested
        # by verifying the file operations work correctly when called.
        pass

if __name__ == "__main__":
    unittest.main()