"""
Unit tests for download_nlcd.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from data.download_nlcd import compute_sha256, save_metadata
from utils.config import get_project_root, get_raw_data_dir, get_metadata_file

class TestDownloadNLCD(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_content = b"Hello, World!"
        with open(self.test_file, 'wb') as f:
            f.write(self.test_content)
        
        self.test_metadata_path = Path(self.temp_dir) / "test_metadata.yaml"
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_compute_sha256(self):
        """Test SHA-256 computation."""
        expected_hash = hashlib.sha256(self.test_content).hexdigest()
        computed_hash = compute_sha256(self.test_file)
        self.assertEqual(computed_hash, expected_hash)
    
    def test_save_metadata(self):
        """Test metadata saving functionality."""
        version = "test_version"
        download_date = "2023-01-01T00:00:00"
        checksum = "test_checksum"
        
        save_metadata(self.test_metadata_path, version, download_date, checksum)
        
        # Verify file exists
        self.assertTrue(self.test_metadata_path.exists())
        
        # Verify content
        with open(self.test_metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        self.assertIn('datasets', metadata)
        self.assertIn('nlcd_2019', metadata['datasets'])
        self.assertEqual(metadata['datasets']['nlcd_2019']['version'], version)
        self.assertEqual(metadata['datasets']['nlcd_2019']['download_date'], download_date)
        self.assertEqual(metadata['datasets']['nlcd_2019']['checksum'], checksum)
    
    def test_save_metadata_existing(self):
        """Test saving to existing metadata file."""
        # Create initial metadata
        initial_data = {
            'datasets': {
                'ebd_train': {
                    'source_url': 's3://test',
                    'version': 'v1'
                }
            }
        }
        with open(self.test_metadata_path, 'w') as f:
            yaml.dump(initial_data, f)
        
        save_metadata(self.test_metadata_path, "v2", "2023-01-01", "checksum123")
        
        with open(self.test_metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        # Verify both datasets exist
        self.assertIn('ebd_train', metadata['datasets'])
        self.assertIn('nlcd_2019', metadata['datasets'])

if __name__ == '__main__':
    unittest.main()