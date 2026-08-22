import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root():
    return Path(__file__).parent.parent

def test_black_is_installed():
    result = subprocess.run([sys.executable, "-m", "black", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Black is not installed or not working"

def test_flake8_is_installed():
    result = subprocess.run([sys.executable, "-m", "flake8", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Flake8 is not installed or not working"

def test_isort_is_installed():
    result = subprocess.run([sys.executable, "-m", "isort", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "isort is not installed or not working"

def test_gitignore_exists():
    root = get_project_root()
    gitignore = root / ".gitignore"
    assert gitignore.exists(), ".gitignore file does not exist"

def test_setup_cfg_exists():
    root = get_project_root()
    setup_cfg = root / "setup.cfg"
    assert setup_cfg.exists(), "setup.cfg file does not exist"

def test_pyproject_toml_exists():
    root = get_project_root()
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml file does not exist"

def test_requirements_txt_includes_dev_tools():
    root = get_project_root()
    req_file = root / "requirements.txt"
    assert req_file.exists(), "requirements.txt does not exist"
    content = req_file.read_text()
    assert "black" in content, "black not in requirements.txt"
    assert "flake8" in content, "flake8 not in requirements.txt"
    assert "isort" in content, "isort not in requirements.txt"

def test_code_passes_flake8():
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "src", "scripts", "tests"],
        capture_output=True,
        text=True,
        cwd=root
    )
    assert result.returncode == 0, f"Flake8 found issues:\n{result.stdout}\n{result.stderr}"

def test_code_passes_isort():
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", "src", "scripts", "tests"],
        capture_output=True,
        text=True,
        cwd=root
    )
    assert result.returncode == 0, f"isort found issues:\n{result.stdout}\n{result.stderr}"

def test_code_passes_black():
    root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "src", "scripts", "tests"],
        capture_output=True,
        text=True,
        cwd=root
    )
    assert result.returncode == 0, f"Black found issues:\n{result.stdout}\n{result.stderr}"