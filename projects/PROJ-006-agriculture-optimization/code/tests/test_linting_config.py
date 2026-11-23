import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def test_black_is_installed():
    """Test that black is installed."""
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("black is not installed")

def test_flake8_is_installed():
    """Test that flake8 is installed."""
    try:
        subprocess.run(["flake8", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("flake8 is not installed")

def test_isort_is_installed():
    """Test that isort is installed."""
    try:
        subprocess.run(["isort", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("isort is not installed")

def test_gitignore_exists():
    """Test that .gitignore exists."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file does not exist"

def test_setup_cfg_exists():
    """Test that pyproject.toml exists (modern replacement for setup.cfg)."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml file does not exist"

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml file does not exist"

def test_requirements_txt_includes_dev_tools():
    """Test that requirements.txt includes dev tools."""
    project_root = get_project_root()
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt does not exist"
    
    content = requirements_path.read_text()
    dev_tools = ["black", "flake8", "isort", "pytest"]
    for tool in dev_tools:
        assert tool in content.lower(), f"{tool} is not listed in requirements.txt"

def test_code_passes_flake8():
    """Test that code passes flake8 checks."""
    project_root = get_project_root()
    result = subprocess.run(
        ["flake8", str(project_root / "code")],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # We expect flake8 to be configured with max-line-length=88
    # If there are violations, the test fails
    if result.returncode != 0:
        pytest.fail(f"flake8 found violations:\n{result.stdout}\n{result.stderr}")

def test_code_passes_isort():
    """Test that code passes isort checks."""
    project_root = get_project_root()
    result = subprocess.run(
        ["isort", "--check", "--diff", str(project_root / "code")],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"isort found violations:\n{result.stdout}\n{result.stderr}")

def test_code_passes_black():
    """Test that code passes black checks."""
    project_root = get_project_root()
    result = subprocess.run(
        ["black", "--check", "--diff", str(project_root / "code")],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"black found violations:\n{result.stdout}\n{result.stderr}")