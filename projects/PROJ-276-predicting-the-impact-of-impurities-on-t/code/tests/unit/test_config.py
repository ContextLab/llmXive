import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from code.src.utils.config import (
    ConfigError,
    load_env_file,
    get_api_key,
    get_materials_project_api_key,
    get_huggingface_token,
    validate_materials_project_connection,
    get_project_root,
    get_config_summary
)

class TestLoadEnvFile:
    def test_load_env_file_success(self):
        """Test successful loading of .env file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_content = """
            # Comment line
            MP_API_KEY=test_key_123
            HF_TOKEN=hf_token_456
            EMPTY_VALUE=
            QUOTED_VALUE="quoted value"
            """
            env_path.write_text(env_content)
            
            result = load_env_file(str(env_path))
            
            assert result["MP_API_KEY"] == "test_key_123"
            assert result["HF_TOKEN"] == "hf_token_456"
            assert result["EMPTY_VALUE"] == ""
            assert result["QUOTED_VALUE"] == "quoted value"
            
    def test_load_env_file_missing(self):
        """Test handling of missing .env file"""
        result = load_env_file("/nonexistent/path/.env")
        assert result == {}
        
    def test_load_env_file_default_path(self):
        """Test loading from default path"""
        # This should not raise an error even if .env doesn't exist
        result = load_env_file()
        assert isinstance(result, dict)

class TestGetApiKey:
    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        with patch.dict(os.environ, {"TEST_SERVICE_API_KEY": "test_key"}):
            key = get_api_key("test_service")
            assert key == "test_key"
            
    def test_get_api_key_custom_env_key(self):
        """Test API key retrieval with custom env key"""
        with patch.dict(os.environ, {"CUSTOM_KEY": "custom_value"}):
            key = get_api_key("test_service", "CUSTOM_KEY")
            assert key == "custom_value"
            
    def test_get_api_key_missing(self):
        """Test error when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                get_api_key("nonexistent_service")

class TestGetMaterialsProjectApiKey:
    def test_get_materials_project_api_key_success(self):
        """Test successful MP API key retrieval"""
        with patch.dict(os.environ, {"MP_API_KEY": "mp_test_key"}):
            key = get_materials_project_api_key()
            assert key == "mp_test_key"
            
    def test_get_materials_project_api_key_missing(self):
        """Test error when MP API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                get_materials_project_api_key()

class TestGetHuggingfaceToken:
    def test_get_huggingface_token_success(self):
        """Test successful HF token retrieval"""
        with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"}):
            token = get_huggingface_token()
            assert token == "hf_test_token"
            
    def test_get_huggingface_token_missing(self):
        """Test error when HF token is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                get_huggingface_token()

class TestValidateMaterialsProjectConnection:
    @patch('code.src.utils.config.requests.get')
    def test_validate_materials_project_connection_success(self, mock_get):
        """Test successful connection validation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"MP_API_KEY": "valid_key"}):
            result = validate_materials_project_connection()
            assert result is True
            
    @patch('code.src.utils.config.requests.get')
    def test_validate_materials_project_connection_invalid_key(self, mock_get):
        """Test connection validation with invalid key"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"MP_API_KEY": "invalid_key"}):
            result = validate_materials_project_connection()
            assert result is False
            
    @patch('code.src.utils.config.requests.get')
    def test_validate_materials_project_connection_timeout(self, mock_get):
        """Test connection validation with timeout"""
        mock_get.side_effect = Exception("Timeout")
        
        with patch.dict(os.environ, {"MP_API_KEY": "test_key"}):
            result = validate_materials_project_connection()
            assert result is False
            
    def test_validate_materials_project_connection_missing_key(self):
        """Test connection validation with missing key"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_materials_project_connection()
            assert result is False

class TestGetProjectRoot:
    def test_get_project_root_returns_path(self):
        """Test that project root is a valid Path"""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

class TestGetConfigSummary:
    def test_get_config_summary_structure(self):
        """Test config summary structure"""
        with patch.dict(os.environ, {
            "MP_API_KEY": "mp_key_1234567890",
            "HF_TOKEN": "hf_token_0987654321"
        }):
            summary = get_config_summary()
            
            assert "project_root" in summary
            assert "environment_loaded" in summary
            assert "services" in summary
            assert "materials_project" in summary["services"]
            assert "huggingface" in summary["services"]
            
            # Check MP service details
            mp_service = summary["services"]["materials_project"]
            assert mp_service["configured"] is True
            assert mp_service["key_present"] is True
            assert "mp_key" in mp_service["key_masked"]
            
            # Check HF service details
            hf_service = summary["services"]["huggingface"]
            assert hf_service["configured"] is True
            assert hf_service["key_present"] is True
            assert "hf_token" in hf_service["key_masked"]
            
    def test_get_config_summary_no_keys(self):
        """Test config summary with no keys"""
        with patch.dict(os.environ, {}, clear=True):
            summary = get_config_summary()
            
            assert summary["environment_loaded"] is False
            assert summary["services"]["materials_project"]["configured"] is False
            assert summary["services"]["huggingface"]["configured"] is False