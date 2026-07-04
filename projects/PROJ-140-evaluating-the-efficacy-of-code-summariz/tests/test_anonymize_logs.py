import unittest
import os
import csv
import json
import tempfile
import shutil
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
        self.test_dir = tempfile.mkdtemp()
        self.raw_logs_path = os.path.join(self.test_dir, 'raw_logs.csv')
        self.anonymized_logs_path = os.path.join(self.test_dir, 'anonymized_logs.csv')
        self.mapping_path = os.path.join(self.test_dir, 'mapping.json')
        
        # Create sample raw logs
        self.sample_logs = [
            {'participant_id': 'P001', 'task_id': 'T1', 'condition': 'llm', 'timestamp_ms': '1000', 'selected_line': '5', 'ground_truth_line': '6'},
            {'participant_id': 'P001', 'task_id': 'T2', 'condition': 'rule', 'timestamp_ms': '2000', 'selected_line': '7', 'ground_truth_line': '8'},
            {'participant_id': 'P002', 'task_id': 'T1', 'condition': 'baseline', 'timestamp_ms': '3000', 'selected_line': '9', 'ground_truth_line': '10'},
            {'participant_id': 'P003', 'task_id': 'T3', 'condition': 'llm', 'timestamp_ms': '4000', 'selected_line': '11', 'ground_truth_line': '12'},
        ]
        
        with open(self.raw_logs_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.sample_logs[0].keys())
            writer.writeheader()
            writer.writerows(self.sample_logs)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_raw_logs(self):
        """Test loading raw logs from CSV."""
        logs = load_raw_logs(self.raw_logs_path)
        self.assertEqual(len(logs), 4)
        self.assertIn('participant_id', logs[0])
        self.assertEqual(logs[0]['participant_id'], 'P001')

    def test_create_anonymization_mapping(self):
        """Test creation of deterministic anonymization mapping."""
        salt = 'test-salt-123'
        mapping = create_anonymization_mapping(self.sample_logs, salt)
        
        # Should have 3 unique participants
        self.assertEqual(len(mapping), 3)
        
        # Check that P001, P002, P003 are mapped
        self.assertIn('P001', mapping)
        self.assertIn('P002', mapping)
        self.assertIn('P003', mapping)
        
        # Check format of anonymized IDs
        for anon_id in mapping.values():
            self.assertTrue(anon_id.startswith('ANON_'))
            self.assertEqual(len(anon_id), 17)  # ANON_ + 12 chars

    def test_anonymization_determinism(self):
        """Test that anonymization is deterministic with same salt."""
        salt = 'determinism-test'
        mapping1 = create_anonymization_mapping(self.sample_logs, salt)
        mapping2 = create_anonymization_mapping(self.sample_logs, salt)
        
        self.assertEqual(mapping1, mapping2)

    def test_anonymization_different_salt(self):
        """Test that different salt produces different mapping."""
        mapping1 = create_anonymization_mapping(self.sample_logs, 'salt-1')
        mapping2 = create_anonymization_mapping(self.sample_logs, 'salt-2')
        
        # At least some mappings should be different
        self.assertNotEqual(mapping1, mapping2)

    def test_anonymize_logs(self):
        """Test that participant IDs are replaced correctly."""
        salt = 'test-salt'
        mapping = create_anonymization_mapping(self.sample_logs, salt)
        anonymized = anonymize_logs(self.sample_logs, mapping)
        
        # All participant IDs should be anonymized
        for log in anonymized:
            self.assertTrue(log['participant_id'].startswith('ANON_'))
        
        # Original IDs should not appear
        for log in anonymized:
            self.assertNotIn(log['participant_id'], ['P001', 'P002', 'P003'])

    def test_save_and_load_anonymized_logs(self):
        """Test saving and loading anonymized logs."""
        salt = 'test-salt'
        mapping = create_anonymization_mapping(self.sample_logs, salt)
        anonymized = anonymize_logs(self.sample_logs, mapping)
        
        save_anonymized_logs(anonymized, self.anonymized_logs_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.anonymized_logs_path))
        
        # Verify content
        with open(self.anonymized_logs_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 4)
        self.assertTrue(rows[0]['participant_id'].startswith('ANON_'))

    def test_save_anonymization_mapping(self):
        """Test saving anonymization mapping securely."""
        salt = 'test-salt'
        mapping = create_anonymization_mapping(self.sample_logs, salt)
        
        save_anonymization_mapping(mapping, self.mapping_path, self.test_dir)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.mapping_path))
        
        # Verify content structure
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('mapping', data)
        self.assertIn('created_at', data)
        self.assertIn('note', data)
        
        # Verify permissions (owner read/write only)
        file_stat = os.stat(self.mapping_path)
        mode = file_stat.st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_preserves_other_fields(self):
        """Test that non-participant fields are preserved."""
        salt = 'test-salt'
        mapping = create_anonymization_mapping(self.sample_logs, salt)
        anonymized = anonymize_logs(self.sample_logs, mapping)
        
        for original, anon in zip(self.sample_logs, anonymized):
            # task_id, condition, timestamp_ms, selected_line, ground_truth_line should be preserved
            self.assertEqual(original['task_id'], anon['task_id'])
            self.assertEqual(original['condition'], anon['condition'])
            self.assertEqual(original['timestamp_ms'], anon['timestamp_ms'])
            self.assertEqual(original['selected_line'], anon['selected_line'])
            self.assertEqual(original['ground_truth_line'], anon['ground_truth_line'])

if __name__ == '__main__':
    unittest.main()