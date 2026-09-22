import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_installed():
    """Test that ruff is installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "ruff"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "ruff is not installed"

def test_black_installed():
    """Test that black is installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "black"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "black is not installed"

def test_ruff_config_exists():
    """Test that ruff configuration exists."""
    root_dir = Path(__file__).resolve().parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "ruff configuration missing in pyproject.toml"

def test_black_config_exists():
    """Test that black configuration exists."""
    root_dir = Path(__file__).resolve().parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content or "line-length" in content, "black configuration missing in pyproject.toml"

def test_precommit_config_exists():
    """Test that pre-commit configuration exists."""
    root_dir = Path(__file__).resolve().parent.parent
    precommit_path = root_dir / ".pre-commit-config.yaml"
    assert precommit_path.exists(), ".pre-commit-config.yaml not found"

def test_run_lint_script_exists():
    """Test that run_lint.py script exists."""
    root_dir = Path(__file__).resolve().parent.parent
    script_path = root_dir / "scripts" / "run_lint.py"
    assert script_path.exists(), "scripts/run_lint.py not found"

def test_run_format_script_exists():
    """Test that run_format.py script exists."""
    root_dir = Path(__file__).resolve().parent.parent
    script_path = root_dir / "scripts" / "run_format.py"
    assert script_path.exists(), "scripts/run_format.py not found"

def test_ruff_check_passes():
    """Test that ruff check passes on the codebase."""
    root_dir = Path(__file__).resolve().parent.parent
    code_dir = root_dir / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Test that black check passes on the codebase."""
    root_dir = Path(__file__).resolve().parent.parent
    code_dir = root_dir / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"