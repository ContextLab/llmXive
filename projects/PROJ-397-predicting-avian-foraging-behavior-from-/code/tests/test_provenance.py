"""
Unit tests for the utils/provenance.py module.
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.provenance import (
    compute_file_hash,
    compute_data_hash,
    generate_provenance_record,
    load_metadata_config,
    save_metadata_config,
    save_provenance_record,
    record_source_info,
    log_step,
    verify_data_integrity,
    load_provenance_records,
    record_artifact_provenance
)
from utils.config import get_metadata_file

class TestProvenance(unittest.TestCase):
    """Test cases for provenance functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("Hello, World!")
        
        # Backup original metadata file if it exists
        self.metadata_path = get_metadata_file()
        self.original_metadata = None
        if self.metadata_path.exists():
            self.original_metadata = self.metadata_path.read_text()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Restore original metadata file
        if self.original_metadata is not None:
            self.metadata_path.write_text(self.original_metadata)
        elif self.metadata_path.exists():
            self.metadata_path.unlink()

    def test_compute_file_hash_returns_string(self):
        """Test that compute_file_hash returns a hexadecimal string."""
        hash_value = compute_file_hash(self.test_file)
        self.assertIsInstance(hash_value, str)
        self.assertEqual(len(hash_value), 64)  # SHA-256 hex length

    def test_compute_file_hash_deterministic(self):
        """Test that compute_file_hash is deterministic."""
        hash1 = compute_file_hash(self.test_file)
        hash2 = compute_file_hash(self.test_file)
        self.assertEqual(hash1, hash2)

    def test_compute_data_hash_returns_string(self):
        """Test that compute_data_hash returns a hexadecimal string."""
        data = {"key": "value"}
        hash_value = compute_data_hash(data)
        self.assertIsInstance(hash_value, str)
        self.assertEqual(len(hash_value), 64)

    def test_compute_data_hash_deterministic(self):
        """Test that compute_data_hash is deterministic."""
        data = {"key": "value"}
        hash1 = compute_data_hash(data)
        hash2 = compute_data_hash(data)
        self.assertEqual(hash1, hash2)

    def test_generate_provenance_record_returns_dict(self):
        """Test that generate_provenance_record returns a dictionary."""
        record = generate_provenance_record(
            source_url="http://example.com",
            version="1.0",
            extraction_date="2023-10-27"
        )
        self.assertIsInstance(record, dict)
        self.assertIn("source_url", record)
        self.assertIn("version", record)
        self.assertIn("extraction_date", record)

    def test_save_and_load_metadata_config(self):
        """Test saving and loading metadata configuration."""
        test_metadata = {"test_key": "test_value"}
        save_metadata_config(test_metadata)
        loaded_metadata = load_metadata_config()
        self.assertEqual(loaded_metadata.get("test_key"), "test_value")

    def test_save_provenance_record(self):
        """Test saving a provenance record."""
        record = generate_provenance_record(
            source_url="http://example.com",
            version="1.0",
            extraction_date="2023-10-27"
        )
        save_provenance_record("test_source", record)
        
        metadata = load_metadata_config()
        self.assertIn("sources", metadata)
        self.assertIn("test_source", metadata["sources"])
        self.assertEqual(metadata["sources"]["test_source"]["source_url"], "http://example.com")

    def test_record_source_info(self):
        """Test recording source info with hash."""
        record_source_info(
            source_name="test_file",
            source_url="http://example.com",
            version="1.0",
            file_path=self.test_file,
            notes="Test note"
        )
        
        metadata = load_metadata_config()
        self.assertIn("sources", metadata)
        self.assertIn("test_file", metadata["sources"])
        self.assertIsNotNone(metadata["sources"]["test_file"]["hash"])

    def test_log_step(self):
        """Test logging a pipeline step."""
        log_step("test_step", "completed", "Test details")
        
        metadata = load_metadata_config()
        self.assertIn("execution_log", metadata)
        self.assertEqual(len(metadata["execution_log"]), 1)
        self.assertEqual(metadata["execution_log"][0]["step"], "test_step")

    def test_verify_data_integrity(self):
        """Test verifying data integrity."""
        # First, record the file
        hash_value = compute_file_hash(self.test_file)
        record_source_info(
            source_name="verify_test",
            source_url="http://example.com",
            version="1.0",
            file_path=self.test_file
        )
        
        # Then verify
        self.assertTrue(verify_data_integrity("verify_test", hash_value))
        self.assertFalse(verify_data_integrity("verify_test", "wrong_hash"))

    def test_load_provenance_records(self):
        """Test loading all provenance records."""
        record = generate_provenance_record(
            source_url="http://example.com",
            version="1.0",
            extraction_date="2023-10-27"
        )
        save_provenance_record("recorded_source", record)
        
        records = load_provenance_records()
        self.assertIn("recorded_source", records)

    def test_record_artifact_provenance(self):
        """Test recording artifact provenance."""
        record_artifact_provenance(
            artifact_name="test_artifact",
            file_path=self.test_file,
            source_url="http://example.com/script.py",
            version="1.0",
            notes="Generated by test"
        )
        
        metadata = load_metadata_config()
        self.assertIn("sources", metadata)
        self.assertIn("test_artifact", metadata["sources"])

if __name__ == "__main__":
    import shutil
    unittest.main()