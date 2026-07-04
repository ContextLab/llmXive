"""
Tests to verify that linting and formatting configurations are valid.
"""
import subprocess
import os
import sys
import tempfile
import shutil

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in code/ directory."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".flake8")
    assert os.path.exists(config_path), "Missing .flake8 configuration file"

def test_pyproject_toml_config_exists():
    """Verify pyproject.toml configuration file exists."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")
    assert os.path.exists(config_path), "Missing pyproject.toml configuration file"

def test_black_config_valid():
    """Verify black configuration is present and parseable."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")
    with open(config_path, 'r') as f:
        content = f.read()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "line-length = 88" in content, "Missing line-length configuration for black"

def test_flake8_config_valid():
    """Verify flake8 configuration is present and parseable."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".flake8")
    with open(config_path, 'r') as f:
        content = f.read()
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length" in content, "Missing max-line-length configuration for flake8"