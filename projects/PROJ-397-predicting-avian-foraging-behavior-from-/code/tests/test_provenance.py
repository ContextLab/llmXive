"""
Unit tests for the provenance module.
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.provenance import (
    compute_file_hash,
    compute_data_hash,
    generate_provenance_record,
    save_provenance_record,
    log_step,
    verify_data_integrity,
    load_provenance_records
)
from utils.config import get_data_dir


class TestProvenance(unittest.TestCase):
    """Test cases for the provenance module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        with open(self.test_file, 'w') as f:
            f.write("Test content for provenance testing.")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        hash_result = compute_file_hash(self.test_file)
        self.assertEqual(len(hash_result), 64)  # SHA-256 produces 64 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))

    def test_compute_file_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash("nonexistent_file.txt")

    def test_compute_data_hash(self):
        """Test data hash computation."""
        test_data = {"key": "value", "number": 42}
        hash_result = compute_data_hash(test_data)
        self.assertEqual(len(hash_result), 64)

    def test_compute_data_hash_consistency(self):
        """Test that the same data produces the same hash."""
        test_data = {"key": "value"}
        hash1 = compute_data_hash(test_data)
        hash2 = compute_data_hash(test_data)
        self.assertEqual(hash1, hash2)

    def test_generate_provenance_record(self):
        """Test provenance record generation."""
        record = generate_provenance_record(
            step_name="test_step",
            inputs={"input1": "path/to/file"},
            outputs={"output1": "path/to/result"},
            parameters={"param1": "value1"}
        )
        
        self.assertEqual(record['step_name'], "test_step")
        self.assertIn('timestamp', record)
        self.assertIn('record_id', record)
        self.assertEqual(record['inputs'], {"input1": "path/to/file"})
        self.assertEqual(record['parameters'], {"param1": "value1"})

    def test_save_provenance_record(self):
        """Test saving a provenance record."""
        record = generate_provenance_record(step_name="test_save")
        file_path = save_provenance_record(record, output_dir=self.temp_dir)
        
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.suffix, '.json')
        
        # Verify the content
        with open(file_path, 'r') as f:
            loaded_record = json.load(f)
        self.assertEqual(loaded_record['step_name'], "test_save")

    def test_log_step(self):
        """Test logging a pipeline step."""
        record = log_step(
            step_name="test_logging",
            status="completed",
            inputs={"input": "data"},
            parameters={"seed": 42}
        )
        
        self.assertEqual(record['status'], "completed")
        self.assertEqual(record['step_name'], "test_logging")
        self.assertIn('record_id', record)

    def test_verify_data_integrity(self):
        """Test data integrity verification."""
        file_hash = compute_file_hash(self.test_file)
        self.assertTrue(verify_data_integrity(self.test_file, file_hash))
        self.assertFalse(verify_data_integrity(self.test_file, "wrong_hash"))

    def test_verify_data_integrity_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            verify_data_integrity("nonexistent.txt", "some_hash")

    def test_load_provenance_records(self):
        """Test loading provenance records."""
        # Create a test record
        record = generate_provenance_record(step_name="test_load")
        save_provenance_record(record, output_dir=self.temp_dir)
        
        # Load records
        records = load_provenance_records(directory=self.temp_dir)
        self.assertGreaterEqual(len(records), 1)
        
        # Filter by step name
        filtered = load_provenance_records(directory=self.temp_dir, step_name="test_load")
        self.assertEqual(len(filtered), 1)

    def test_generate_provenance_record_with_metadata(self):
        """Test provenance record with additional metadata."""
        record = generate_provenance_record(
            step_name="test_metadata",
            metadata={"author": "test", "version": "1.0"}
        )
        
        self.assertEqual(record['metadata']['author'], "test")
        self.assertEqual(record['metadata']['version'], "1.0")


if __name__ == '__main__':
    unittest.main()