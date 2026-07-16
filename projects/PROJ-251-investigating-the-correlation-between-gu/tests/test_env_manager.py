import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys

# Ensure code/utils is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.env_manager import load_dotenv_file, validate_api_keys, setup_environment

class TestEnvManager(unittest.TestCase):
    
    def setUp(self):
        # Clean up environment variables before each test
        self.original_env = os.environ.copy()
        for key in ['HF_TOKEN', 'NCBI_API_KEY', 'RANDOM_SEED', 'MIN_SAMPLE_SIZE', 'PSEUDOCOUNT']:
            os.environ.pop(key, None)
    
    def tearDown(self):
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_load_dotenv_file_missing_file(self):
        """Test behavior when .env file does not exist."""
        # Should return False and log warning
        result = load_dotenv_file(Path("/nonexistent/.env"))
        self.assertFalse(result)
    
    def test_load_dotenv_file_success(self):
        """Test loading a valid .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            f.write("HF_TOKEN=hf_12345\n")
            temp_path = Path(f.name)
        
        try:
            result = load_dotenv_file(temp_path)
            self.assertTrue(result)
            self.assertEqual(os.getenv("TEST_KEY"), "test_value")
            self.assertEqual(os.getenv("HF_TOKEN"), "hf_12345")
        finally:
            temp_path.unlink()
    
    def test_validate_api_keys_missing(self):
        """Test validation fails when keys are missing."""
        # No keys set in environment
        result = validate_api_keys(['HF_TOKEN', 'NCBI_API_KEY'])
        self.assertFalse(result)
    
    def test_validate_api_keys_present(self):
        """Test validation succeeds when keys are present."""
        os.environ['HF_TOKEN'] = 'hf_real_token'
        os.environ['NCBI_API_KEY'] = 'ncbi_real_key'
        
        result = validate_api_keys(['HF_TOKEN', 'NCBI_API_KEY'])
        self.assertTrue(result)
    
    def test_validate_api_keys_empty(self):
        """Test validation fails when keys are empty strings."""
        os.environ['HF_TOKEN'] = ''
        os.environ['NCBI_API_KEY'] = 'ncbi_real_key'
        
        result = validate_api_keys(['HF_TOKEN', 'NCBI_API_KEY'])
        self.assertFalse(result)
    
    @patch('code.utils.env_manager.load_dotenv_file')
    @patch('code.utils.env_manager.validate_api_keys')
    def test_setup_environment_success(self, mock_validate, mock_load):
        """Test successful setup environment flow."""
        mock_load.return_value = True
        mock_validate.return_value = True
        
        result = setup_environment()
        self.assertTrue(result)
        mock_load.assert_called_once()
        mock_validate.assert_called_once()
    
    @patch('code.utils.env_manager.load_dotenv_file')
    @patch('code.utils.env_manager.validate_api_keys')
    def test_setup_environment_failure(self, mock_validate, mock_load):
        """Test failed setup environment flow."""
        mock_load.return_value = True
        mock_validate.return_value = False
        
        result = setup_environment()
        self.assertFalse(result)
        mock_validate.assert_called_once()
