import unittest
import os
import sys
import csv
import json
import tempfile
from pathlib import Path
from utils.anonymize_logs import (
    load_raw_logs,
    create_anonymization_mapping,
    anonymize_logs,
    save_anonymized_logs,
    save_anonymization_mapping
)

class TestAnonymizeLogs(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_logs_path = os.path.join(self.temp_dir, "raw_logs.csv")
        self.anon_logs_path = os.path.join(self.temp_dir, "anonymized_logs.csv")
        self.mapping_path = os.path.join(self.temp_dir, "mapping.json")
        
        # Create test raw logs
        test_data = [
            {'participant_id': 'P001', 'task_id': 'T1', 'condition': 'LLM', 'timestamp_ms': '1000', 'selected_line': '5', 'ground_truth_line': '5'},
            {'participant_id': 'P001', 'task_id': 'T2', 'condition': 'Rule', 'timestamp_ms': '2000', 'selected_line': '10', 'ground_truth_line': '10'},
            {'participant_id': 'P002', 'task_id': 'T1', 'condition': 'Rule', 'timestamp_ms': '3000', 'selected_line': '5', 'ground_truth_line': '5'},
            {'participant_id': 'P003', 'task_id': 'T3', 'condition': 'LLM', 'timestamp_ms': '4000', 'selected_line': '15', 'ground_truth_line': '15'},
        ]
        
        with open(self.raw_logs_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_data[0].keys())
            writer.writeheader()
            writer.writerows(test_data)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_raw_logs(self):
        """Test loading raw logs from CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        self.assertEqual(len(logs), 4)
        self.assertEqual(logs[0]['participant_id'], 'P001')
    
    def test_load_raw_logs_missing_file(self):
        """Test loading from a non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            load_raw_logs("/nonexistent/path.csv")
    
    def test_create_anonymization_mapping(self):
        """Test creation of anonymization mapping."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        
        # Should have 3 unique participants
        self.assertEqual(len(mapping), 3)
        
        # Check that all real IDs are in mapping
        self.assertIn('P001', mapping)
        self.assertIn('P002', mapping)
        self.assertIn('P003', mapping)
        
        # Check that anonymized IDs follow the pattern
        for anon_id in mapping.values():
            self.assertTrue(anon_id.startswith("ANON_"))
            self.assertEqual(len(anon_id), 17) # "ANON_" + 8 hex chars
    
    def test_anonymize_logs(self):
        """Test anonymization of log entries."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anon_logs = anonymize_logs(logs, mapping)
        
        # Check that participant IDs are replaced
        for log in anon_logs:
            self.assertTrue(log['participant_id'].startswith("ANON_"))
            self.assertNotIn(log['participant_id'], ['P001', 'P002', 'P003'])
        
        # Check that other fields are preserved
        self.assertEqual(anon_logs[0]['task_id'], 'T1')
        self.assertEqual(anon_logs[0]['condition'], 'LLM')
        self.assertEqual(anon_logs[0]['timestamp_ms'], '1000')
    
    def test_save_and_load_anonymized_logs(self):
        """Test saving and reloading anonymized logs."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anon_logs = anonymize_logs(logs, mapping)
        
        save_anonymized_logs(anon_logs, self.anon_logs_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.anon_logs_path))
        
        # Verify content
        with open(self.anon_logs_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 4)
        self.assertTrue(rows[0]['participant_id'].startswith("ANON_"))
    
    def test_save_and_load_mapping(self):
        """Test saving and loading anonymization mapping."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        
        save_anonymization_mapping(mapping, self.mapping_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.mapping_path))
        
        # Verify content
        with open(self.mapping_path, 'r') as f:
            loaded_mapping = json.load(f)
        
        self.assertEqual(len(loaded_mapping), 3)
        self.assertEqual(loaded_mapping, mapping)

if __name__ == '__main__':
    unittest.main()