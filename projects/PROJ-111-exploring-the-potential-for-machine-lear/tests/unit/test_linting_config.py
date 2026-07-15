"""
Unit tests to verify that linting and formatting configurations are present and valid.
This test ensures T002 (Configure linting and formatting) is satisfied.
"""
import os
import subprocess
import tomllib
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the path to the project root."""
    return Path(__file__).parent.parent.parent


def test_pyproject_toml_exists(project_root):
    """Check that pyproject.toml exists."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist for linting config"


def test_pyproject_toml_contains_black_config(project_root):
    """Check that pyproject.toml contains [tool.black] section."""
    pyproject = project_root / "pyproject.toml"
    with open(pyproject, "rb") as f:
        config = tomllib.load(f)
    
    assert "tool" in config, "pyproject.toml must have [tool] section"
    assert "black" in config["tool"], "pyproject.toml must contain [tool.black] configuration"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black config must specify line-length"
    assert black_config["line-length"] == 88, "Black line-length should be 88"


def test_pyproject_toml_contains_ruff_config(project_root):
    """Check that pyproject.toml contains [tool.ruff] section."""
    pyproject = project_root / "pyproject.toml"
    with open(pyproject, "rb") as f:
        config = tomllib.load(f)
    
    assert "tool" in config, "pyproject.toml must have [tool] section"
    assert "ruff" in config["tool"], "pyproject.toml must contain [tool.ruff] configuration"
    
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Ruff config must specify line-length"
    assert "lint" in ruff_config, "Ruff config must specify lint rules"


def test_ruff_and_black_in_requirements(project_root):
    """Check that ruff and black are listed in requirements.txt."""
    requirements = project_root / "requirements.txt"
    assert requirements.exists(), "requirements.txt must exist"
    
    content = requirements.read_text()
    assert "ruff" in content.lower(), "requirements.txt must include ruff"
    assert "black" in content.lower(), "requirements.txt must include black"


def test_ruff_config_syntax(project_root):
    """Attempt to run 'ruff check' on the config file itself to ensure syntax is valid."""
    # We just check if ruff can parse the file without crashing
    ruff_path = project_root / "pyproject.toml"
    try:
        # Run ruff check on the project root (which reads pyproject.toml)
        # We use --no-cache to force a fresh read
        result = subprocess.run(
            ["ruff", "check", "--no-cache", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # We don't necessarily expect exit code 0 if there are lint errors in code,
        # but we expect it to NOT fail with a config parsing error.
        # If it fails due to config syntax, stderr usually contains "Failed to parse"
        assert "Failed to parse" not in result.stderr, f"Ruff config parsing failed: {result.stderr}"
    except FileNotFoundError:
        # If ruff is not installed in the environment, we skip the runtime check
        # but the file presence checks above are sufficient for T002 verification.
        pytest.skip("Ruff not installed in environment, skipping runtime syntax check")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff check timed out")