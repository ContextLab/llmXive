"""
Test that project dependencies are correctly installed and importable.
"""
import sys
import pytest

# List of required packages as per T002
REQUIRED_PACKAGES = [
    "qiskit_ibm_runtime",
    "networkx",
    "pandas",
    "scipy",
    "matplotlib",
    "requests",
    "pytest",
]

def test_python_version():
    """Ensure we are running Python 3.11 or higher."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"

@pytest.mark.parametrize("package", REQUIRED_PACKAGES)
def test_package_imports(package):
    """Verify all required packages can be imported."""
    try:
        __import__(package)
    except ImportError as e:
        pytest.fail(f"Failed to import {package}: {e}")

def test_networkx_version():
    """Check networkx version is sufficient."""
    import networkx
    # Just a sanity check that it's a modern version
    assert tuple(map(int, networkx.__version__.split(".")[:2])) >= (3, 0)

def test_pandas_version():
    """Check pandas version is sufficient."""
    import pandas
    assert tuple(map(int, pandas.__version__.split(".")[:2])) >= (2, 0)