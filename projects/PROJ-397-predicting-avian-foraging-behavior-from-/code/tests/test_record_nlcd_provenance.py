"""
Unit tests for the NLCD provenance recording functionality.

Tests verify that:
1. NLCD provenance information is correctly recorded in metadata
2. Required fields are present and have correct values
3. File hash is computed when file exists
4. Graceful handling when file doesn't exist
"""
import os
import sys
import unittest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.record_nlcd_provenance import (
    load_metadata,
    save_metadata,
    record_nlcd_provenance,
    verify_nlcd_file_exists,
    compute_and_record_hash,
    NLCD_2019_VERSION,
    NLCD_2019_SOURCE_URL,
    NLCD_2019_CITATION
)

class TestRecordNLCDProvenance(unittest.TestCase):
    """Test cases for NLCD provenance recording."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_path = Path(self.temp_dir) / "metadata.yaml"
        self.raw_data_dir = Path(self.temp_dir) / "raw"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_nlcd_provenance_creates_section(self):
        """Test that record_nlcd_provenance creates the nlcd section."""
        metadata = {}
        result = record_nlcd_provenance(metadata)
        
        self.assertIn('nlcd', result)
        self.assertIsInstance(result['nlcd'], dict)

    def test_record_nlcd_provenance_required_fields(self):
        """Test that all required provenance fields are recorded."""
        metadata = {}
        result = record_nlcd_provenance(metadata)
        
        nlcd = result['nlcd']
        
        # Check required fields exist
        required_fields = [
            'version',
            'release_date',
            'source_url',
            'citation',
            'extraction_date'
        ]
        
        for field in required_fields:
            self.assertIn(field, nlcd, f"Missing required field: {field}")

    def test_record_nlcd_provenance_correct_values(self):
        """Test that provenance fields have correct values."""
        metadata = {}
        result = record_nlcd_provenance(metadata)
        
        nlcd = result['nlcd']
        
        self.assertEqual(nlcd['version'], NLCD_2019_VERSION)
        self.assertEqual(nlcd['source_url'], NLCD_2019_SOURCE_URL)
        self.assertEqual(nlcd['citation'], NLCD_2019_CITATION)
        
        # Check extraction_date is valid ISO format
        extraction_date = datetime.fromisoformat(nlcd['extraction_date'])
        self.assertIsInstance(extraction_date, datetime)

    def test_record_nlcd_provenance_preserves_existing_data(self):
        """Test that record_nlcd_provenance doesn't overwrite existing data."""
        metadata = {
            'ebd': {
                'version': 'v1.0',
                'source': 'eBird'
            },
            'other_field': 'some_value'
        }
        
        result = record_nlcd_provenance(metadata)
        
        # Check existing data preserved
        self.assertEqual(result['ebd']['version'], 'v1.0')
        self.assertEqual(result['other_field'], 'some_value')
        
        # Check nlcd section added
        self.assertIn('nlcd', result)

    def test_load_and_save_metadata(self):
        """Test loading and saving metadata to/from YAML."""
        test_metadata = {
            'test_field': 'test_value',
            'nested': {
                'key': 'value'
            }
        }
        
        # Save metadata
        save_metadata(test_metadata, self.metadata_path)
        
        # Load metadata
        loaded_metadata = load_metadata(self.metadata_path)
        
        # Verify content
        self.assertEqual(loaded_metadata['test_field'], 'test_value')
        self.assertEqual(loaded_metadata['nested']['key'], 'value')

    def test_load_metadata_nonexistent_file(self):
        """Test loading metadata from non-existent file returns empty dict."""
        non_existent_path = Path(self.temp_dir) / "nonexistent.yaml"
        result = load_metadata(non_existent_path)
        
        self.assertEqual(result, {})

    def test_verify_nlcd_file_exists_found(self):
        """Test that verify_nlcd_file_exists finds NLCD file when present."""
        # Create a mock NLCD file
        mock_nlcd_file = self.raw_data_dir / "nlcd_2019.zip"
        mock_nlcd_file.touch()
        
        result = verify_nlcd_file_exists(self.raw_data_dir)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "nlcd_2019.zip")

    def test_verify_nlcd_file_exists_not_found(self):
        """Test that verify_nlcd_file_exists returns None when file missing."""
        result = verify_nlcd_file_exists(self.raw_data_dir)
        
        self.assertIsNone(result)

    def test_compute_and_record_hash(self):
        """Test that hash is computed and recorded correctly."""
        # Create a test file
        test_file = self.raw_data_dir / "test_file.txt"
        test_content = b"Test content for hashing"
        test_file.write_bytes(test_content)
        
        metadata = {}
        result = compute_and_record_hash(test_file, metadata)
        
        # Check hash was recorded
        self.assertIn('file_hash', result['nlcd'])
        self.assertIn('file_size_bytes', result['nlcd'])
        self.assertIn('file_name', result['nlcd'])
        
        # Verify hash length (SHA-256 produces 64 hex characters)
        self.assertEqual(len(result['nlcd']['file_hash']), 64)
        
        # Verify file size
        self.assertEqual(result['nlcd']['file_size_bytes'], len(test_content))

    def test_compute_and_record_hash_missing_file(self):
        """Test graceful handling when file doesn't exist."""
        non_existent_file = self.raw_data_dir / "nonexistent.txt"
        metadata = {}
        
        # Should not raise exception
        result = compute_and_record_hash(non_existent_file, metadata)
        
        # Hash should not be recorded
        self.assertNotIn('file_hash', result.get('nlcd', {}))

    def test_full_workflow(self):
        """Test the complete workflow of recording NLCD provenance."""
        # Create mock NLCD file
        mock_nlcd_file = self.raw_data_dir / "nlcd_2019.zip"
        mock_nlcd_file.write_bytes(b"Mock NLCD data")
        
        # Load empty metadata
        metadata = load_metadata(self.metadata_path)
        
        # Record provenance
        metadata = record_nlcd_provenance(metadata)
        
        # Record file hash
        metadata = compute_and_record_hash(mock_nlcd_file, metadata)
        
        # Save metadata
        save_metadata(metadata, self.metadata_path)
        
        # Reload and verify
        final_metadata = load_metadata(self.metadata_path)
        
        # Verify all components
        self.assertIn('nlcd', final_metadata)
        self.assertEqual(final_metadata['nlcd']['version'], NLCD_2019_VERSION)
        self.assertIn('file_hash', final_metadata['nlcd'])
        self.assertEqual(final_metadata['nlcd']['file_name'], "nlcd_2019.zip")

if __name__ == '__main__':
    unittest.main()