"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import sys
import tomli
from pathlib import Path

import pytest

# Determine the code directory relative to this test file
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Test that .flake8 exists in the code directory."""
    flake8_path = CODE_DIR / ".flake8"
    assert flake8_path.exists(), f".flake8 configuration missing at {flake8_path}"

def test_flake8_config_valid():
    """Test that .flake8 contains expected settings."""
    flake8_path = CODE_DIR / ".flake8"
    content = flake8_path.read_text()
    assert "max-line-length" in content, "max-line-length missing in .flake8"
    assert "100" in content, "max-line-length should be 100"

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the code directory."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml missing at {pyproject_path}"

def test_pyproject_toml_black_config():
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length = 100" in content, "Black line-length should be 100"
    assert "py311" in content, "Black target-version should include py311"

def test_editorconfig_exists():
    """Test that .editorconfig exists in the code directory."""
    editorconfig_path = CODE_DIR / ".editorconfig"
    assert editorconfig_path.exists(), f".editorconfig missing at {editorconfig_path}"

def test_editorconfig_content():
    """Test that .editorconfig contains expected settings."""
    editorconfig_path = CODE_DIR / ".editorconfig"
    content = editorconfig_path.read_text()
    assert "root = true" in content, "EditorConfig root missing"
    assert "indent_style = space" in content, "indent_style should be space"
    assert "indent_size = 4" in content, "indent_size should be 4"

def test_precommit_config_exists():
    """Test that .pre-commit-config.yaml exists in the code directory."""
    precommit_path = CODE_DIR / ".pre-commit-config.yaml"
    assert precommit_path.exists(), f".pre-commit-config.yaml missing at {precommit_path}"

def test_precommit_config_hooks():
    """Test that .pre-commit-config.yaml includes black and flake8 hooks."""
    precommit_path = CODE_DIR / ".pre-commit-config.yaml"
    content = precommit_path.read_text()
    assert "black" in content, "Black hook missing in .pre-commit-config.yaml"
    assert "flake8" in content, "Flake8 hook missing in .pre-commit-config.yaml"
    assert "isort" in content, "Isort hook missing in .pre-commit-config.yaml"
