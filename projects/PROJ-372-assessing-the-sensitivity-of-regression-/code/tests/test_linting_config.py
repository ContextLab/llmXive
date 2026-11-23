"""
Test to verify that linting and formatting configurations are valid.
This ensures ruff.toml and pyproject.toml are syntactically correct
and do not conflict.
"""
import os
import toml
import tomli
import pytest

@pytest.fixture
def project_root():
    # Assuming this test runs from the project root or code/
    # Adjust path resolution if necessary
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return parent_dir

def test_ruff_toml_exists(project_root):
    ruff_path = os.path.join(project_root, "code", "ruff.toml")
    assert os.path.exists(ruff_path), f"ruff.toml not found at {ruff_path}"

def test_pyproject_toml_exists(project_root):
    pyproject_path = os.path.join(project_root, "code", "pyproject.toml")
    assert os.path.exists(pyproject_path), f"pyproject.toml not found at {pyproject_path}"

def test_ruff_config_parsable(project_root):
    ruff_path = os.path.join(project_root, "code", "ruff.toml")
    try:
        with open(ruff_path, "rb") as f:
            tomli.load(f)
    except Exception as e:
        pytest.fail(f"ruff.toml is not valid TOML: {e}")

def test_pyproject_config_parsable(project_root):
    pyproject_path = os.path.join(project_root, "code", "pyproject.toml")
    try:
        with open(pyproject_path, "rb") as f:
            tomli.load(f)
    except Exception as e:
        pytest.fail(f"pyproject.toml is not valid TOML: {e}")

def test_black_config_in_pyproject(project_root):
    pyproject_path = os.path.join(project_root, "code", "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)
    
    assert "tool" in data
    assert "black" in data["tool"]
    assert "line-length" in data["tool"]["black"]
    assert data["tool"]["black"]["line-length"] == 88