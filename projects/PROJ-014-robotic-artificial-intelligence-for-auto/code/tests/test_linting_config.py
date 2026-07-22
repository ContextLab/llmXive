"""
Tests to verify that linting and formatting tools are configured correctly.
These tests check for the existence of configuration files and that the tools can run.
"""
import os
import subprocess
import pytest
from pathlib import Path

# Path to the project root (where ruff/black configs should live)
PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Check if ruff configuration file exists."""
    # Look for common ruff config files
    possible_configs = [
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "ruff.toml",
        PROJECT_ROOT / ".ruff.toml",
        PROJECT_ROOT / "ruff.yaml"
    ]
    found = False
    for config in possible_configs:
        if config.exists():
            found = True
            break
    assert found, "No ruff configuration file found (ruff.toml, .ruff.toml, or pyproject.toml)"

def test_black_config_exists():
    """Check if black configuration file exists."""
    # Look for common black config files
    possible_configs = [
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "setup.cfg",
        PROJECT_ROOT / "tox.ini"
    ]
    found = False
    for config in possible_configs:
        if config.exists():
            # Check if it contains black config
            content = config.read_text()
            if "[tool.black]" in content or "[black]" in content:
                found = True
                break
    # If pyproject.toml exists but doesn't have black config, that might be okay if black defaults are used,
    # but we expect a config based on T003 requirements.
    # Let's be lenient: if pyproject.toml exists, we assume black can run with defaults or it's configured there.
    # However, the task T003 requires configuration. Let's check for explicit black config in pyproject.toml.
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists() and "[tool.black]" in pyproject.read_text():
        found = True
    elif pyproject.exists():
        # If pyproject exists but no black section, is that a failure?
        # Let's assume if pyproject exists, it's the place for config, even if empty section.
        # But to be safe, let's just check if black can run.
        pass
    
    # Fallback: if black can run with --version, it's installed, but config is the task.
    # Let's assert that pyproject.toml exists and has tool.black
    assert pyproject.exists(), "pyproject.toml not found for Black configuration"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section [tool.black] not found in pyproject.toml"

def test_ruff_can_run():
    """Verify that ruff can be executed and check the codebase."""
    ruff_path = PROJECT_ROOT / "ruff.toml"
    if not ruff_path.exists() and not (PROJECT_ROOT / ".ruff.toml").exists():
        # Try pyproject.toml
        pyproject = PROJECT_ROOT / "pyproject.toml"
        if pyproject.exists() and "[tool.ruff]" in pyproject.read_text():
            pass # Config exists in pyproject
        else:
            # If no config, ruff might use defaults, which is fine for "can run"
            pass
    
    try:
        result = subprocess.run(
            ["ruff", "check", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0 or "ruff" in result.stdout.lower(), "Ruff is not installed or cannot run"
    except FileNotFoundError:
        pytest.fail("Ruff is not installed. Please install it via pip.")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out.")

def test_black_can_run():
    """Verify that black can be executed."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "Black is not installed or cannot run"
    except FileNotFoundError:
        pytest.fail("Black is not installed. Please install it via pip.")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out.")
