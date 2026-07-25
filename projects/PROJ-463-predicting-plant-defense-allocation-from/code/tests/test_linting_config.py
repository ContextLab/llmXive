import subprocess
import sys
from pathlib import Path
import pytest
import tomli

@pytest.fixture
def project_root():
    # Assuming tests are run from code/ or root, adjust if necessary
    # The task artifacts are in code/, so we look for pyproject.toml relative to this file
    return Path(__file__).parent.parent

def test_black_config_valid(project_root):
    """Verify that black configuration in pyproject.toml is valid and targets Python 3.11."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config
    assert "black" in config["tool"]
    black_config = config["tool"]["black"]

    assert black_config.get("line-length") == 88
    assert "py311" in black_config.get("target-version", [])

def test_ruff_config_valid(project_root):
    """Verify that ruff configuration in pyproject.toml is valid and targets Python 3.11."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config
    assert "ruff" in config["tool"]
    ruff_config = config["tool"]["ruff"]

    assert ruff_config.get("line-length") == 88
    assert ruff_config.get("target-version") == "py311"

    # Check linting section exists
    assert "lint" in ruff_config
    assert "select" in ruff_config["lint"]
    # Ensure E, F, I are selected (common standards)
    selected = ruff_config["lint"]["select"]
    assert "E" in selected
    assert "F" in selected
    assert "I" in selected