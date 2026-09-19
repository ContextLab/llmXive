"""
Tests for linting configuration setup.

These tests verify that the linting configuration files are created
correctly and contain the expected settings.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import tomli
from src.utils.linting_config import (
    get_ruff_config, 
    get_black_config, 
    write_pyproject_toml,
    create_ruff_toml
)

class TestLintingConfig:
    """Test suite for linting configuration."""

    def test_get_ruff_config_returns_dict(self):
        """Test that get_ruff_config returns a dictionary."""
        config = get_ruff_config()
        assert isinstance(config, dict)
        assert "lint" in config
        assert "line-length" in config
        assert "target-version" in config

    def test_get_ruff_config_has_correct_line_length(self):
        """Test that Ruff line length is set to 88."""
        config = get_ruff_config()
        assert config["line-length"] == 88

    def test_get_black_config_returns_dict(self):
        """Test that get_black_config returns a dictionary."""
        config = get_black_config()
        assert isinstance(config, dict)
        assert "line-length" in config
        assert "target-version" in config

    def test_get_black_config_has_correct_line_length(self):
        """Test that Black line length is set to 88."""
        config = get_black_config()
        assert config["line-length"] == 88

    def test_ruff_select_rules_exist(self):
        """Test that expected linting rules are selected."""
        config = get_ruff_config()
        select_rules = config["lint"]["select"]
        expected_rules = ["E", "W", "F", "I", "C", "B", "UP", "SIM"]
        for rule in expected_rules:
            assert rule in select_rules, f"Rule {rule} not found in select rules"

    def test_write_pyproject_toml_creates_file(self, tmp_path):
        """Test that write_pyproject_toml creates the file."""
        write_pyproject_toml(tmp_path)
        pyproject_path = tmp_path / "pyproject.toml"
        assert pyproject_path.exists()

    def test_write_pyproject_toml_contains_ruff_section(self, tmp_path):
        """Test that pyproject.toml contains the ruff section."""
        write_pyproject_toml(tmp_path)
        pyproject_path = tmp_path / "pyproject.toml"
        
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        assert "tool" in config
        assert "ruff" in config["tool"]
        assert "lint" in config["tool"]["ruff"]

    def test_write_pyproject_toml_contains_black_section(self, tmp_path):
        """Test that pyproject.toml contains the black section."""
        write_pyproject_toml(tmp_path)
        pyproject_path = tmp_path / "pyproject.toml"
        
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        assert "tool" in config
        assert "black" in config["tool"]

    def test_create_ruff_toml_creates_file(self, tmp_path):
        """Test that create_ruff_toml creates the file."""
        create_ruff_toml(tmp_path)
        ruff_toml_path = tmp_path / ".ruff.toml"
        assert ruff_toml_path.exists()

    def test_create_ruff_toml_contains_line_length(self, tmp_path):
        """Test that .ruff.toml contains the line-length setting."""
        create_ruff_toml(tmp_path)
        ruff_toml_path = tmp_path / ".ruff.toml"
        
        with open(ruff_toml_path, "r") as f:
            content = f.read()
        
        assert "line-length = 88" in content

    def test_pyproject_toml_preserves_existing_content(self, tmp_path):
        """Test that write_pyproject_toml preserves existing content."""
        # Create a pyproject.toml with existing content
        pyproject_path = tmp_path / "pyproject.toml"
        existing_content = """
        [project]
        name = "test-project"
        version = "0.1.0"
        """
        with open(pyproject_path, "w") as f:
            f.write(existing_content)
        
        write_pyproject_toml(tmp_path)
        
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        # Check that existing content is preserved
        assert "project" in config
        assert config["project"]["name"] == "test-project"
        
        # Check that new content is added
        assert "tool" in config
        assert "ruff" in config["tool"]
        assert "black" in config["tool"]
