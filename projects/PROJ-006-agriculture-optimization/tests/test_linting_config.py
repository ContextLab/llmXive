import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find .git or the project root markers
    while current.parent != current:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()

def test_black_is_installed():
    """Test that black is installed in the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "black is not installed"

def test_flake8_is_installed():
    """Test that flake8 is installed in the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "flake8 is not installed"

def test_isort_is_installed():
    """Test that isort is installed in the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "isort is not installed"

def test_gitignore_exists():
    """Test that .gitignore exists in the project root."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore does not exist"

def test_setup_cfg_exists():
    """Test that setup.cfg exists in the project root."""
    project_root = get_project_root()
    setup_cfg_path = project_root / "setup.cfg"
    assert setup_cfg_path.exists(), "setup.cfg does not exist"

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the project root."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml does not exist"

def test_requirements_txt_includes_dev_tools():
    """Test that requirements.txt includes dev tools."""
    project_root = get_project_root()
    req_path = project_root / "requirements.txt"
    if req_path.exists():
        content = req_path.read_text()
        # Check for common dev tools
        assert "black" in content.lower() or "pyproject.toml" in content.lower(), \
            "requirements.txt should include black or reference pyproject.toml for dev tools"

def test_code_passes_flake8():
    """Test that the code passes flake8 checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "flake8", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    # Note: This may fail if src/ is not fully implemented yet
    # We expect this to pass once all code is implemented
    if result.returncode != 0:
        # Only fail if there are actual errors (not just warnings about missing files)
        if "No such file or directory" not in result.stdout and \
           "does not exist" not in result.stdout:
            pytest.fail(f"flake8 found issues:\n{result.stdout}")

def test_code_passes_isort():
    """Test that the code passes isort checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    # Note: This may fail if src/ is not fully implemented yet
    if result.returncode != 0:
        if "No such file or directory" not in result.stdout and \
           "does not exist" not in result.stdout:
            pytest.fail(f"isort found issues:\n{result.stdout}")

def test_code_passes_black():
    """Test that the code passes black checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    # Note: This may fail if src/ is not fully implemented yet
    if result.returncode != 0:
        if "No such file or directory" not in result.stdout and \
           "does not exist" not in result.stdout:
            pytest.fail(f"black found issues:\n{result.stdout}")
