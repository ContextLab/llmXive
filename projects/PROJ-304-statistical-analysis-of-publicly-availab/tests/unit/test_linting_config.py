"""Tests for linting configuration and tool availability."""
import subprocess
import sys
from pathlib import Path

def test_black_is_installed():
    """Verify black is installed and accessible."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "black" in result.stdout.lower()

def test_ruff_is_installed():
    """Verify ruff is installed and accessible."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "ruff" in result.stdout.lower()

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "pyproject.toml"
    assert config_file.exists(), f"pyproject.toml not found at {config_file}"

def test_black_config_in_pyproject():
    """Verify black configuration exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "pyproject.toml"
    content = config_file.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_ruff_config_in_pyproject():
    """Verify ruff configuration exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "pyproject.toml"
    content = config_file.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "select" in content, "Ruff select rules missing"