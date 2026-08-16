"""
Unit tests to verify linting and formatting configuration.
These tests ensure that the project adheres to the defined code style.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_installed():
    """Test that Ruff is installed and accessible."""
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.fail("Ruff is not installed or not accessible")

def test_black_installed():
    """Test that Black is installed and accessible."""
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.fail("Black is not installed or not accessible")

def test_ruff_config_exists():
    """Test that Ruff configuration file exists."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".ruff.toml"
    
    assert config_path.exists(), f"Ruff config not found at {config_path}"

def test_black_config_exists():
    """Test that Black configuration exists in pyproject.toml."""
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration not found in pyproject.toml"

def test_precommit_config_exists():
    """Test that pre-commit configuration file exists."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".pre-commit-config.yaml"
    
    assert config_path.exists(), f"Pre-commit config not found at {config_path}"

def test_run_lint_script_exists():
    """Test that run_lint.py script exists."""
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "scripts" / "run_lint.py"
    
    assert script_path.exists(), f"run_lint.py not found at {script_path}"

def test_run_format_script_exists():
    """Test that run_format.py script exists."""
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "scripts" / "run_format.py"
    
    assert script_path.exists(), f"run_format.py not found at {script_path}"

@pytest.mark.skipif(
    not os.environ.get("RUN_LINT_TESTS"),
    reason="Skipping actual lint/format execution in CI unless explicitly requested"
)
def test_ruff_check_passes():
    """Run Ruff check on the code directory (skipped by default)."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

@pytest.mark.skipif(
    not os.environ.get("RUN_LINT_TESTS"),
    reason="Skipping actual lint/format execution in CI unless explicitly requested"
)
def test_black_check_passes():
    """Run Black check on the code directory (skipped by default)."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"