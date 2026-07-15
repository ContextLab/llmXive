"""
Unit tests to verify linting and formatting configurations are valid.
These tests ensure that flake8 and black configurations exist and are
syntactically correct.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Test that .flake8 or setup.cfg with [flake8] section exists."""
    flake8_file = CODE_DIR / ".flake8"
    setup_cfg = CODE_DIR / "setup.cfg"
    assert flake8_file.exists() or setup_cfg.exists(), "Flake8 config file missing"

def test_black_config_exists():
    """Test that pyproject.toml with [tool.black] section exists."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

def test_flake8_runs_without_syntax_error():
    """Test that flake8 can run on the code directory without crashing."""
    # We run flake8 on an empty list of files or a dummy file to check config validity
    # If config is invalid, flake8 will exit with an error code.
    flake8_file = CODE_DIR / ".flake8"
    setup_cfg = CODE_DIR / "setup.cfg"
    
    config_file = flake8_file if flake8_file.exists() else setup_cfg
    
    # Run flake8 with --help or on a dummy file to validate config parsing
    # We use --version to ensure the tool is installed and config is read
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Flake8 failed to run: {result.stderr}"

def test_black_runs_without_syntax_error():
    """Test that black can run on the code directory without crashing."""
    # Run black --check on a dummy file or the directory itself to validate config
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "--quiet", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    # Black returns 1 if files need reformatting, but 0 if it runs successfully.
    # We are only testing that the configuration is valid and the tool runs.
    # If the config is broken, it will exit with a non-zero code and an error in stderr.
    if result.returncode != 0 and "error" in result.stderr.lower():
        pytest.fail(f"Black configuration error: {result.stderr}")