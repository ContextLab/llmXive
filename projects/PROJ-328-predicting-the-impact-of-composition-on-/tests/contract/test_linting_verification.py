"""
Contract test for linting verification (T003b).
Ensures that the linting configuration is valid and flake8 runs correctly.
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    config_path = ROOT_DIR / ".flake8"
    assert config_path.exists(), f"Missing .flake8 config at {config_path}"

def test_pyproject_toml_exists():
    """Test that pyproject.toml configuration file exists."""
    config_path = ROOT_DIR / "pyproject.toml"
    assert config_path.exists(), f"Missing pyproject.toml config at {config_path}"

def test_flake8_runs_on_sample():
    """Test that flake8 can run on the sample file without crashing."""
    sample_file = ROOT_DIR / "code" / "tests" / "linting" / "sample_code.py"
    assert sample_file.exists(), f"Sample file missing: {sample_file}"

    try:
        result = subprocess.run(
            ["flake8", str(sample_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # flake8 returning non-zero is expected if there are linting issues
        # The important thing is that it runs without crashing
        assert result.returncode in [0, 1], f"flake8 crashed with return code {result.returncode}"
    except FileNotFoundError:
        pytest.skip("flake8 not installed")
    except subprocess.TimeoutExpired:
        pytest.fail("flake8 timed out")

def test_black_config_parsable():
    """Test that Black can parse the pyproject.toml configuration."""
    import tomli
    config_path = ROOT_DIR / "pyproject.toml"

    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)

        # If black section exists, it should be valid
        if "tool" in config and "black" in config["tool"]:
            black_config = config["tool"]["black"]
            assert isinstance(black_config, dict), "Black config should be a dictionary"
    except Exception as e:
        pytest.fail(f"Failed to parse pyproject.toml for Black config: {e}")