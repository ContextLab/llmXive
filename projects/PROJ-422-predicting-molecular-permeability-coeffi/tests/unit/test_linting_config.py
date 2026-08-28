"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

class TestLintingConfig:
    """Tests for linting and formatting configuration."""

    def test_black_config_exists(self):
        """Verify .black.toml exists in the code directory."""
        config_path = CODE_DIR / ".black.toml"
        assert config_path.exists(), f"Black config missing at {config_path}"

    def test_black_config_valid(self):
        """Verify .black.toml is valid TOML and contains required keys."""
        config_path = CODE_DIR / ".black.toml"
        with open(config_path, "r") as f:
            config = toml.load(f)
        
        assert "tool" in config
        assert "black" in config["tool"]
        assert "line-length" in config["tool"]["black"]
        assert config["tool"]["black"]["line-length"] == 88
        assert config["tool"]["black"]["target-version"] == ['py311']

    def test_ruff_config_exists(self):
        """Verify .ruff.toml exists in the code directory."""
        config_path = CODE_DIR / ".ruff.toml"
        assert config_path.exists(), f"Ruff config missing at {config_path}"

    def test_ruff_config_valid(self):
        """Verify .ruff.toml is valid TOML and contains required keys."""
        config_path = CODE_DIR / ".ruff.toml"
        with open(config_path, "r") as f:
            config = toml.load(f)
        
        assert "lint" in config
        assert "select" in config["lint"]
        assert "E" in config["lint"]["select"]
        assert "F" in config["lint"]["select"]
        
        assert "format" in config
        assert "quote-style" in config["format"]
        assert config["format"]["quote-style"] == "double"

    def test_ruff_ignores_line_length(self):
        """Verify Ruff ignores E501 (line too long) as Black handles it."""
        config_path = CODE_DIR / ".ruff.toml"
        with open(config_path, "r") as f:
            config = toml.load(f)
        
        assert "E501" in config["lint"]["ignore"]
