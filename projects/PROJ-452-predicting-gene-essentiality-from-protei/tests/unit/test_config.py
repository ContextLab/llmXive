"""
Unit tests to verify that the project structure and configuration tools are correctly set up.
This test ensures that the linting/formatting configuration is valid by attempting to load
the project config and run basic validation.
"""
import os
import sys
import subprocess
from pathlib import Path

import pytest
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import load_config, get_path

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in the project root."""
    root = Path(__file__).parent.parent.parent
    assert (root / "pyproject.toml").exists(), "pyproject.toml not found"

def test_ruff_config_exists():
    """Verify .ruff.toml exists."""
    root = Path(__file__).parent.parent.parent
    assert (root / ".ruff.toml").exists(), ".ruff.toml not found"

def test_black_config_exists():
    """Verify .black.toml exists."""
    root = Path(__file__).parent.parent.parent
    assert (root / ".black.toml").exists(), ".black.toml not found"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    root = Path(__file__).parent.parent.parent
    assert (root / ".pre-commit-config.yaml").exists(), ".pre-commit-config.yaml not found"

def test_requirements_valid():
    """Verify that required dependencies are listed in pyproject.toml."""
    root = Path(__file__).parent.parent.parent
    with open(root / "pyproject.toml", "r") as f:
        content = f.read()

    required_deps = [
        "networkx",
        "pandas",
        "scipy",
        "statsmodels",
        "requests",
        "pyyaml",
        "numpy",
        "biopython",
        "dendropy",
    ]

    for dep in required_deps:
        assert dep.lower() in content.lower(), f"Dependency {dep} not found in pyproject.toml"

def test_scripts_exist():
    """Verify linting and formatting scripts exist."""
    root = Path(__file__).parent.parent.parent
    assert (root / "scripts" / "format.sh").exists(), "scripts/format.sh not found"
    assert (root / "scripts" / "lint.sh").exists(), "scripts/lint.sh not found"

def test_config_loads():
    """Verify that config.py can be loaded and basic functions work."""
    # This implicitly tests that the environment is set up correctly
    # If pyproject.toml or dependencies are missing, this might fail during import
    # but we assume T002 passed. This ensures the structure is coherent.
    try:
        config = load_config()
        assert isinstance(config, dict)
    except Exception as e:
        pytest.fail(f"Failed to load config: {e}")
