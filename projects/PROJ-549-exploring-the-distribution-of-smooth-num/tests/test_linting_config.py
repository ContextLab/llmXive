"""
Tests to verify that linting and formatting configuration files exist and are valid.
These tests ensure T003 requirements are met.
"""
import os
import subprocess
import sys
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in the code directory."""
    flake8_path = os.path.join(CODE_DIR, ".flake8")
    assert os.path.exists(flake8_path), f".flake8 not found at {flake8_path}"
    with open(flake8_path, "r") as f:
        content = f.read()
    assert "[flake8]" in content, ".flake8 must contain [flake8] section"
    assert "max-line-length" in content, ".flake8 must define max-line-length"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and contains Black/Pytest config."""
    pyproject_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    assert os.path.exists(pyproject_path), f"pyproject.toml not found at {pyproject_path}"
    with open(pyproject_path, "r") as f:
        content = f.read()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black]"
    assert "[tool.pytest.ini_options]" in content, "pyproject.toml must contain pytest config"

def test_black_executable_exists():
    """Verify black is installed and runnable."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or not runnable")

def test_flake8_executable_exists():
    """Verify flake8 is installed and runnable."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        assert len(result.stdout.strip()) > 0
    except subprocess.CalledProcessError:
        pytest.fail("flake8 is not installed or not runnable")

def test_code_directory_syntax_valid():
    """Verify all .py files in code/ are syntactically valid."""
    for root, _, files in os.walk(CODE_DIR):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()
                    compile(source, filepath, "exec")
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {filepath}: {e}")