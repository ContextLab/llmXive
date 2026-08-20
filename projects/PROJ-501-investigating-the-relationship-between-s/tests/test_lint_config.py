"""
Tests for lint configuration files existence and basic structure.
These tests ensure that the necessary configuration files for T008 are present.
"""
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path to allow imports if needed, though this test is file-based
current_dir = Path(__file__).parent
code_dir = current_dir.parent / "code"

@pytest.fixture
def config_files():
    return {
        "flake8": code_dir / ".flake8",
        "pylint": code_dir / ".pylintrc",
        "black": code_dir / "pyproject.toml",
        "runner": code_dir / "lint_runner.py"
    }

def test_flake8_config_exists(config_files):
    """Test that .flake8 configuration file exists."""
    assert config_files["flake8"].exists(), ".flake8 file is missing in code/"
    content = config_files["flake8"].read_text()
    assert "[flake8]" in content, ".flake8 file must contain [flake8] section"
    assert "max-line-length" in content, ".flake8 must define max-line-length"

def test_pylint_config_exists(config_files):
    """Test that .pylintrc configuration file exists."""
    assert config_files["pylint"].exists(), ".pylintrc file is missing in code/"
    content = config_files["pylint"].read_text()
    assert "[MESSAGES CONTROL]" in content, ".pylintrc must contain [MESSAGES CONTROL] section"
    assert "[FORMAT]" in content, ".pylintrc must contain [FORMAT] section"

def test_black_config_exists(config_files):
    """Test that pyproject.toml contains black configuration."""
    assert config_files["black"].exists(), "pyproject.toml is missing in code/"
    content = config_files["black"].read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length" in content, "pyproject.toml black config must define line-length"

def test_lint_runner_exists(config_files):
    """Test that lint_runner.py exists and is a valid python file."""
    assert config_files["runner"].exists(), "lint_runner.py is missing in code/"
    content = config_files["runner"].read_text()
    assert "import subprocess" in content, "lint_runner.py must import subprocess"
    assert "def main()" in content, "lint_runner.py must define a main function"
    assert "black" in content.lower(), "lint_runner.py must reference black"
    assert "flake8" in content.lower(), "lint_runner.py must reference flake8"
    assert "pylint" in content.lower(), "lint_runner.py must reference pylint"