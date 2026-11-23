"""
Tests to verify that linting and formatting configurations are correctly set up.
These tests ensure that the project adheres to the defined style guidelines.
"""
import os
import subprocess
import tempfile
import json
from pathlib import Path

import pytest


def test_pyproject_exists():
    """Test that pyproject.toml exists and contains black/ruff config."""
    assert Path("pyproject.toml").exists(), "pyproject.toml must exist"

    with open("pyproject.toml", "r") as f:
        content = f.read()

    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
    assert "line-length" in content, "line-length must be configured"


def test_ruff_config_valid():
    """Test that ruff can parse the configuration."""
    result = subprocess.run(
        ["ruff", "check", "--config", "pyproject.toml", "--isolated", "--no-cache", "."],
        capture_output=True,
        text=True,
    )
    # ruff might find issues, but it should not crash parsing config
    assert result.returncode in [0, 1], "ruff should be able to parse the config"


def test_black_config_valid():
    """Test that black can parse the configuration."""
    result = subprocess.run(
        ["black", "--config", "pyproject.toml", "--check", "--diff", "--exclude", "venv", "."],
        capture_output=True,
        text=True,
    )
    # black might find issues, but it should not crash parsing config
    assert result.returncode in [0, 1], "black should be able to parse the config"


def test_setup_script_exists():
    """Test that the setup linting script exists."""
    assert Path("scripts/setup_linting.sh").exists(), "scripts/setup_linting.sh must exist"
    assert Path("scripts/setup_linting.sh").stat().st_size > 0, "setup_linting.sh must not be empty"


def test_black_formatting_on_sample_code():
    """Test that black can format a simple Python file correctly."""
    sample_code = "x=1+2\n"
    expected = "x = 1 + 2\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_code)
        temp_path = f.name

    try:
        # Format with black
        subprocess.run(
            ["black", "--config", "pyproject.toml", temp_path],
            check=True,
            capture_output=True,
        )

        with open(temp_path, "r") as f:
            formatted = f.read()

        assert formatted == expected, f"Black formatting failed: got {repr(formatted)}, expected {repr(expected)}"
    finally:
        os.unlink(temp_path)


def test_ruff_linting_on_sample_code():
    """Test that ruff can detect issues in a simple Python file."""
    # Code with an unused import (E402/F401)
    sample_code = "import os\nimport sys\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_code)
        temp_path = f.name

    try:
        # Run ruff
        result = subprocess.run(
            ["ruff", "check", "--config", "pyproject.toml", temp_path],
            capture_output=True,
            text=True,
        )

        # Ruff should find issues (returncode 1)
        assert result.returncode == 1, "Ruff should detect issues in sample code"
        assert "F401" in result.stdout or "F401" in result.stderr or "unused" in result.stdout.lower(), "Ruff should report unused import"
    finally:
        os.unlink(temp_path)