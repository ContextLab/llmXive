"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import yaml
import toml
import pytest

# Determine the path to the code directory relative to this test file
# Assuming tests/unit/ and code/ are siblings in the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = os.path.join(CODE_DIR, ".flake8")
    assert os.path.isfile(flake8_path), f"Missing .flake8 config at {flake8_path}"

def test_flake8_config_valid():
    """Verify .flake8 is readable (basic validation)."""
    flake8_path = os.path.join(CODE_DIR, ".flake8")
    try:
        with open(flake8_path, "r") as f:
            content = f.read()
            assert "max-line-length" in content, "max-line-length not configured"
    except Exception as e:
        pytest.fail(f"Could not read .flake8: {e}")

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    toml_path = os.path.join(CODE_DIR, "pyproject.toml")
    assert os.path.isfile(toml_path), f"Missing pyproject.toml at {toml_path}"

def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML and contains black config."""
    toml_path = os.path.join(CODE_DIR, "pyproject.toml")
    try:
        with open(toml_path, "r") as f:
            data = toml.load(f)
            assert "tool" in data
            assert "black" in data["tool"], "Black configuration missing in pyproject.toml"
            assert "line-length" in data["tool"]["black"], "Black line-length missing"
    except Exception as e:
        pytest.fail(f"Could not parse pyproject.toml: {e}")

def test_lint_script_exists():
    """Verify lint_and_format.py exists."""
    script_path = os.path.join(CODE_DIR, "lint_and_format.py")
    assert os.path.isfile(script_path), f"Missing lint script at {script_path}"

def test_lint_script_importable():
    """Verify lint_and_format.py is syntactically valid and importable."""
    script_path = os.path.join(CODE_DIR, "lint_and_format.py")
    try:
        with open(script_path, "r") as f:
            compile(f.read(), script_path, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in lint_and_format.py: {e}")