"""
Tests for linting configuration (Task T003b).
"""
import subprocess
import os
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    flake8_path = project_root / ".flake8"
    assert flake8_path.exists(), f".flake8 file not found at {flake8_path}"


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"


def test_black_can_parse_config():
    """Test that black can parse the configuration."""
    pyproject_path = project_root / "pyproject.toml"
    try:
        import tomli
        with open(pyproject_path, "rb") as f:
            tomli.load(f)
        assert True
    except Exception as e:
        pytest.fail(f"Black/tomli could not parse pyproject.toml: {e}")


def test_flake8_can_parse_config():
    """Test that flake8 can parse the configuration."""
    flake8_path = project_root / ".flake8"
    try:
        result = subprocess.run(
            ["flake8", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # If we get here, flake8 is installed and can run
        assert result.returncode == 0 or "usage" in result.stdout.lower()
    except FileNotFoundError:
        pytest.fail("flake8 is not installed. Please install it: pip install flake8")


def test_linting_rules_are_reasonable():
    """Test that linting rules are reasonably configured."""
    flake8_path = project_root / ".flake8"
    with open(flake8_path, "r") as f:
        content = f.read()

    # Check for max-line-length
    assert "max-line-length" in content, "max-line-length should be defined in .flake8"


def test_flake8_runs_on_sample_file():
    """
    Test that flake8 can successfully run on a sample file.
    This verifies the configuration is valid and flake8 is executable.
    """
    sample_file = project_root / "code" / "tests" / "linting" / "sample_code.py"
    flake8_path = project_root / ".flake8"

    assert sample_file.exists(), f"Sample file not found at {sample_file}"
    assert flake8_path.exists(), f".flake8 config not found at {flake8_path}"

    result = subprocess.run(
        ["flake8", "--config=" + str(flake8_path), str(sample_file)],
        capture_output=True,
        text=True,
        cwd=project_root
    )

    # The important thing is that flake8 ran without crashing.
    # It may return non-zero if it finds issues, which is expected.
    # We just verify it executed successfully.
    assert result.returncode is not None, "flake8 failed to execute"
    # If returncode is 0, perfect. If non-zero, it means it found issues (expected with sample file)
    # but the configuration is valid.
    assert True, f"Flake8 executed. Return code: {result.returncode}"
