import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# We need to mock the logger import if it causes issues, 
# but typically we just import the module under test.
# Since env_config imports from utils.logging, we assume that works.
from utils.env_config import load_environment, get_hf_token, get_env_var, PROJECT_ROOT

class TestEnvConfig:
    
    @patch("utils.env_config.load_dotenv")
    @patch("utils.env_config.ENV_FILE_PATH")
    @patch("utils.env_config.Path.exists", return_value=True)
    def test_load_environment_with_file(self, mock_exists, mock_path, mock_load_dotenv, caplog):
        """Test that load_environment calls load_dotenv when .env exists."""
        mock_load_dotenv.return_value = True
        with patch.dict(os.environ, {}, clear=False):
            load_environment()
        mock_load_dotenv.assert_called_once()
        
    @patch("utils.env_config.ENV_FILE_PATH")
    @patch("utils.env_config.Path.exists", return_value=False)
    def test_load_environment_without_file(self, mock_exists, mock_path, caplog):
        """Test that load_environment handles missing .env gracefully."""
        load_environment()
        # Should not raise, just log info
        
    def test_get_hf_token_success(self):
        """Test retrieving HF_TOKEN when set."""
        with patch.dict(os.environ, {"HF_TOKEN": "test_token_123"}):
            token = get_hf_token()
            assert token == "test_token_123"
            
    def test_get_hf_token_fallback(self):
        """Test retrieving HF_TOKEN from alternative name."""
        with patch.dict(os.environ, {"HF_TOKEN": "", "HUGGING_FACE_HUB_TOKEN": "alt_token_456"}):
            # Note: get_hf_token checks HF_TOKEN first. If empty string, it might fail depending on logic.
            # Current logic: if not token: check alt. Empty string is falsy.
            token = get_hf_token()
            assert token == "alt_token_456"

    def test_get_hf_token_missing(self):
        """Test that get_hf_token raises RuntimeError when missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="HF_TOKEN not found"):
                get_hf_token()

    def test_get_env_var_default(self):
        """Test get_env_var with default value."""
        with patch.dict(os.environ, {}, clear=True):
            val = get_env_var("NON_EXISTENT", default="default_val")
            assert val == "default_val"

    def test_get_env_var_required_missing(self):
        """Test get_env_var raises when required and missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="Required environment variable"):
                get_env_var("NON_EXISTENT", required=True)

    def test_get_env_var_success(self):
        """Test get_env_var retrieves value."""
        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            val = get_env_var("MY_VAR")
            assert val == "my_value"
