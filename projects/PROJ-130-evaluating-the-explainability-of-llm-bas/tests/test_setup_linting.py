"""
Tests for the setup_linting.py script.

These tests verify that the configuration files are created correctly
and contain the expected content.
"""
import os
import tempfile
from pathlib import Path
import pytest

# We need to import the setup_linting module
# Since it's in code/, we need to add it to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_linting import create_pyproject_config, create_precommit_config


class TestSetupLinting:
    """Test suite for linting configuration setup."""

    def test_pyproject_config_creation(self, tmp_path):
        """Test that pyproject.toml is created with correct content."""
        create_pyproject_config(tmp_path)
        
        pyproject_path = tmp_path / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should be created"
        
        content = pyproject_path.read_text()
        
        # Check for required sections
        assert "[tool.black]" in content, "Should contain [tool.black] section"
        assert "[tool.ruff]" in content, "Should contain [tool.ruff] section"
        assert "line-length = 88" in content, "Should set line length to 88"
        assert "target-version = 'py311'" in content or 'target-version = "py311"' in content, "Should target Python 3.11"
        
        # Check for black-specific settings
        assert "include" in content, "Should have include pattern for black"
        
        # Check for ruff-specific settings
        assert 'select =' in content, "Should have select list for ruff"
        assert '"E"' in content or "'E'" in content, "Should include pycodestyle errors"
        assert '"F"' in content or "'F'" in content, "Should include Pyflakes"

    def test_precommit_config_creation(self, tmp_path):
        """Test that .pre-commit-config.yaml is created with correct content."""
        create_precommit_config(tmp_path)
        
        precommit_path = tmp_path / ".pre-commit-config.yaml"
        assert precommit_path.exists(), ".pre-commit-config.yaml should be created"
        
        content = precommit_path.read_text()
        
        # Check for required repos
        assert "psf/black" in content, "Should include black repo"
        assert "astral-sh/ruff-pre-commit" in content, "Should include ruff repo"
        
        # Check for hooks
        assert "- id: black" in content, "Should have black hook"
        assert "- id: ruff" in content, "Should have ruff hook"
        assert "- id: ruff-format" in content, "Should have ruff-format hook"

    def test_full_setup_integration(self, tmp_path):
        """Test that both configuration files are created successfully."""
        create_pyproject_config(tmp_path)
        create_precommit_config(tmp_path)
        
        pyproject_path = tmp_path / "pyproject.toml"
        precommit_path = tmp_path / ".pre-commit-config.yaml"
        
        assert pyproject_path.exists(), "pyproject.toml should exist"
        assert precommit_path.exists(), ".pre-commit-config.yaml should exist"
        
        # Verify both files are non-empty
        assert pyproject_path.stat().st_size > 0, "pyproject.toml should not be empty"
        assert precommit_path.stat().st_size > 0, ".pre-commit-config.yaml should not be empty"

    def test_config_syntax_validity(self, tmp_path):
        """Test that the generated configs have valid syntax."""
        create_pyproject_config(tmp_path)
        create_precommit_config(tmp_path)
        
        import tomllib
        import yaml
        
        # Test pyproject.toml is valid TOML
        pyproject_path = tmp_path / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            try:
                tomllib.load(f)
            except Exception as e:
                pytest.fail(f"pyproject.toml is not valid TOML: {e}")
        
        # Test .pre-commit-config.yaml is valid YAML
        precommit_path = tmp_path / ".pre-commit-config.yaml"
        with open(precommit_path, "r") as f:
            try:
                yaml.safe_load(f)
            except Exception as e:
                pytest.fail(f".pre-commit-config.yaml is not valid YAML: {e}")