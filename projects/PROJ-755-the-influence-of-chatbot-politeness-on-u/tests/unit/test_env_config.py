"""
Unit tests for environment configuration utilities.
"""
import os
import tempfile
import pytest
from pathlib import Path
from code.utils.env_config import create_env_template, validate_env_config, EnvConfigError

class TestEnvConfig:
    
    def test_create_env_template(self):
        """Test that create_env_template generates a file with expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir) / "test_env"
            create_env_template(target_path)
            
            assert target_path.exists()
            content = target_path.read_text()
            assert "HF_TOKEN=" in content
            assert "HuggingFace" in content or "Token" in content  # Basic check for comments
    
    def test_validate_env_config_missing_token(self):
        """Test validation fails gracefully if token is missing but file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("HF_TOKEN=\n")
            
            # Should raise EnvConfigError because token is empty
            with pytest.raises(EnvConfigError):
                validate_env_config(env_path)
    
    def test_validate_env_config_valid(self):
        """Test validation passes if token is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("HF_TOKEN=hf_valid_token_12345\n")
            
            # Should not raise
            try:
                validate_env_config(env_path)
            except EnvConfigError:
                pytest.fail("validate_env_config raised unexpectedly for valid token")
    
    def test_validate_env_config_missing_file(self):
        """Test validation handles missing file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "nonexistent.env"
            
            # Should raise EnvConfigError because file is missing
            with pytest.raises(EnvConfigError):
                validate_env_config(env_path)