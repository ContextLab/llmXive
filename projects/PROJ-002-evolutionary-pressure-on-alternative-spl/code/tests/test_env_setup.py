"""
Tests to verify environment setup and dependency installation.
"""
import os
import sys
from pathlib import Path

def test_python_version():
    """Verify Python version is 3.11+."""
    version = sys.version_info
    assert version.major == 3, f"Expected Python 3.x, got {version.major}.x"
    assert version.minor >= 11, f"Expected Python 3.11+, got 3.{version.minor}"

def test_requirements_exists():
    """Verify requirements.txt exists in code directory."""
    code_dir = Path(__file__).parent.parent
    req_file = code_dir / "requirements.txt"
    assert req_file.exists(), f"{req_file} not found"

def test_requirements_r_exists():
    """Verify requirements-r.txt exists in code directory."""
    code_dir = Path(__file__).parent.parent
    req_file = code_dir / "requirements-r.txt"
    assert req_file.exists(), f"{req_file} not found"

def test_flake8_config_exists():
    """Verify .flake8 configuration exists."""
    code_dir = Path(__file__).parent.parent
    config_file = code_dir / ".flake8"
    assert config_file.exists(), f"{config_file} not found"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    code_dir = Path(__file__).parent.parent
    config_file = code_dir / "pyproject.toml"
    assert config_file.exists(), f"{config_file} not found"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    code_dir = Path(__file__).parent.parent
    config_file = code_dir / ".pre-commit-config.yaml"
    assert config_file.exists(), f"{config_file} not found"

def test_imports_available():
    """Verify core dependencies can be imported."""
    try:
        import pandas
        import numpy
        import yaml
        import biopython
        import requests
        import tqdm
        import sklearn
        import loguru
    except ImportError as e:
        pytest.fail(f"Core dependency missing: {e}")