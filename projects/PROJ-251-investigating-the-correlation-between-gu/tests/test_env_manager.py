"""
Tests for environment configuration management.
"""
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.env_manager import (
    load_dotenv_file,
    validate_api_keys,
    get_env_var,
    setup_environment,
    get_huggingface_token,
    get_ncbi_api_key,
    get_random_seed,
    get_max_workers,
    get_timeout_seconds,
    get_cache_dir,
    DEFAULT_ENV_PATH
)

class TestEnvManager(unittest.TestCase):
    """Test environment configuration management functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test .env files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Save original environment variables
        self.original_env = {
            "HUGGINGFACE_TOKEN": os.environ.get("HUGGINGFACE_TOKEN"),
            "NCBI_API_KEY": os.environ.get("NCBI_API_KEY"),
            "RANDOM_SEED": os.environ.get("RANDOM_SEED"),
            "MAX_WORKERS": os.environ.get("MAX_WORKERS"),
            "REQUEST_TIMEOUT": os.environ.get("REQUEST_TIMEOUT"),
            "CACHE_DIR": os.environ.get("CACHE_DIR"),
        }
        
        # Clear environment variables for testing
        for key in ["HUGGINGFACE_TOKEN", "NCBI_API_KEY", "RANDOM_SEED", 
                   "MAX_WORKERS", "REQUEST_TIMEOUT", "CACHE_DIR"]:
            if key in os.environ:
                del os.environ[key]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.chdir(self.original_cwd)
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_load_dotenv_file_creates_env(self):
        """Test that load_dotenv_file correctly loads a .env file."""
        # Create a test .env file
        env_content = """
        HUGGINGFACE_TOKEN=test_token_123
        NCBI_API_KEY=test_key_456
        RANDOM_SEED=999
        """
        
        env_path = Path(self.test_dir) / ".env"
        env_path.write_text(env_content)
        
        # Load the environment
        result = load_dotenv_file(env_path)
        
        self.assertTrue(result)
        self.assertEqual(os.getenv("HUGGINGFACE_TOKEN"), "test_token_123")
        self.assertEqual(os.getenv("NCBI_API_KEY"), "test_key_456")
        self.assertEqual(os.getenv("RANDOM_SEED"), "999")
    
    def test_load_dotenv_file_missing_file(self):
        """Test that load_dotenv_file returns False for missing file."""
        result = load_dotenv_file(Path("/nonexistent/.env"))
        self.assertFalse(result)
    
    def test_validate_api_keys_all_present(self):
        """Test validation when all required keys are present."""
        os.environ["HUGGINGFACE_TOKEN"] = "test_token"
        os.environ["NCBI_API_KEY"] = "test_key"
        
        result = validate_api_keys()
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["missing"], [])
        self.assertIn("HUGGINGFACE_TOKEN", result["present"])
        self.assertIn("NCBI_API_KEY", result["present"])
    
    def test_validate_api_keys_missing_some(self):
        """Test validation when some required keys are missing."""
        os.environ["HUGGINGFACE_TOKEN"] = "test_token"
        # NCBI_API_KEY is missing
        
        result = validate_api_keys()
        
        self.assertFalse(result["valid"])
        self.assertIn("NCBI_API_KEY", result["missing"])
        self.assertNotIn("NCBI_API_KEY", result["present"])
    
    def test_validate_api_keys_all_missing(self):
        """Test validation when all required keys are missing."""
        result = validate_api_keys()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["missing"]), 2)
        self.assertIn("HUGGINGFACE_TOKEN", result["missing"])
        self.assertIn("NCBI_API_KEY", result["missing"])
    
    def test_get_env_var_with_default(self):
        """Test get_env_var with default value."""
        result = get_env_var("NONEXISTENT_VAR", default="default_value")
        self.assertEqual(result, "default_value")
    
    def test_get_env_var_required_missing(self):
        """Test get_env_var with required=True raises error when missing."""
        with self.assertRaises(ValueError):
            get_env_var("NONEXISTENT_VAR", required=True)
    
    def test_get_env_var_required_present(self):
        """Test get_env_var with required=True when present."""
        os.environ["TEST_VAR"] = "test_value"
        result = get_env_var("TEST_VAR", required=True)
        self.assertEqual(result, "test_value")
    
    def test_setup_environment(self):
        """Test complete environment setup."""
        # Create a test .env file
        env_content = """
        HUGGINGFACE_TOKEN=test_token
        NCBI_API_KEY=test_key
        """
        
        env_path = Path(self.test_dir) / ".env"
        env_path.write_text(env_content)
        
        result = setup_environment(env_path, validate_required=True)
        
        self.assertTrue(result["env_loaded"])
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual(result["errors"], [])
    
    def test_get_huggingface_token(self):
        """Test HuggingFace token retrieval."""
        os.environ["HUGGINGFACE_TOKEN"] = "hf_test_token"
        result = get_huggingface_token()
        self.assertEqual(result, "hf_test_token")
    
    def test_get_ncbi_api_key(self):
        """Test NCBI API key retrieval."""
        os.environ["NCBI_API_KEY"] = "ncbi_test_key"
        result = get_ncbi_api_key()
        self.assertEqual(result, "ncbi_test_key")
    
    def test_get_random_seed_default(self):
        """Test random seed with default value."""
        result = get_random_seed()
        self.assertEqual(result, 42)
    
    def test_get_random_seed_custom(self):
        """Test random seed with custom value."""
        os.environ["RANDOM_SEED"] = "12345"
        result = get_random_seed()
        self.assertEqual(result, 12345)
    
    def test_get_random_seed_invalid(self):
        """Test random seed with invalid value (should fallback to default)."""
        os.environ["RANDOM_SEED"] = "invalid"
        result = get_random_seed()
        self.assertEqual(result, 42)
    
    def test_get_max_workers_default(self):
        """Test max workers with default value."""
        result = get_max_workers()
        self.assertEqual(result, 4)
    
    def test_get_max_workers_custom(self):
        """Test max workers with custom value."""
        os.environ["MAX_WORKERS"] = "8"
        result = get_max_workers()
        self.assertEqual(result, 8)
    
    def test_get_timeout_seconds_default(self):
        """Test timeout with default value."""
        result = get_timeout_seconds()
        self.assertEqual(result, 60)
    
    def test_get_timeout_seconds_custom(self):
        """Test timeout with custom value."""
        os.environ["REQUEST_TIMEOUT"] = "120"
        result = get_timeout_seconds()
        self.assertEqual(result, 120)
    
    def test_get_cache_dir_default(self):
        """Test cache directory with default value."""
        result = get_cache_dir()
        self.assertEqual(result, Path("data/cache"))
    
    def test_get_cache_dir_custom(self):
        """Test cache directory with custom value."""
        os.environ["CACHE_DIR"] = "/tmp/my_cache"
        result = get_cache_dir()
        self.assertEqual(result, Path("/tmp/my_cache"))

if __name__ == "__main__":
    unittest.main()
