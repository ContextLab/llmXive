"""
Unit tests for the provenance module.

Tests verify:
1. SHA-256 hash computation for files and data
2. Provenance record generation and saving
3. Metadata file management
4. Data integrity verification
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.provenance import (
    compute_file_hash,
    compute_data_hash,
    generate_provenance_record,
    save_provenance_record,
    log_step,
    verify_data_integrity,
    load_provenance_records,
    record_artifact_provenance
)
from utils.config import get_metadata_file


class TestProvenance(unittest.TestCase):
    """Test suite for provenance module functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_file.txt"
        
        # Create a test file with known content
        test_content = "This is test content for provenance verification."
        self.test_file.write_text(test_content)
        
        # Expected hash for the test content
        import hashlib
        self.expected_hash = hashlib.sha256(test_content.encode('utf-8')).hexdigest()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_compute_file_hash(self):
        """Test SHA-256 hash computation for a file."""
        actual_hash = compute_file_hash(self.test_file)
        self.assertEqual(actual_hash, self.expected_hash)

    def test_compute_file_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        nonexistent = Path(self.temp_dir.name) / "nonexistent.txt"
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(nonexistent)

    def test_compute_data_hash(self):
        """Test hash computation for serializable data."""
        test_data = {"key": "value", "number": 42}
        hash1 = compute_data_hash(test_data)
        hash2 = compute_data_hash(test_data)
        
        # Same data should produce same hash
        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex length

    def test_generate_provenance_record(self):
        """Test provenance record generation."""
        record = generate_provenance_record(
            artifact_path=self.test_file,
            source_url="https://example.com/data",
            version="1.0",
            artifact_type="test_data",
            description="Test artifact"
        )
        
        self.assertEqual(record["artifact_path"], str(self.test_file))
        self.assertEqual(record["file_hash"], self.expected_hash)
        self.assertEqual(record["source_url"], "https://example.com/data")
        self.assertEqual(record["version"], "1.0")
        self.assertEqual(record["artifact_type"], "test_data")
        self.assertIn("created_at", record)
        self.assertIn("file_size_bytes", record)

    def test_save_provenance_record(self):
        """Test saving provenance record to metadata file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_metadata = Path(f.name)
        
        try:
            record = generate_provenance_record(
                artifact_path=self.test_file,
                source_url="https://example.com/data",
                artifact_type="external_data"
            )
            
            save_provenance_record(record, temp_metadata)
            
            # Verify metadata file exists and contains the record
            self.assertTrue(temp_metadata.exists())
            
            loaded = load_provenance_records(temp_metadata)
            self.assertIn("external_sources", loaded)
            self.assertEqual(len(loaded["external_sources"]), 1)
            self.assertEqual(loaded["external_sources"][0]["source_url"], "https://example.com/data")
        finally:
            temp_metadata.unlink(missing_ok=True)

    def test_log_step(self):
        """Test pipeline step logging."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_metadata = Path(f.name)
        
        try:
            log_step("test_step", "completed", "Test message", temp_metadata)
            
            loaded = load_provenance_records(temp_metadata)
            self.assertIn("pipeline_execution_log", loaded)
            self.assertEqual(len(loaded["pipeline_execution_log"]), 1)
            
            entry = loaded["pipeline_execution_log"][0]
            self.assertEqual(entry["step_name"], "test_step")
            self.assertEqual(entry["status"], "completed")
            self.assertEqual(entry["message"], "Test message")
        finally:
            temp_metadata.unlink(missing_ok=True)

    def test_verify_data_integrity(self):
        """Test data integrity verification."""
        # Valid verification
        is_valid = verify_data_integrity(self.test_file, self.expected_hash)
        self.assertTrue(is_valid)
        
        # Invalid verification
        is_invalid = verify_data_integrity(self.test_file, "wrong_hash")
        self.assertFalse(is_invalid)

    def test_record_artifact_provenance(self):
        """Test the convenience function for recording artifact provenance."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_metadata = Path(f.name)
        
        try:
            record = record_artifact_provenance(
                artifact_path=self.test_file,
                source_url="https://example.com/data",
                artifact_type="test_artifact",
                description="Test artifact",
                metadata_file=temp_metadata
            )
            
            self.assertEqual(record["file_hash"], self.expected_hash)
            
            # Verify it was saved
            loaded = load_provenance_records(temp_metadata)
            self.assertTrue(len(loaded["artifacts"]) > 0 or len(loaded.get("external_sources", [])) > 0)
        finally:
            temp_metadata.unlink(missing_ok=True)

    def test_load_provenance_records_empty(self):
        """Test loading from non-existent metadata file."""
        records = load_provenance_records(Path("/nonexistent/path/metadata.yaml"))
        self.assertEqual(records["artifacts"], [])
        self.assertEqual(records["external_sources"], [])
        self.assertEqual(records["pipeline_execution_log"], [])


if __name__ == "__main__":
    unittest.main()