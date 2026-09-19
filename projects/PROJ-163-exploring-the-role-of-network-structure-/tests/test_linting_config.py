"""
Test suite to verify that linting and formatting configurations are correctly set up.
These tests check that the configuration files exist and contain the expected settings.
"""
import os
import pytest
import toml

PROJECT_ROOT = os.path.dirname(os.dirname(os.path.abspath(__file__)))

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    assert os.path.isfile(path), f"pyproject.toml not found at {path}"

def test_black_configuration_present():
    """Verify Black configuration exists in pyproject.toml."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "black" in config["tool"], "Black configuration missing in pyproject.toml"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black line-length setting missing"
    assert black_config["line-length"] == 88, f"Expected Black line-length 88, got {black_config['line-length']}"
    assert "target-version" in black_config, "Black target-version missing"
    assert "py311" in black_config["target-version"], "Python 3.11 target not set for Black"

def test_ruff_configuration_present():
    """Verify Ruff configuration exists in pyproject.toml."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "ruff" in config["tool"], "Ruff configuration missing in pyproject.toml"

    ruff_config = config["tool"]["ruff"]
    assert "target-version" in ruff_config, "Ruff target-version missing"
    assert ruff_config["target-version"] == "py311", "Python 3.11 target not set for Ruff"
    assert "select" in ruff_config, "Ruff select rules missing"

def test_ruff_toml_exists():
    """Verify .ruff.toml exists at project root."""
    path = os.path.join(PROJECT_ROOT, ".ruff.toml")
    assert os.path.isfile(path), f".ruff.toml not found at {path}"

def test_flake8_configuration_present():
    """Verify .flake8 configuration exists at project root."""
    path = os.path.join(PROJECT_ROOT, ".flake8")
    assert os.path.isfile(path), f".flake8 not found at {path}"

    with open(path, "r") as f:
        content = f.read()

    assert "max-line-length" in content, "max-line-length setting missing in .flake8"
    assert "88" in content, "Expected max-line-length 88 in .flake8"
    assert "E501" in content, "E501 ignore setting missing in .flake8"

def test_pytest_configuration_present():
    """Verify pytest configuration exists in pyproject.toml."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "pytest.ini_options" in config["tool"], "pytest configuration missing"

    pytest_config = config["tool"]["pytest.ini_options"]
    assert "testpaths" in pytest_config, "testpaths setting missing"
    assert "tests" in pytest_config["testpaths"], "tests directory not set as testpath"
    assert "pythonpath" in pytest_config, "pythonpath setting missing"
    assert "." in pytest_config["pythonpath"], "Current directory not in pythonpath"