"""
Integration tests for environment setup functionality.

These tests verify that the environment setup works correctly in various scenarios,
including edge cases and error conditions.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

import setup_env

class TestEnvironmentSetupIntegration:
    """Integration tests for the setup_env module."""
    
    def test_full_workflow_with_mocked_config(self):
        """Test the complete workflow with a mock configuration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create a mock config file
            config_dir = tmp_path / "config"
            config_dir.mkdir()
            config_file = config_dir / "settings.yaml"
            config_file.write_text("""
            datasets:
              ultrafeedback:
                name: "mock_dataset"
            """)
            
            # Patch the PROJECT_ROOT
            with patch.object(setup_env, 'PROJECT_ROOT', tmp_path):
                # Mock the token to avoid actual validation
                with patch.dict(os.environ, {"HF_TOKEN": "mock_token"}):
                    # Run validation
                    results = setup_env.validate_env_setup()
                    
                    assert results["valid"] is True
                    assert len(results["missing_vars"]) == 0
    
    def test_dataset_path_construction(self):
        """Test that dataset paths are constructed correctly."""
        # Test with various dataset names
        test_cases = [
            ("ultrafeedback", "data/datasets/ultrafeedback"),
            ("dolly", "data/datasets/dolly"),
            ("custom_dataset", "data/datasets/custom_dataset"),
        ]
        
        for dataset_name, expected_suffix in test_cases:
            path = setup_env.get_dataset_path(dataset_name)
            assert path.name == dataset_name
            assert "data" in str(path)
            assert "datasets" in str(path)
    
    def test_env_variable_precedence(self):
        """Test that explicit arguments take precedence over environment variables."""
        # Set environment variable
        with patch.dict(os.environ, {"HF_TOKEN": "env_token"}):
            # Call with explicit argument
            setup_env.setup_huggingface_env(token="explicit_token")
            
            # Verify explicit token was used
            assert os.environ["HF_TOKEN"] == "explicit_token"
    
    def test_whitespace_handling_in_token(self):
        """Test that whitespace is properly handled in tokens."""
        with patch.dict(os.environ, {}, clear=True):
            # Token with leading/trailing whitespace
            setup_env.setup_huggingface_env(token="  token_with_whitespace  ")
            
            # Should be stripped
            assert os.environ["HF_TOKEN"] == "token_with_whitespace"
    
    def test_cache_directory_creation(self):
        """Test that cache directories are referenced correctly."""
        with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
            # This should set HF_DATASETS_CACHE
            setup_env.setup_huggingface_env()
            
            cache_path = os.environ.get("HF_DATASETS_CACHE")
            assert cache_path is not None
            assert "data" in cache_path
            assert "hf_cache" in cache_path
    
    def test_validation_with_partial_config(self):
        """Test validation with a partial configuration."""
        # Config with only data section
        config = {"data": {}}
        
        results = setup_env.validate_env_setup(config)
        
        # Should have warnings about missing datasets section
        assert len(results["config_warnings"]) > 0
        assert any("datasets" in warning for warning in results["config_warnings"])
    
    def test_validation_with_complete_config(self):
        """Test validation with a complete configuration."""
        # Config with all sections
        config = {
            "data": {},
            "datasets": {},
            "training": {}
        }
        
        with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
            results = setup_env.validate_env_setup(config)
            
            # Should have no warnings
            assert len(results["config_warnings"]) == 0
            assert results["valid"] is True
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and actionable."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                setup_env.setup_huggingface_env()
            
            error_message = str(exc_info.value)
            assert "HF_TOKEN" in error_message
            assert "huggingface.co" in error_message
    
    def test_main_with_missing_config_file(self, capsys):
        """Test main function behavior when config file is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Patch PROJECT_ROOT to a directory without config
            with patch.object(setup_env, 'PROJECT_ROOT', tmp_path):
                with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
                    # Should continue with defaults and print warning
                    result = setup_env.main()
                    
                    # Should still succeed if token is set
                    assert result == 0
                    
                    # Check that warning was printed
                    captured = capsys.readouterr()
                    assert "Configuration file not found" in captured.out or "Continuing with default" in captured.out
    
    def test_multiple_env_setup_calls(self):
        """Test that calling setup multiple times doesn't cause issues."""
        with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
            # Call multiple times
            setup_env.setup_huggingface_env()
            setup_env.setup_huggingface_env()
            setup_env.setup_huggingface_env()
            
            # Token should still be set correctly
            assert os.environ["HF_TOKEN"] == "test_token"
    
    def test_empty_token_handling(self):
        """Test that empty tokens are rejected."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                setup_env.setup_huggingface_env(token="   ")
    
    def test_none_token_from_env(self):
        """Test that None token from environment is handled correctly."""
        # Ensure HF_TOKEN is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                setup_env.setup_huggingface_env(token=None)
    
    def test_config_file_with_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML in config file."""
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(Exception):  # yaml.YAMLError or similar
            setup_env.load_env_config(config_file)
    
    def test_default_cache_location(self):
        """Test that the default cache location is correctly constructed."""
        expected_default = str(setup_env.PROJECT_ROOT / "data" / "hf_cache")
        
        # Temporarily remove HF_DATASETS_CACHE if it exists
        original = os.environ.get("HF_DATASETS_CACHE")
        if "HF_DATASETS_CACHE" in os.environ:
            del os.environ["HF_DATASETS_CACHE"]
        
        try:
            with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
                setup_env.setup_huggingface_env()
                assert os.environ["HF_DATASETS_CACHE"] == expected_default
        finally:
            # Restore original value
            if original is not None:
                os.environ["HF_DATASETS_CACHE"] = original
            elif "HF_DATASETS_CACHE" in os.environ:
                del os.environ["HF_DATASETS_CACHE"]