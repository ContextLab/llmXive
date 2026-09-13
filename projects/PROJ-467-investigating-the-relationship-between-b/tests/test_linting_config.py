import os
import subprocess
from pathlib import Path
import pytest

def test_pyproject_toml_exists():
    assert Path("pyproject.toml").exists()

def test_pyproject_toml_contains_black_config():
    with open("pyproject.toml", "r") as f:
        assert "black" in f.read()

def test_pyproject_toml_contains_isort_config():
    with open("pyproject.toml", "r") as f:
        assert "isort" in f.read()

def test_pyproject_toml_contains_ruff_config():
    with open("pyproject.toml", "r") as f:
        assert "ruff" in f.read()

def test_pyproject_toml_contains_pytest_config():
    with open("pyproject.toml", "r") as f:
        assert "pytest" in f.read()

def test_gitignore_exists():
    assert Path(".gitignore").exists()

def test_gitignore_contains_data_patterns():
    with open(".gitignore", "r") as f:
        assert "data/" in f.read()
        assert "*.nii" in f.read()

def test_ruff_check_passes():
    try:
        subprocess.run(["ruff", "check"], check=True)
    except subprocess.CalledProcessError:
        pytest.fail("ruff check failed")

def test_black_check_passes():
    try:
        subprocess.run(["black", "--check", "."], check=True)
    except subprocess.CalledProcessError:
        pytest.fail("black check failed")

def test_isort_check_passes():
    try:
        subprocess.run(["isort", "--check-only", "."], check=True)
    except subprocess.CalledProcessError:
        pytest.fail("isort check failed")
