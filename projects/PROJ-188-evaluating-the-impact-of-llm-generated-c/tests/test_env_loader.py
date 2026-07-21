import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.env_loader import load_env_vars, get_model_path, validate_token

class TestEnvLoader:
    def test_load_env_vars_missing_file(self, caplog):
        """Test that load_env_vars returns False when .env is missing."""
        result = load_env_vars(Path("/nonexistent/path/.env"))
        assert result is False
        assert "not found" in caplog.text.lower()

    def test_load_env_vars_success(self):
        """Test loading a valid .env file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text("TEST_VAR=test_value\nANOTHER_VAR=123")
            
            # Mock load_dotenv to avoid side effects in test env
            with patch('code.utils.env_loader.load_dotenv') as mock_load:
                mock_load.return_value = True
                result = load_env_vars(env_path)
                assert result is True
                mock_load.assert_called_once()

    def test_get_model_path_set(self):
        """Test retrieving a set model path."""
        with patch.dict(os.environ, {"HF_MODEL_PATH": "/path/to/model"}):
            path = get_model_path()
            assert path == "/path/to/model"

    def test_get_model_path_unset(self):
        """Test retrieving an unset model path."""
        with patch.dict(os.environ, {}, clear=True):
            path = get_model_path()
            assert path is None

    def test_validate_token_valid(self):
        """Test validation of a valid token."""
        with patch.dict(os.environ, {"HF_TOKEN": "hf_1234567890abcdef"}):
            assert validate_token() is True

    def test_validate_token_empty(self):
        """Test validation of an empty token."""
        with patch.dict(os.environ, {"HF_TOKEN": ""}):
            assert validate_token() is False

    def test_validate_token_missing(self):
        """Test validation when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            assert validate_token() is False
