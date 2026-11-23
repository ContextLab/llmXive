"""
Tests for environment setup and dependency verification.
"""
import os
import sys
from pathlib import Path

def test_python_version():
    """Verify Python version is >= 3.9"""
    assert sys.version_info >= (3, 9), f"Python 3.9+ required, got {sys.version}"

def test_requirements_exists():
    """Verify requirements.txt exists"""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt not found"

def test_requirements_r_exists():
    """Verify renv.lock exists"""
    renv_file = Path(__file__).parent.parent / "renv.lock"
    assert renv_file.exists(), "renv.lock not found"

def test_flake8_config_exists():
    """Verify .flake8 config exists"""
    flake8_file = Path(__file__).parent.parent / ".flake8"
    assert flake8_file.exists(), ".flake8 not found"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists"""
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_file.exists(), "pyproject.toml not found"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists"""
    precommit_file = Path(__file__).parent.parent / ".pre-commit-config.yaml"
    assert precommit_file.exists(), ".pre-commit-config.yaml not found"

def test_imports_available():
    """Verify core dependencies can be imported"""
    try:
        import pandas
        import numpy
        import yaml
        import requests
        import tqdm
        import loguru
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import dependency: {e}")