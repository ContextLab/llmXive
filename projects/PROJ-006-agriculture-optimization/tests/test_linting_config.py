"""
Tests for T003: Linting and Formatting Configuration.
Verifies that black, flake8, isort are installed and configured,
and that .gitignore exists.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent

def test_black_is_installed():
    """Verify black is installed and executable."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black not installed or failed: {result.stderr}"
    assert "black" in result.stdout.lower()

def test_flake8_is_installed():
    """Verify flake8 is installed and executable."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Flake8 not installed or failed: {result.stderr}"

def test_isort_is_installed():
    """Verify isort is installed and executable."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Isort not installed or failed: {result.stderr}"

def test_gitignore_exists():
    """Verify .gitignore exists in project root."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), f".gitignore not found at {gitignore_path}"
    assert gitignore_path.is_file(), f".gitignore is not a file"

def test_setup_cfg_exists():
    """Verify setup.cfg exists in project root."""
    project_root = get_project_root()
    setup_cfg_path = project_root / "setup.cfg"
    assert setup_cfg_path.exists(), f"setup.cfg not found at {setup_cfg_path}"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_requirements_txt_includes_dev_tools():
    """Verify requirements.txt includes black, flake8, isort."""
    project_root = get_project_root()
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"

    content = req_path.read_text()
    assert "black" in content, "black not found in requirements.txt"
    assert "flake8" in content, "flake8 not found in requirements.txt"
    assert "isort" in content, "isort not found in requirements.txt"

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Shell commands behave differently on Windows"
)
def test_code_passes_flake8():
    """Verify code passes flake8 checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "src", "tests", "scripts"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    # Allow non-zero exit if there are issues, but log them
    if result.returncode != 0:
        # In a real CI, this would fail. For now, we just assert the command ran.
        # If the project is clean, this should pass.
        # We will assert that the command executed successfully (return code 0 or 1)
        # and that the output is valid.
        # For the purpose of this test task, we assert it runs without crashing.
        assert "No module named" not in result.stderr, "Flake8 module missing"
        # If there are linting errors, that's expected in an active project,
        # but the tool must be runnable.
        # To strictly satisfy "code passes", we assume the code generated for T003 is clean.
        # If the previous state was dirty, this test documents the state.
        # We will assert returncode == 0 to enforce the goal of T003.
        # If it fails, it means the code needs fixing.
        # For this specific task implementation, we assume the generated files are clean.
        # If this test fails, it indicates the codebase needs linting fixes.
        # We will raise an error if flake8 finds issues to enforce T003 completion.
        if result.returncode != 0:
             pytest.fail(f"Flake8 found issues:\n{result.stdout}\n{result.stderr}")
    assert result.returncode == 0, f"Flake8 found issues:\n{result.stdout}\n{result.stderr}"

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Shell commands behave differently on Windows"
)
def test_code_passes_isort():
    """Verify code passes isort checks (dry-run)."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", "src", "tests", "scripts"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    if result.returncode != 0:
        pytest.fail(f"Isort found issues:\n{result.stdout}\n{result.stderr}")
    assert result.returncode == 0, f"Isort found issues:\n{result.stdout}\n{result.stderr}"

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Shell commands behave differently on Windows"
)
def test_code_passes_black():
    """Verify code passes black checks (dry-run)."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "src", "tests", "scripts"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    if result.returncode != 0:
        pytest.fail(f"Black found issues:\n{result.stdout}\n{result.stderr}")
    assert result.returncode == 0, f"Black found issues:\n{result.stdout}\n{result.stderr}"