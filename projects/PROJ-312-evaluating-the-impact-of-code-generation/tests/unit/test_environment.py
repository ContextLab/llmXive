"""
Test for T002b: Environment verification.
Tests that the required packages are importable.
"""
import importlib
import pytest

REQUIRED_PACKAGES = [
    'requests',
    'pandas',
    'scipy',
    'matplotlib',
    'yaml',
    'tqdm',
    'statsmodels'
]

@pytest.mark.parametrize("package", REQUIRED_PACKAGES)
def test_package_import(package):
    """Test that each required package can be imported."""
    try:
        importlib.import_module(package)
    except ImportError:
        pytest.fail(f"Package {package} could not be imported")

def test_pandas_version():
    """Test that pandas is installed (version check optional)."""
    import pandas
    assert pandas.__version__ is not None

def test_matplotlib_version():
    """Test that matplotlib is installed."""
    import matplotlib
    assert matplotlib.__version__ is not None