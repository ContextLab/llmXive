"""
Smoke tests to verify linting configuration files exist and are valid TOML/YAML.
These tests ensure the project setup for linting (T003) was successful.
"""
import os
import toml

def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    config_path = os.path.join("code", ".ruff.toml")
    assert os.path.isfile(config_path), f"Configuration file missing: {config_path}"

def test_pyproject_exists():
    """Verify pyproject.toml exists in the code directory."""
    config_path = os.path.join("code", "pyproject.toml")
    assert os.path.isfile(config_path), f"Configuration file missing: {config_path}"

def test_pyproject_valid_toml():
    """Verify pyproject.toml is valid TOML and contains black/pytest sections."""
    config_path = os.path.join("code", "pyproject.toml")
    try:
        with open(config_path, "r") as f:
            data = toml.load(f)
        assert "tool" in data
        assert "black" in data["tool"], "Missing [tool.black] section"
        assert "pytest" in data["tool"], "Missing [tool.pytest] section"
    except Exception as e:
        assert False, f"Failed to parse or validate pyproject.toml: {e}"

def test_requirements_includes_linters():
    """Verify requirements.txt includes ruff and black."""
    req_path = os.path.join("requirements.txt")
    assert os.path.isfile(req_path), "requirements.txt missing"
    with open(req_path, "r") as f:
        content = f.read().lower()
    assert "ruff" in content, "Missing 'ruff' in requirements.txt"
    assert "black" in content, "Missing 'black' in requirements.txt"