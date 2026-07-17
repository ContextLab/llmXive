"""
Tests to verify that linting and formatting configurations are present and valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent

@pytest.fixture
def pyproject_path(project_root):
    return project_root / "code" / "pyproject.toml"

def test_pyproject_exists(project_root):
    """Test that pyproject.toml exists in the code directory."""
    code_dir = project_root / "code"
    assert code_dir.exists(), "code/ directory must exist"
    pyproject = code_dir / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist in code/"

def test_black_config_present(pyproject_path):
    """Test that Black configuration is present in pyproject.toml."""
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section [tool.black] must be present"
    assert "line-length" in content, "Black line-length setting must be present"

def test_ruff_config_present(pyproject_path):
    """Test that Ruff configuration is present in pyproject.toml."""
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section [tool.ruff] must be present"
    assert "select" in content, "Ruff 'select' setting must be present"

def test_setup_linting_script_exists(project_root):
    """Test that setup_linting.py exists."""
    code_dir = project_root / "code"
    script_path = code_dir / "setup_linting.py"
    assert script_path.exists(), "setup_linting.py must exist in code/"

def test_setup_linting_script_executable(project_root):
    """Test that setup_linting.py can be executed without errors."""
    script_path = project_root / "code" / "setup_linting.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root / "code",
        capture_output=True,
        text=True
    )
    # We expect success or at least valid execution (returncode 0 or 1 if tools missing)
    # But the script should not crash with syntax errors
    assert "SyntaxError" not in result.stderr, f"Script has syntax errors: {result.stderr}"

def test_black_check_compatible(project_root):
    """Test that black check runs without configuration errors."""
    pyproject_path = project_root / "code" / "pyproject.toml"
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(pyproject_path), "--check", "--diff", "."],
        cwd=project_root / "code",
        capture_output=True,
        text=True
    )
    # We don't require it to pass (code might not be formatted yet), but config must be valid
    assert "Invalid" not in result.stderr and "Error" not in result.stderr, f"Black config error: {result.stderr}"

def test_ruff_check_compatible(project_root):
    """Test that ruff check runs without configuration errors."""
    pyproject_path = project_root / "code" / "pyproject.toml"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(pyproject_path), "."],
        cwd=project_root / "code",
        capture_output=True,
        text=True
    )
    # We don't require it to pass (code might have lint errors), but config must be valid
    assert "Invalid" not in result.stderr and "Error" not in result.stderr, f"Ruff config error: {result.stderr}"