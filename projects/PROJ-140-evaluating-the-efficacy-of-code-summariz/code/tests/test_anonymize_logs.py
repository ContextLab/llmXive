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
        self.anonymized_logs_path = os.path.join(self.temp_dir, "anonymized_logs.csv")
        self.mapping_path = os.path.join(self.temp_dir, "mapping.json")
        
        # Create test raw logs
        test_data = [
            {
                'participant_id': 'P001',
                'task_id': 'T1',
                'condition': 'baseline',
                'timestamp_ms': '1234567890',
                'selected_line': '10',
                'ground_truth_line': '15'
            },
            {
                'participant_id': 'P002',
                'task_id': 'T2',
                'condition': 'llm',
                'timestamp_ms': '1234567891',
                'selected_line': '20',
                'ground_truth_line': '20'
            },
            {
                'participant_id': 'P001',
                'task_id': 'T3',
                'condition': 'rule',
                'timestamp_ms': '1234567892',
                'selected_line': '5',
                'ground_truth_line': '8'
            }
        ]
        
        with open(self.raw_logs_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_data[0].keys())
            writer.writeheader()
            writer.writerows(test_data)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_raw_logs(self):
        """Test loading raw logs from CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0]['participant_id'], 'P001')
        self.assertEqual(logs[1]['participant_id'], 'P002')
    
    def test_load_raw_logs_missing_file(self):
        """Test loading raw logs when file does not exist."""
        logs = load_raw_logs(os.path.join(self.temp_dir, "nonexistent.csv"))
        self.assertEqual(len(logs), 0)
    
    def test_create_anonymization_mapping(self):
        """Test creation of anonymization mapping."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        
        self.assertEqual(len(mapping), 2)  # P001 and P002
        self.assertIn('P001', mapping)
        self.assertIn('P002', mapping)
        
        # Check format of anonymized IDs
        for anon_id in mapping.values():
            self.assertTrue(anon_id.startswith('ANON_'))
            self.assertEqual(len(anon_id), 17)  # ANON_ + 8 hex chars
    
    def test_anonymization_is_deterministic(self):
        """Test that anonymization is deterministic."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping1 = create_anonymization_mapping(logs)
        mapping2 = create_anonymization_mapping(logs)
        
        self.assertEqual(mapping1, mapping2)
    
    def test_anonymize_logs(self):
        """Test anonymization of log entries."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anonymized = anonymize_logs(logs, mapping)
        
        # Check that all participant IDs are anonymized
        for log in anonymized:
            self.assertTrue(log['participant_id'].startswith('ANON_'))
        
        # Check that non-participant fields are preserved
        self.assertEqual(anonymized[0]['task_id'], 'T1')
        self.assertEqual(anonymized[0]['condition'], 'baseline')
        self.assertEqual(anonymized[0]['timestamp_ms'], '1234567890')
    
    def test_save_anonymized_logs(self):
        """Test saving anonymized logs to CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        mapping = create_anonymization_mapping(logs)
        anonymized = anonymize_logs(logs, mapping)
        
        save_anonymized_logs(anonymized, self.anonymized_logs_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.anonymized_logs_path))
        
        # Verify content
        with open(self.anonymized_logs_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 3)
        self.assertTrue(rows[0]['participant_id'].startswith('ANON_'))
    
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
    
    def test_integration_full_flow(self):
        """Test the full anonymization flow."""
        logs = load_raw_logs(self.raw_logs_path)
        self.assertGreater(len(logs), 0)
        
        mapping = create_anonymization_mapping(logs)
        self.assertGreater(len(mapping), 0)
        
        anonymized = anonymize_logs(logs, mapping)
        self.assertEqual(len(anonymized), len(logs))
        
        save_anonymized_logs(anonymized, self.anonymized_logs_path)
        save_anonymization_mapping(mapping, self.mapping_path)
        
        # Verify outputs
        with open(self.anonymized_logs_path, 'r') as f:
            reader = csv.DictReader(f)
            anonymized_rows = list(reader)
        
        with open(self.mapping_path, 'r') as f:
            loaded_mapping = json.load(f)
        
        # Check that anonymized IDs in CSV match mapping
        anon_ids_in_csv = set(row['participant_id'] for row in anonymized_rows)
        anon_ids_in_mapping = set(loaded_mapping.values())
        
        self.assertEqual(anon_ids_in_csv, anon_ids_in_mapping)

if __name__ == '__main__':
    unittest.main()