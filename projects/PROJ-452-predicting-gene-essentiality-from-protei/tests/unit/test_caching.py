"""
Unit tests for caching module (T041).
"""
import os
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.caching import (
    _ensure_cache_dir,
    _load_manifest,
    _save_manifest,
    _compute_key,
    _get_cache_path,
    _is_cache_valid,
    _save_to_cache,
    _load_from_cache,
    cache_result,
    clear_cache,
    profile_function
)

class TestCaching(unittest.TestCase):
    """Test cases for caching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_cache_dir = Path(tempfile.mkdtemp())
        self.original_cache_dir = Path("data/cache")
        
        # Mock cache directory
        import code.caching
        code.caching.CACHE_DIR = self.test_cache_dir
        code.caching.CACHE_MANIFEST = self.test_cache_dir / "manifest.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)

    def test_ensure_cache_dir(self):
        """Test that cache directory is created."""
        result = _ensure_cache_dir()
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())

    def test_load_manifest_empty(self):
        """Test loading non-existent manifest."""
        manifest = _load_manifest()
        self.assertIn("entries", manifest)
        self.assertEqual(len(manifest["entries"]), 0)

    def test_save_and_load_manifest(self):
        """Test saving and loading manifest."""
        test_manifest = {"entries": {"key1": {"created_at": 123}}}
        _save_manifest(test_manifest)
        
        loaded = _load_manifest()
        self.assertEqual(loaded["entries"]["key1"]["created_at"], 123)

    def test_compute_key(self):
        """Test cache key computation."""
        key1 = _compute_key("test", param1="a", param2=1)
        key2 = _compute_key("test", param2=1, param1="a")  # Same params, different order
        
        self.assertEqual(key1, key2)
        
        key3 = _compute_key("test", param1="b", param2=1)
        self.assertNotEqual(key1, key3)

    def test_cache_validity(self):
        """Test cache validity checking."""
        key = _compute_key("test")
        
        # Initially invalid
        self.assertFalse(_is_cache_valid(key))
        
        # Save to cache
        _save_to_cache(key, {"data": "test_value"})
        
        # Now valid
        self.assertTrue(_is_cache_valid(key))

    def test_save_and_load_from_cache(self):
        """Test saving and loading data from cache."""
        key = _compute_key("test")
        test_data = {"value": 42, "list": [1, 2, 3]}
        
        _save_to_cache(key, test_data)
        
        loaded = _load_from_cache(key)
        self.assertEqual(loaded["value"], 42)
        self.assertEqual(loaded["list"], [1, 2, 3])

    def test_cache_expiration(self):
        """Test cache expiration."""
        key = _compute_key("test")
        _save_to_cache(key, {"data": "test"})
        
        # Manually set old timestamp
        manifest = _load_manifest()
        manifest["entries"][key]["created_at"] = time.time() - 1000
        _save_manifest(manifest)
        
        # Should be invalid
        self.assertFalse(_is_cache_valid(key, ttl=100))

    def test_clear_cache(self):
        """Test cache clearing."""
        key1 = _compute_key("test1")
        key2 = _compute_key("test2")
        
        _save_to_cache(key1, {"data": "1"})
        _save_to_cache(key2, {"data": "2"})
        
        # Clear all
        count = clear_cache()
        self.assertEqual(count, 2)
        
        self.assertFalse(_is_cache_valid(key1))
        self.assertFalse(_is_cache_valid(key2))

    def test_clear_cache_with_prefix(self):
        """Test cache clearing with prefix."""
        key1 = _compute_key("string_test")
        key2 = _compute_key("deg_test")
        
        _save_to_cache(key1, {"data": "1"})
        _save_to_cache(key2, {"data": "2"})
        
        # Clear only string prefix
        count = clear_cache("string")
        self.assertEqual(count, 1)
        
        self.assertFalse(_is_cache_valid(key1))
        self.assertTrue(_is_cache_valid(key2))

    def test_cache_decorator(self):
        """Test cache decorator functionality."""
        call_count = 0
        
        @cache_result("test_func", ttl=3600)
        def mock_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - should execute
        result1 = mock_func(2, 3)
        self.assertEqual(result1, 5)
        self.assertEqual(call_count, 1)
        
        # Second call with same args - should use cache
        result2 = mock_func(2, 3)
        self.assertEqual(result2, 5)
        self.assertEqual(call_count, 1)  # No additional call
        
        # Call with different args - should execute
        result3 = mock_func(3, 4)
        self.assertEqual(result3, 7)
        self.assertEqual(call_count, 2)

    def test_profile_function(self):
        """Test function profiling."""
        def slow_func(x):
            time.sleep(0.1)
            return x * 2
        
        result, stats = profile_function(slow_func, 5)
        
        self.assertEqual(result, 10)
        self.assertIn("execution_time_seconds", stats)
        self.assertGreater(stats["execution_time_seconds"], 0.05)

if __name__ == "__main__":
    unittest.main()
