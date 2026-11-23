"""
test_record_nlcd_provenance.py

Unit tests for the record_nlcd_provenance module.
"""

import os
import sys
import unittest
import tempfile
import yaml
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.record_nlcd_provenance import (
    load_metadata,
    save_metadata,
    verify_nlcd_file_exists,
    compute_and_record_hash,
    record_nlcd_provenance,
    NLCD_FILENAME,
    NLCD_VERSION
)
from utils.config import get_data_dir, get_raw_data_dir

class TestRecordNLCDProvenance(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_data_dir = Path(self.temp_dir) / "raw"
        self.data_dir = Path(self.temp_dir) / "data"
        self.raw_data_dir.mkdir()
        self.data_dir.mkdir()

        # Create a dummy NLCD file
        self.nlcd_file_path = self.raw_data_dir / NLCD_FILENAME
        with open(self.nlcd_file_path, 'w') as f:
            f.write("dummy nlcd content for testing")

        # Create a dummy metadata file
        self.metadata_path = self.data_dir / "metadata.yaml"
        with open(self.metadata_path, 'w') as f:
            yaml.dump({"existing_key": "existing_value"}, f)

        # Patch config functions temporarily
        self.original_get_data_dir = get_data_dir
        self.original_get_raw_data_dir = get_raw_data_dir
        
        # We will pass paths directly to functions in tests to avoid global config patching complexity
        # but the module imports these, so we ensure the module logic works with passed paths.

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_verify_nlcd_file_exists_success(self):
        """Test that verify_nlcd_file_exists returns the path if file exists."""
        result = verify_nlcd_file_exists(self.raw_data_dir)
        self.assertEqual(result, self.nlcd_file_path)

    def test_verify_nlcd_file_exists_failure(self):
        """Test that verify_nlcd_file_exists raises FileNotFoundError if file missing."""
        empty_dir = self.temp_dir + "/empty"
        os.makedirs(empty_dir)
        with self.assertRaises(FileNotFoundError):
            verify_nlcd_file_exists(Path(empty_dir))

    def test_load_metadata_existing(self):
        """Test loading existing metadata."""
        data = load_metadata(self.metadata_path)
        self.assertEqual(data.get("existing_key"), "existing_value")

    def test_load_metadata_missing(self):
        """Test loading non-existing metadata returns empty dict."""
        missing_path = Path(self.temp_dir) / "nonexistent.yaml"
        data = load_metadata(missing_path)
        self.assertEqual(data, {})

    def test_save_metadata(self):
        """Test saving metadata to a new file."""
        test_path = Path(self.temp_dir) / "test_metadata.yaml"
        test_data = {"key": "value", "nested": {"a": 1}}
        save_metadata(test_path, test_data)
        
        self.assertTrue(test_path.exists())
        with open(test_path, 'r') as f:
            loaded = yaml.safe_load(f)
        self.assertEqual(loaded["key"], "value")
        self.assertEqual(loaded["nested"]["a"], 1)

    def test_compute_and_record_hash(self):
        """Test hash computation."""
        file_hash = compute_and_record_hash(self.nlcd_file_path)
        self.assertIsInstance(file_hash, str)
        self.assertEqual(len(file_hash), 64) # SHA-256 hex length

    def test_record_nlcd_provenance_updates_metadata(self):
        """Test that record_nlcd_provenance correctly updates the metadata dict."""
        # Load initial metadata
        metadata = load_metadata(self.metadata_path)
        
        # Compute hash first
        file_hash = compute_and_record_hash(self.nlcd_file_path)
        
        # Record provenance
        updated_metadata = record_nlcd_provenance(metadata, self.nlcd_file_path, file_hash)
        
        # Assertions
        self.assertIn('nlcd', updated_metadata)
        self.assertEqual(updated_metadata['nlcd']['version'], NLCD_VERSION)
        self.assertEqual(updated_metadata['nlcd']['filename'], NLCD_FILENAME)
        self.assertEqual(updated_metadata['nlcd']['file_hash_sha256'], file_hash)
        self.assertIn('source_url', updated_metadata['nlcd'])
        self.assertIn('downloaded_at', updated_metadata['nlcd'])
        self.assertIn('recorded_at', updated_metadata['nlcd'])
        self.assertEqual(updated_metadata['existing_key'], "existing_value") # Preserved

if __name__ == '__main__':
    unittest.main()