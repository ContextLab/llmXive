"""
Test suite for T003: Linting and Formatting Configuration.
Verifies that ruff and black are correctly configured and functional.
"""
import subprocess
import sys
from pathlib import Path
import pytest


def get_project_root():
    """Get the project root directory (code/)."""
    return Path(__file__).parent.parent


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists with ruff and black configuration."""
    root = get_project_root()
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section missing"
    assert "[tool.black]" in content, "Black configuration section missing"
    assert "target-version" in content, "Target version not configured"


def test_ruff_check_syntax():
    """Verify ruff can run and check syntax without crashing."""
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select=E9,F63,F7,F82", "."],
        cwd=root,
        capture_output=True,
        text=True
    )
    # Ruff might return non-zero if there are actual errors, but it should not crash
    # We just verify the command runs successfully (exit code 0 or 1, not 2+ for syntax error)
    assert result.returncode < 2, f"Ruff check failed to run: {result.stderr}"


def test_black_check_syntax():
    """Verify black can run and check formatting without crashing."""
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "."],
        cwd=root,
        capture_output=True,
        text=True
    )
    # Black returns 0 if formatted, 1 if not, but should not crash
    assert result.returncode < 2, f"Black check failed to run: {result.stderr}"


def test_ruff_config_loadable():
    """Verify ruff can load and validate its configuration."""
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "config", "list"],
        cwd=root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff config load failed: {result.stderr}"
    assert "line-length" in result.stdout, "Ruff config not loaded correctly"


def test_black_config_loadable():
    """Verify black can load and validate its configuration."""
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(root / "pyproject.toml"), "--help"],
        cwd=root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black config load failed: {result.stderr}"