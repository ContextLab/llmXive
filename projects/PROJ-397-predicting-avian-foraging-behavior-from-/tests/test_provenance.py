"""
Unit tests for the provenance tracking module.
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
import hashlib

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.provenance import (
    compute_file_hash,
    compute_data_hash,
    generate_provenance_record,
    load_metadata_config,
    save_metadata_config,
    save_provenance_record,
    record_source_info,
    verify_data_integrity,
    load_provenance_records,
    record_artifact_provenance
)
from utils.config import get_metadata_file


class TestProvenance(unittest.TestCase):
    """Test cases for provenance tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("Hello, World!")
        
        # Create a temporary metadata file
        self.temp_metadata = Path(self.temp_dir) / "test_metadata.yaml"
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_file_hash(self):
        """Test SHA-256 hash computation for a file."""
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_file_hash(self.test_file)
        self.assertEqual(actual_hash, expected_hash)
    
    def test_compute_file_hash_nonexistent(self):
        """Test that computing hash for nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(Path(self.temp_dir) / "nonexistent.txt")
    
    def test_compute_data_hash(self):
        """Test hash computation for serialized data."""
        test_data = {"key": "value", "number": 42}
        serialized = json.dumps(test_data, sort_keys=True).encode('utf-8')
        expected_hash = hashlib.sha256(serialized).hexdigest()
        actual_hash = compute_data_hash(test_data)
        self.assertEqual(actual_hash, expected_hash)
    
    def test_generate_provenance_record(self):
        """Test generation of a complete provenance record."""
        record = generate_provenance_record(
            artifact_name="test_artifact",
            file_path=self.test_file,
            source_url="https://example.com/data",
            version="1.0",
            extraction_date="2023-10-27T12:00:00Z"
        )
        
        self.assertEqual(record["artifact_name"], "test_artifact")
        self.assertEqual(record["source_url"], "https://example.com/data")
        self.assertEqual(record["version"], "1.0")
        self.assertIn("checksum", record)
        self.assertIn("file_size_bytes", record)
        self.assertEqual(record["extraction_date"], "2023-10-27T12:00:00Z")
    
    def test_generate_provenance_record_auto_date(self):
        """Test that extraction_date is auto-generated if not provided."""
        record = generate_provenance_record(
            artifact_name="test_artifact",
            file_path=self.test_file
        )
        
        self.assertIn(record["extraction_date"], ["", None] or len(record["extraction_date"]) > 0)
    
    def test_save_and_load_metadata_config(self):
        """Test saving and loading metadata configuration."""
        test_metadata = {
            "datasets": {"test_dataset": {"url": "https://example.com"}},
            "artifacts": {"test_artifact": {"checksum": "abc123"}},
            "pipeline_runs": []
        }
        
        save_metadata_config(test_metadata, self.temp_metadata)
        loaded_metadata = load_metadata_config(self.temp_metadata)
        
        self.assertEqual(loaded_metadata, test_metadata)
    
    def test_load_nonexistent_metadata(self):
        """Test loading nonexistent metadata returns empty structure."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.yaml"
        metadata = load_metadata_config(nonexistent_path)
        
        self.assertEqual(metadata, {"datasets": {}, "artifacts": {}, "pipeline_runs": []})
    
    def test_save_provenance_record(self):
        """Test saving a provenance record to metadata."""
        record = {
            "artifact_name": "test_record",
            "file_path": str(self.test_file),
            "checksum": "abc123"
        }
        
        save_provenance_record(record, category="artifacts", metadata_path=self.temp_metadata)
        
        loaded = load_metadata_config(self.temp_metadata)
        self.assertIn("test_record", loaded["artifacts"])
        self.assertEqual(loaded["artifacts"]["test_record"]["checksum"], "abc123")
    
    def test_record_source_info(self):
        """Test recording source information for external dataset."""
        record_source_info(
            dataset_name="test_dataset",
            source_url="https://example.com/data.csv",
            version="1.0",
            local_path=self.test_file,
            extraction_date="2023-10-27T12:00:00Z"
        )
        
        # Load and verify
        loaded = load_metadata_config(get_metadata_file())
        self.assertIn("test_dataset", loaded["datasets"])
        self.assertEqual(loaded["datasets"]["test_dataset"]["source_url"], "https://example.com/data.csv")
    
    def test_verify_data_integrity_match(self):
        """Test integrity verification with matching checksum."""
        expected_hash = compute_file_hash(self.test_file)
        result = verify_data_integrity(self.test_file, expected_hash)
        self.assertTrue(result)
    
    def test_verify_data_integrity_mismatch(self):
        """Test integrity verification with mismatched checksum."""
        result = verify_data_integrity(self.test_file, "wrong_checksum")
        self.assertFalse(result)
    
    def test_load_provenance_records(self):
        """Test loading provenance records by category."""
        # First, save some records
        record1 = {"artifact_name": "record1", "checksum": "abc"}
        record2 = {"artifact_name": "record2", "checksum": "def"}
        
        save_provenance_record(record1, category="artifacts", metadata_path=self.temp_metadata)
        save_provenance_record(record2, category="datasets", metadata_path=self.temp_metadata)
        
        # Load and verify
        artifacts = load_provenance_records(category="artifacts", metadata_path=self.temp_metadata)
        datasets = load_provenance_records(category="datasets", metadata_path=self.temp_metadata)
        
        self.assertIn("record1", artifacts)
        self.assertIn("record2", datasets)
    
    def test_record_artifact_provenance(self):
        """Test the convenience function for recording artifact provenance."""
        record = record_artifact_provenance(
            artifact_name="convenience_test",
            file_path=self.test_file,
            source_url="https://example.com",
            version="1.0"
        )
        
        self.assertEqual(record["artifact_name"], "convenience_test")
        self.assertEqual(record["source_url"], "https://example.com")
        self.assertIn("checksum", record)
    
    def test_metadata_structure_after_operations(self):
        """Test that metadata maintains correct structure after multiple operations."""
        # Create initial metadata
        initial = {
            "datasets": {},
            "artifacts": {},
            "pipeline_runs": []
        }
        save_metadata_config(initial, self.temp_metadata)
        
        # Add some records
        record_source_info(
            dataset_name="ds1",
            source_url="https://example.com",
            version="1.0",
            local_path=self.test_file,
            metadata_path=self.temp_metadata
        )
        
        record = generate_provenance_record(
            artifact_name="art1",
            file_path=self.test_file,
            metadata_path=self.temp_metadata
        )
        save_provenance_record(record, category="artifacts", metadata_path=self.temp_metadata)
        
        # Verify structure
        loaded = load_metadata_config(self.temp_metadata)
        self.assertIn("datasets", loaded)
        self.assertIn("artifacts", loaded)
        self.assertIn("pipeline_runs", loaded)
        self.assertEqual(len(loaded["datasets"]), 1)
        self.assertEqual(len(loaded["artifacts"]), 1)


if __name__ == "__main__":
    unittest.main()