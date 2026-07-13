"""
Unit tests to verify that linting and formatting tools are correctly configured.
These tests ensure that 'ruff' and 'black' are installed and can be invoked.
"""
import subprocess
import sys
import os

def test_ruff_is_installed():
    """Verify ruff is installed and returns a version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("ruff is not installed or not callable via python -m ruff")

def test_black_is_installed():
    """Verify black is installed and returns a version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("black is not installed or not callable via python -m black")

def test_ruff_config_exists():
    """Verify ruff configuration file exists in code/."""
    config_path = os.path.join("code", ".ruff.toml")
    assert os.path.exists(config_path), f"Ruff config missing at {config_path}"

def test_ruff_can_check_code():
    """Verify ruff can successfully run a check on the code directory."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        capture_output=True,
        text=True
    )
    # Ruff returns 0 if no errors, 1 if errors found. Both are valid "runs".
    # We just want to ensure it didn't crash due to missing config or syntax errors in config.
    # If it crashes (non-zero exit due to config error), it would likely be a different code.
    # However, standard check behavior: 0=ok, 1=lint errors.
    # We accept exit code 0 or 1 as a successful invocation.
    assert result.returncode in (0, 1), f"Ruff check failed to run: {result.stderr}"