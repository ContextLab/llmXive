import subprocess
import sys
import os
from pathlib import Path
import pytest

def get_project_root():
    return Path(__file__).parent.parent

def test_ruff_installed():
    """Test that ruff is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("ruff is not installed or not working.")

def test_black_installed():
    """Test that black is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or not working.")

def test_ruff_config_exists():
    """Test that ruff configuration file exists."""
    root = get_project_root()
    assert (root / ".ruff.toml").exists() or (root / "pyproject.toml").exists()

def test_black_config_exists():
    """Test that black configuration file exists."""
    root = get_project_root()
    config = root / "pyproject.toml"
    if not config.exists():
        pytest.fail("pyproject.toml not found for black config")
    
    content = config.read_text()
    assert "[tool.black]" in content

def test_precommit_config_exists():
    """Test that pre-commit configuration exists (optional but recommended)."""
    root = get_project_root()
    # We expect a .pre-commit-config.yaml or similar if pre-commit is used, 
    # but for this task we verify the existence of the config files we created.
    assert (root / ".ruff.toml").exists()
    assert (root / "pyproject.toml").exists()

def test_run_lint_script_exists():
    """Test that run_lint.py script exists."""
    root = get_project_root()
    script = root / "scripts" / "run_lint.py"
    assert script.exists()

def test_run_format_script_exists():
    """Test that run_format.py script exists."""
    root = get_project_root()
    script = root / "scripts" / "run_format.py"
    assert script.exists()

def test_ruff_check_passes():
    """Test that ruff check passes on the codebase."""
    root = get_project_root()
    cmd = [sys.executable, "-m", "ruff", "check", str(root)]
    try:
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=True)
        # If check=True passed, stdout/stderr should be clean or empty
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Ruff check failed:\n{e.stdout}\n{e.stderr}")

def test_black_check_passes():
    """Test that black check passes on the codebase."""
    root = get_project_root()
    cmd = [sys.executable, "-m", "black", "--check", str(root)]
    try:
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=True)
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Black check failed:\n{e.stdout}\n{e.stderr}")
