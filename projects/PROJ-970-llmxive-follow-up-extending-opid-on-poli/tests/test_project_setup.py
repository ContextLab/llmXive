"""
Test suite to verify Project Setup (T002) and Dependencies.
Ensures that required libraries are importable and the project structure is valid.
"""
import sys
import importlib

def test_python_version():
    """Verify Python 3.11+ is used."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"

def test_networkx_import():
    """Verify networkx is installed and importable."""
    networkx = importlib.import_module("networkx")
    assert hasattr(networkx, "Graph"), "networkx.Graph not found"

def test_numpy_import():
    """Verify numpy is installed and importable."""
    numpy = importlib.import_module("numpy")
    assert hasattr(numpy, "array"), "numpy.array not found"

def test_pandas_import():
    """Verify pandas is installed and importable."""
    pandas = importlib.import_module("pandas")
    assert hasattr(pandas, "DataFrame"), "pandas.DataFrame not found"

def test_scipy_import():
    """Verify scipy is installed and importable."""
    scipy = importlib.import_module("scipy")
    assert hasattr(scipy, "stats"), "scipy.stats not found"

def test_pytest_import():
    """Verify pytest is installed and importable."""
    pytest = importlib.import_module("pytest")
    assert hasattr(pytest, "mark"), "pytest.mark not found"

def test_project_structure_exists():
    """Verify basic project directories exist."""
    import os
    assert os.path.isdir("code"), "Directory 'code' not found"
    assert os.path.isdir("tests"), "Directory 'tests' not found"
    assert os.path.isfile("requirements.txt"), "File 'requirements.txt' not found"
    assert os.path.isfile("pyproject.toml"), "File 'pyproject.toml' not found"
