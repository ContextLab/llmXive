"""
Unit tests for the provenance module.
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
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
from utils.config import get_metadata_file


class TestProvenance(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_data.txt"
        self.test_file.write_text("test content for provenance")
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_file_hash(self):
        """Test SHA-256 hash computation for a file."""
        hash_value = compute_file_hash(self.test_file)
        self.assertEqual(len(hash_value), 64)  # SHA-256 hex length
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))
    
    def test_compute_file_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(Path("/nonexistent/file.txt"))
    
    def test_compute_data_hash(self):
        """Test hash computation for serializable data."""
        data = {"key": "value", "number": 42}
        hash1 = compute_data_hash(data)
        hash2 = compute_data_hash(data)
        self.assertEqual(hash1, hash2)  # Deterministic
        self.assertEqual(len(hash1), 64)
    
    def test_generate_provenance_record(self):
        """Test generation of a provenance record."""
        record = generate_provenance_record(
            file_path=self.test_file,
            source_url="https://example.com/data",
            version="1.0",
            extraction_date="2024-01-01T00:00:00",
            additional_metadata={"test": "value"}
        )
        
        self.assertIn("file_path", record)
        self.assertIn("sha256_hash", record)
        self.assertIn("source_url", record)
        self.assertEqual(record["source_url"], "https://example.com/data")
        self.assertEqual(record["version"], "1.0")
    
    def test_save_provenance_record(self):
        """Test saving provenance record to metadata file."""
        record = generate_provenance_record(self.test_file)
        metadata_file = Path(self.temp_dir) / "metadata.yaml"
        
        saved_file = save_provenance_record(record, metadata_file)
        
        self.assertTrue(saved_file.exists())
        
        # Verify content
        with open(saved_file, 'r') as f:
            content = f.read()
        self.assertIn("provenance", content)
        self.assertIn(self.test_file.name, content)
    
    def test_log_step(self):
        """Test logging a pipeline step."""
        input_file = Path(self.temp_dir) / "input.txt"
        output_file = Path(self.temp_dir) / "output.txt"
        input_file.write_text("input")
        output_file.write_text("output")
        
        metadata_file = Path(self.temp_dir) / "metadata.yaml"
        
        logged_file = log_step(
            step_name="test_step",
            input_files=[input_file],
            output_files=[output_file],
            parameters={"param1": "value1"},
            metadata_file=metadata_file
        )
        
        self.assertTrue(logged_file.exists())
        
        # Verify step was recorded
        records = load_provenance_records(logged_file)
        # Note: log_step writes to pipeline_log, not provenance
        # We check the file exists and has content
        with open(logged_file, 'r') as f:
            content = f.read()
        self.assertIn("test_step", content)
    
    def test_verify_data_integrity(self):
        """Test data integrity verification."""
        hash_value = compute_file_hash(self.test_file)
        self.assertTrue(verify_data_integrity(self.test_file, hash_value))
        self.assertFalse(verify_data_integrity(self.test_file, "wrong_hash"))
    
    def test_verify_data_integrity_invalid_algorithm(self):
        """Test that ValueError is raised for unsupported algorithm."""
        with self.assertRaises(ValueError):
            verify_data_integrity(self.test_file, "hash", hash_algorithm="md5")
    
    def test_load_provenance_records(self):
        """Test loading provenance records from metadata file."""
        record = generate_provenance_record(self.test_file)
        metadata_file = Path(self.temp_dir) / "metadata.yaml"
        save_provenance_record(record, metadata_file)
        
        records = load_provenance_records(metadata_file)
        self.assertIn("artifacts", records)
        self.assertEqual(len(records["artifacts"]), 1)
