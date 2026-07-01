"""
Unit tests for project setup and initialization (T008).
Verifies Python 3.11 environment and dependencies.
"""
import os
import sys
import pytest
from pathlib import Path


def test_python_version_minimum():
    """Test that Python 3.11+ is being used."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version_info}"


def test_requirements_file_exists():
    """Test that requirements.txt exists."""
    requirements_path = Path("code/requirements.txt")
    assert requirements_path.exists(), "requirements.txt must exist"
    assert requirements_path.stat().st_size > 0, "requirements.txt must not be empty"


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    pyproject_path = Path("code/pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"
    assert pyproject_path.stat().st_size > 0, "pyproject.toml must not be empty"


def test_critical_dependencies_importable():
    """Test that critical dependencies can be imported."""
    critical_packages = ["numpy", "pandas", "yaml", "scipy"]

    for pkg in critical_packages:
        try:
            __import__(pkg)
        except ImportError as e:
            pytest.fail(f"Critical package {pkg} not importable: {e}")


def test_numpy_version():
    """Test that numpy is available and has a reasonable version."""
    import numpy as np
    version = tuple(map(int, np.__version__.split(".")[:2]))
    assert version >= (1, 24), f"numpy 1.24+ required, found {np.__version__}"


def test_pandas_version():
    """Test that pandas is available and has a reasonable version."""
    import pandas as pd
    version = tuple(map(int, pd.__version__.split(".")[:2]))
    assert version >= (2, 0), f"pandas 2.0+ required, found {pd.__version__}"


def test_project_structure_exists():
    """Test that required project directories exist."""
    required_dirs = [
        "code/src",
        "code/tests",
        "code/data",
        "code/state",
        "code/contracts"
    ]

    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Directory {dir_path} must exist"


def test_setup_script_exists():
    """Test that setup_project.py exists."""
    setup_path = Path("code/setup_project.py")
    assert setup_path.exists(), "setup_project.py must exist"