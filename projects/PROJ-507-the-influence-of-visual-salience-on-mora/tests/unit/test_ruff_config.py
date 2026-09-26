"""
Unit tests for .ruff.toml configuration verification.
"""
import os
import sys
import tempfile
import tomllib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_ruff_config import verify_ruff_config, create_dummy_file_for_check

class TestRuffConfigVerification:
    """Test cases for ruff configuration verification."""

    def test_verify_ruff_config_file_exists(self, tmp_path, monkeypatch):
        """Test that verification fails when config file doesn't exist."""
        # Create a temporary directory and change to it
        monkeypatch.chdir(tmp_path)
        
        # Ensure file doesn't exist
        config_path = tmp_path / ".ruff.toml"
        assert not config_path.exists()
        
        # Verification should fail
        result = verify_ruff_config()
        assert result is False

    def test_verify_ruff_config_invalid_toml(self, tmp_path, monkeypatch):
        """Test that verification fails with invalid TOML syntax."""
        monkeypatch.chdir(tmp_path)
        
        # Create invalid TOML file
        config_path = tmp_path / ".ruff.toml"
        with open(config_path, "w") as f:
            f.write("invalid toml [syntax")
        
        result = verify_ruff_config()
        assert result is False

    def test_verify_ruff_config_missing_section(self, tmp_path, monkeypatch):
        """Test that verification fails when required section is missing."""
        monkeypatch.chdir(tmp_path)
        
        config_path = tmp_path / ".ruff.toml"
        with open(config_path, "w") as f:
            f.write("""
            [format]
            quote-style = "double"
            """)
        
        result = verify_ruff_config()
        assert result is False

    def test_verify_ruff_config_missing_keys(self, tmp_path, monkeypatch):
        """Test that verification fails when required keys are missing."""
        monkeypatch.chdir(tmp_path)
        
        config_path = tmp_path / ".ruff.toml"
        with open(config_path, "w") as f:
            f.write("""
            [lint]
            select = ["E", "F"]
            """)
        
        result = verify_ruff_config()
        assert result is False

    def test_verify_ruff_config_valid(self, tmp_path, monkeypatch):
        """Test that verification passes with valid configuration."""
        monkeypatch.chdir(tmp_path)
        
        config_path = tmp_path / ".ruff.toml"
        with open(config_path, "w") as f:
            f.write("""
            [lint]
            select = ["E", "F", "W", "I"]
            ignore = ["E501"]
            line-length = 100
            """)
        
        result = verify_ruff_config()
        assert result is True

    def test_verify_ruff_config_correct_values(self, tmp_path, monkeypatch):
        """Test that configuration values match expected values."""
        monkeypatch.chdir(tmp_path)
        
        # Create a valid config with correct values
        config_path = tmp_path / ".ruff.toml"
        with open(config_path, "wb") as f:
            f.write(b"""
            [lint]
            select = ["E", "F", "W", "I"]
            ignore = ["E501"]
            line-length = 100
            """)
        
        # Parse and verify manually
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        
        assert config["lint"]["line-length"] == 100
        assert set(config["lint"]["select"]) == {"E", "F", "W", "I"}
        assert set(config["lint"]["ignore"]) == {"E501"}

    def test_create_dummy_file_for_check(self, tmp_path, monkeypatch):
        """Test that dummy file creation works correctly."""
        monkeypatch.chdir(tmp_path)
        
        dummy_path = create_dummy_file_for_check()
        
        assert dummy_path.exists()
        assert dummy_path.suffix == ".py"
        
        with open(dummy_path, "r") as f:
            content = f.read()
        
        assert "import os" in content
        assert "def test_function" in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])