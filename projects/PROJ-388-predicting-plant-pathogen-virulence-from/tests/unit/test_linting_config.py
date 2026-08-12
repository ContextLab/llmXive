"""
Unit tests to verify linting and formatting configurations are present and valid.
These tests check for the existence and basic validity of ruff, black, and pytest configs.
"""
import os
import toml
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_pyproject_toml_exists():
    """Check that pyproject.toml exists at the project root."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist at project root."

def test_pyproject_toml_is_valid():
    """Check that pyproject.toml is valid TOML and contains required sections."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    try:
        config = toml.load(pyproject_path)
    except Exception as e:
        pytest.fail(f"pyproject.toml is not valid TOML: {e}")

    assert "tool" in config, "pyproject.toml must contain [tool] section."
    assert "ruff" in config.get("tool", {}), "pyproject.toml must contain [tool.ruff] section."
    assert "black" in config.get("tool", {}), "pyproject.toml must contain [tool.black] section."
    assert "pytest" in config.get("tool", {}), "pyproject.toml must contain [tool.pytest.ini_options] section."

def test_ruff_config_line_length():
    """Check that ruff line-length is set to 100."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    config = toml.load(pyproject_path)
    ruff_config = config.get("tool", {}).get("ruff", {})
    assert ruff_config.get("line-length") == 100, "Ruff line-length must be 100."

def test_black_config_line_length():
    """Check that black line-length is set to 100."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    config = toml.load(pyproject_path)
    black_config = config.get("tool", {}).get("black", {})
    assert black_config.get("line-length") == 100, "Black line-length must be 100."

def test_pytest_config_exists():
    """Check that pytest configuration exists."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    config = toml.load(pyproject_path)
    pytest_config = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert "testpaths" in pytest_config, "pytest ini_options must contain testpaths."
    assert pytest_config["testpaths"] == ["tests"], "pytest testpaths must be ['tests']."

def test_requirements_txt_contains_dev_deps():
    """Check that requirements.txt contains dev dependencies."""
    req_path = ROOT_DIR / "requirements.txt"
    assert req_path.exists(), "requirements.txt must exist."

    content = req_path.read_text()
    required_dev = ["ruff", "black", "pytest"]
    for dep in required_dev:
        assert any(dep.lower() in line.lower() for line in content.splitlines()), \
            f"requirements.txt must contain {dep}."