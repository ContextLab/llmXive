import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

# We need to mock the settings to use a temp directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.cache_manager import compute_checksum, save_to_cache, load_from_cache, is_cached


class TestCacheManager(TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = {
            "name": "test-package",
            "version": "1.0.0",
            "dependencies": ["lodash", "express"]
        }
        self.cache_key = "test_npm_package"
    
    def test_compute_checksum_deterministic(self):
        """Checksum must be deterministic for the same input."""
        checksum1 = compute_checksum(self.test_data)
        checksum2 = compute_checksum(self.test_data)
        self.assertEqual(checksum1, checksum2)
        self.assertEqual(len(checksum1), 64)  # SHA-256 hex length
    
    def test_compute_checksum_different_data(self):
        """Different data must produce different checksums."""
        data_a = {"key": "value"}
        data_b = {"key": "different"}
        self.assertNotEqual(compute_checksum(data_a), compute_checksum(data_b))
    
    def test_compute_checksum_string_input(self):
        """Must handle string input correctly."""
        s = "test string"
        checksum = compute_checksum(s)
        self.assertEqual(len(checksum), 64)
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_save_to_cache_creates_file(self, mock_get_data_dir):
        """Saving data should create a file with correct naming."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        saved_path = save_to_cache(self.cache_key, self.test_data)
        
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.suffix, ".json")
        
        # Verify content
        with open(saved_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, self.test_data)
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_load_from_cache_success(self, mock_get_data_dir):
        """Loading should return data if checksum matches."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        checksum = compute_checksum(self.test_data)
        save_to_cache(self.cache_key, self.test_data)
        
        loaded = load_from_cache(self.cache_key, checksum)
        self.assertEqual(loaded, self.test_data)
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_load_from_cache_wrong_checksum(self, mock_get_data_dir):
        """Loading should return None if checksum doesn't match."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        checksum = compute_checksum(self.test_data)
        save_to_cache(self.cache_key, self.test_data)
        
        # Try with wrong checksum
        wrong_checksum = "0" * 64
        loaded = load_from_cache(self.cache_key, wrong_checksum)
        self.assertIsNone(loaded)
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_is_cached_true(self, mock_get_data_dir):
        """is_cached should return True for valid cache."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        checksum = compute_checksum(self.test_data)
        save_to_cache(self.cache_key, self.test_data)
        
        self.assertTrue(is_cached(self.cache_key, checksum))
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_is_cached_false_missing_file(self, mock_get_data_dir):
        """is_cached should return False if file doesn't exist."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        checksum = compute_checksum(self.test_data)
        self.assertFalse(is_cached(self.cache_key, checksum))
    
    @patch('src.utils.cache_manager.get_data_dir')
    def test_save_does_not_overwrite_existing(self, mock_get_data_dir):
        """Saving existing checksum should not overwrite file (immutability)."""
        temp_path = Path(self.temp_dir)
        mock_get_data_dir.return_value = temp_path
        
        checksum = compute_checksum(self.test_data)
        path1 = save_to_cache(self.cache_key, self.test_data)
        mtime1 = path1.stat().st_mtime
        
        # Save again with same data
        path2 = save_to_cache(self.cache_key, self.test_data)
        mtime2 = path2.stat().st_mtime
        
        # Paths should be identical
        self.assertEqual(path1, path2)
        # Modification time should not change (file not rewritten)
        self.assertEqual(mtime1, mtime2)
