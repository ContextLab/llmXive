import subprocess
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in code directory."""
    config_path = PROJECT_ROOT / "code" / ".flake8"
    assert config_path.exists(), f"Missing .flake8 config at {config_path}"
    content = config_path.read_text()
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length" in content, "Missing max-line-length setting in .flake8"

def test_pyproject_toml_exists():
    """Verify pyproject.toml configuration file exists in code directory."""
    config_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert config_path.exists(), f"Missing pyproject.toml at {config_path}"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "line-length" in content, "Missing line-length setting in pyproject.toml"

def test_black_can_parse_config():
    """Verify Black can successfully parse the configuration."""
    result = subprocess.run(
        ["black", "--check", "--config", str(PROJECT_ROOT / "code" / "pyproject.toml"), "--diff", str(PROJECT_ROOT / "code" / "seed.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect exit code 1 if formatting is needed, but 0 or 1 means config was parsed successfully
    # Exit code 2 would mean config parsing error
    assert result.returncode != 2, f"Black failed to parse config: {result.stderr}"

def test_flake8_can_parse_config():
    """Verify flake8 can successfully parse the configuration."""
    result = subprocess.run(
        ["flake8", "--version"],
        cwd=PROJECT_ROOT / "code",
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"flake8 not installed or not working: {result.stderr}"
    
    # Try running flake8 with config on a simple file to ensure config is valid
    result = subprocess.run(
        ["flake8", "--config=.flake8", "--select=E,W", "seed.py"],
        cwd=PROJECT_ROOT / "code",
        capture_output=True,
        text=True
    )
    # Exit code 0 (no issues) or 1 (issues found) are both valid; 2 is config error
    assert result.returncode != 2, f"flake8 failed to parse config: {result.stderr}"