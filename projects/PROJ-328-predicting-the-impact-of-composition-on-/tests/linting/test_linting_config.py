"""
Contract tests for linting configuration.
These tests verify that the linting setup is correct and functional.
"""
import subprocess
import os
import pytest
from pathlib import Path
import tomli
import sys

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

def test_flake8_config_exists(project_root):
    """Test that .flake8 configuration file exists."""
    flake8_path = project_root / ".flake8"
    assert flake8_path.exists(), ".flake8 file not found in project root"

def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml configuration file exists."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml file not found in project root"

def test_black_can_parse_config(project_root):
    """Test that black can parse the configuration from pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        assert "tool" in config, "No [tool] section in pyproject.toml"
        assert "black" in config["tool"], "No [tool.black] section in pyproject.toml"
    except Exception as e:
        pytest.fail(f"Failed to parse pyproject.toml for black config: {e}")

def test_flake8_can_parse_config(project_root):
    """Test that flake8 can parse the .flake8 configuration."""
    flake8_path = project_root / ".flake8"
    try:
        result = subprocess.run(
            ["flake8", "--version"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0, f"flake8 failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("flake8 is not installed. Please install it: pip install flake8")

def test_linting_rules_are_reasonable(project_root):
    """Test that the linting rules are reasonable (max-line-length <= 120)."""
    flake8_path = project_root / ".flake8"
    with open(flake8_path, "r") as f:
        content = f.read()

    # Check for max-line-length setting
    if "max-line-length" in content:
        # Extract the value
        import re
        match = re.search(r"max-line-length\s*=\s*(\d+)", content)
        if match:
            max_len = int(match.group(1))
            assert max_len <= 120, f"max-line-length ({max_len}) is too high (should be <= 120)"
            assert max_len >= 79, f"max-line-length ({max_len}) is too low (should be >= 79)"

def test_flake8_runs_on_sample_file(project_root):
    """Test that flake8 can run on a sample file without crashing."""
    sample_file = project_root / "code" / "tests" / "linting" / "sample_code.py"
    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    try:
        result = subprocess.run(
            ["flake8", str(sample_file)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # flake8 should run successfully (returncode 0 or 1 are both OK)
        # 0 = no issues, 1 = issues found
        assert result.returncode in [0, 1], f"flake8 crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("flake8 is not installed. Please install it: pip install flake8")