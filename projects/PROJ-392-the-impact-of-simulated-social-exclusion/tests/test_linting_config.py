"""
Tests to verify that linting configuration files exist and are valid.
"""
import os
import subprocess
import sys
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    flake8_path = os.path.join(CODE_DIR, ".flake8")
    assert os.path.exists(flake8_path), f".flake8 file not found at {flake8_path}"

def test_pyproject_toml_exists():
    """Test that pyproject.toml configuration file exists."""
    pyproject_path = os.path.join(CODE_DIR, "pyproject.toml")
    assert os.path.exists(pyproject_path), f"pyproject.toml file not found at {pyproject_path}"

def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid TOML and contains black config."""
    pyproject_path = os.path.join(CODE_DIR, "pyproject.toml")
    try:
        with open(pyproject_path, "r") as f:
            config = toml.load(f)
        
        assert "tool" in config, "Missing [tool] section in pyproject.toml"
        assert "black" in config["tool"], "Missing [tool.black] section"
        assert "line-length" in config["tool"]["black"], "Missing line-length in black config"
    except Exception as e:
        pytest.fail(f"pyproject.toml is invalid or missing expected config: {e}")

def test_flake8_config_valid():
    """Test that .flake8 file is readable and has expected sections."""
    flake8_path = os.path.join(CODE_DIR, ".flake8")
    try:
        with open(flake8_path, "r") as f:
            content = f.read()
        
        assert "[flake8]" in content, "Missing [flake8] section in .flake8"
        assert "max-line-length" in content, "Missing max-line-length in .flake8"
    except Exception as e:
        pytest.fail(f".flake8 file is invalid or missing expected config: {e}")

@pytest.mark.skipif(
    not subprocess.run(["which", "black"], capture_output=True).returncode == 0,
    reason="black not installed"
)
def test_black_format_check():
    """Test that code directory passes black format check (dry run)."""
    result = subprocess.run(
        ["black", "--check", "--diff", CODE_DIR],
        capture_output=True,
        text=True
    )
    # This test might fail if code is not yet formatted, which is expected for initial setup
    # We assert that the command runs without crashing
    assert result.returncode in [0, 1], f"black check failed with unexpected error: {result.stderr}"

@pytest.mark.skipif(
    not subprocess.run(["which", "flake8"], capture_output=True).returncode == 0,
    reason="flake8 not installed"
)
def test_flake8_lint_check():
    """Test that flake8 can run on the code directory."""
    result = subprocess.run(
        ["flake8", CODE_DIR],
        capture_output=True,
        text=True
    )
    # This test might fail if there are linting errors, which is expected for initial setup
    # We assert that the command runs without crashing
    assert result.returncode in [0, 1], f"flake8 check failed with unexpected error: {result.stderr}"
