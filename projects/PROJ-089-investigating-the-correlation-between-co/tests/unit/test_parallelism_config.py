"""
Unit tests for the parallelism configuration module.
"""
import os
import unittest
from unittest.mock import patch
from code.parallelism_config import (
    get_max_concurrent_repos,
    get_max_concurrent_files,
    DEFAULT_MAX_CONCURRENT_REPOS,
    DEFAULT_MAX_CONCURRENT_FILES,
    ENV_VAR_MAX_CONCURRENT_REPOS,
    ENV_VAR_MAX_CONCURRENT_FILES
)

class TestParallelismConfig(unittest.TestCase):
    
    def tearDown(self):
        """Clean up environment variables after each test."""
        if ENV_VAR_MAX_CONCURRENT_REPOS in os.environ:
            del os.environ[ENV_VAR_MAX_CONCURRENT_REPOS]
        if ENV_VAR_MAX_CONCURRENT_FILES in os.environ:
            del os.environ[ENV_VAR_MAX_CONCURRENT_FILES]

    def test_default_values(self):
        """Test that default values are returned when env vars are not set."""
        self.assertEqual(get_max_concurrent_repos(), DEFAULT_MAX_CONCURRENT_REPOS)
        self.assertEqual(get_max_concurrent_files(), DEFAULT_MAX_CONCURRENT_FILES)

    def test_env_override_repos(self):
        """Test that environment variable overrides the default for repos."""
        os.environ[ENV_VAR_MAX_CONCURRENT_REPOS] = "10"
        self.assertEqual(get_max_concurrent_repos(), 10)

    def test_env_override_files(self):
        """Test that environment variable overrides the default for files."""
        os.environ[ENV_VAR_MAX_CONCURRENT_FILES] = "20"
        self.assertEqual(get_max_concurrent_files(), 20)

    def test_invalid_env_value_fallback(self):
        """Test that invalid env values fall back to default."""
        os.environ[ENV_VAR_MAX_CONCURRENT_REPOS] = "invalid"
        self.assertEqual(get_max_concurrent_repos(), DEFAULT_MAX_CONCURRENT_REPOS)
        
        os.environ[ENV_VAR_MAX_CONCURRENT_FILES] = "not_a_number"
        self.assertEqual(get_max_concurrent_files(), DEFAULT_MAX_CONCURRENT_FILES)

    def test_zero_value_converted_to_one(self):
        """Test that zero or negative values are converted to 1."""
        os.environ[ENV_VAR_MAX_CONCURRENT_REPOS] = "0"
        self.assertEqual(get_max_concurrent_repos(), 1)
        
        os.environ[ENV_VAR_MAX_CONCURRENT_FILES] = "-5"
        self.assertEqual(get_max_concurrent_files(), 1)

if __name__ == "__main__":
    unittest.main()