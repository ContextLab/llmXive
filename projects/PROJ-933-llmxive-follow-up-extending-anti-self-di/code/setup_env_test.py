import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import setup_env

class TestSetupEnv:
    """Tests for environment setup and validation functions."""
    
    def test_load_env_config_file_not_found(self):
        """Test that FileNotFoundError is raised when config file is missing."""
        with pytest.raises(FileNotFoundError):
            setup_env.load_env_config(Path("/nonexistent/path/config.yaml"))
    
    def test_load_env_config_valid_file(self, tmp_path):
        """Test loading a valid configuration file."""
        config_file = tmp_path / "test_config.yaml"
        config_content = """
        datasets:
          ultrafeedback:
            name: "test_dataset"
        """
        config_file.write_text(config_content)
        
        config = setup_env.load_env_config(config_file)
        
        assert "datasets" in config
        assert config["datasets"]["ultrafeedback"]["name"] == "test_dataset"
    
    def test_load_env_config_empty_file(self, tmp_path):
        """Test loading an empty configuration file."""
        config_file = tmp_path / "empty_config.yaml"
        config_file.write_text("")
        
        config = setup_env.load_env_config(config_file)
        
        assert config == {}
    
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_huggingface_env_missing_token(self):
        """Test that ValueError is raised when HF_TOKEN is missing."""
        with pytest.raises(ValueError, match="HF_TOKEN is required"):
            setup_env.setup_huggingface_env()
    
    @patch.dict(os.environ, {"HF_TOKEN": "test_token_123"})
    def test_setup_huggingface_env_from_env_var(self):
        """Test setting up HF environment from environment variable."""
        setup_env.setup_huggingface_env()
        
        assert os.environ["HF_TOKEN"] == "test_token_123"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_huggingface_env_from_argument(self):
        """Test setting up HF environment from argument."""
        setup_env.setup_huggingface_env(token="explicit_token_456")
        
        assert os.environ["HF_TOKEN"] == "explicit_token_456"
    
    @patch.dict(os.environ, {"HF_TOKEN": "test_token"})
    def test_setup_huggingface_env_sets_cache(self):
        """Test that HF_DATASETS_CACHE is set if not already present."""
        # Ensure HF_DATASETS_CACHE is not set
        if "HF_DATASETS_CACHE" in os.environ:
            del os.environ["HF_DATASETS_CACHE"]
        
        setup_env.setup_huggingface_env()
        
        assert "HF_DATASETS_CACHE" in os.environ
        assert "data" in os.environ["HF_DATASETS_CACHE"]
    
    def test_get_dataset_path(self):
        """Test that dataset path is constructed correctly."""
        expected_path = setup_env.PROJECT_ROOT / "data" / "datasets" / "ultrafeedback"
        actual_path = setup_env.get_dataset_path("ultrafeedback")
        
        assert actual_path == expected_path
    
    @patch.dict(os.environ, {"HF_TOKEN": "test_token"})
    def test_validate_env_setup_success(self):
        """Test successful environment validation."""
        results = setup_env.validate_env_setup()
        
        assert results["valid"] is True
        assert len(results["missing_vars"]) == 0
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_env_setup_missing_token(self):
        """Test validation fails when HF_TOKEN is missing."""
        results = setup_env.validate_env_setup()
        
        assert results["valid"] is False
        assert "HF_TOKEN" in results["missing_vars"]
    
    def test_validate_env_setup_config_warnings(self):
        """Test that warnings are generated for missing config sections."""
        config = {}  # Empty config
        results = setup_env.validate_env_setup(config)
        
        assert len(results["config_warnings"]) > 0
        assert any("data" in warning for warning in results["config_warnings"])
    
    @patch("setup_env.load_env_config")
    @patch("setup_env.setup_huggingface_env")
    @patch("setup_env.validate_env_setup")
    def test_main_success(self, mock_validate, mock_setup, mock_load, capsys):
        """Test main function when everything is successful."""
        mock_load.return_value = {"data": {}, "datasets": {}}
        mock_validate.return_value = {"valid": True, "missing_vars": [], "config_warnings": []}
        
        result = setup_env.main()
        
        assert result == 0
        mock_load.assert_called_once()
        mock_setup.assert_called_once()
        mock_validate.assert_called_once()
    
    @patch("setup_env.load_env_config")
    @patch("setup_env.setup_huggingface_env")
    def test_main_hf_setup_failure(self, mock_setup, mock_load, capsys):
        """Test main function when HF setup fails."""
        mock_load.return_value = {}
        mock_setup.side_effect = ValueError("Token required")
        
        result = setup_env.main()
        
        assert result == 1
        mock_setup.assert_called_once()
    
    @patch("setup_env.load_env_config")
    @patch("setup_env.setup_huggingface_env")
    @patch("setup_env.validate_env_setup")
    def test_main_validation_failure(self, mock_validate, mock_setup, mock_load, capsys):
        """Test main function when validation fails."""
        mock_load.return_value = {}
        mock_setup.return_value = None
        mock_validate.return_value = {
            "valid": False,
            "missing_vars": ["HF_TOKEN"],
            "config_warnings": []
        }
        
        result = setup_env.main()
        
        assert result == 1
        mock_validate.assert_called_once()
