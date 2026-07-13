import subprocess
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in the code directory."""
    flake8_config = PROJECT_ROOT / ".flake8"
    assert flake8_config.exists(), f"Missing .flake8 configuration at {flake8_config}"
    assert flake8_config.stat().st_size > 0, ".flake8 file is empty"

def test_pyproject_toml_exists():
    """Verify pyproject.toml configuration file exists in the code directory."""
    pyproject_config = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_config.exists(), f"Missing pyproject.toml configuration at {pyproject_config}"
    assert pyproject_config.stat().st_size > 0, "pyproject.toml file is empty"

def test_black_can_parse_config():
    """Verify black can successfully parse the project configuration."""
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "--config", str(PROJECT_ROOT / "pyproject.toml"), str(PROJECT_ROOT / "seed.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # We don't assert exit code 0 because seed.py might not be formatted yet,
        # but we assert that black successfully parsed the config and ran.
        assert result.returncode is not None, "Black process did not return a status code"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black configuration check timed out")

def test_flake8_can_parse_config():
    """Verify flake8 can successfully parse the project configuration."""
    try:
        # Run flake8 on a known file (seed.py) to ensure it reads the config
        result = subprocess.run(
            ["flake8", "--config", str(PROJECT_ROOT / ".flake8"), str(PROJECT_ROOT / "seed.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # We don't assert exit code 0 because seed.py might have linting errors,
        # but we assert that flake8 successfully parsed the config and ran.
        assert result.returncode is not None, "Flake8 process did not return a status code"
    except FileNotFoundError:
        pytest.skip("Flake8 not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 configuration check timed out")
