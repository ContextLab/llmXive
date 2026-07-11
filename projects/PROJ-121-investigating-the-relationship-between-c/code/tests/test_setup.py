"""
Basic setup validation test to ensure the project structure is correct.
"""
import pytest
import sys
import os

def test_python_version():
    """Ensure Python 3.11+ is being used."""
    assert sys.version_info >= (3, 11), "Python 3.11 or higher is required."

def test_package_imports():
    """Verify that the main package can be imported."""
    try:
        from src import __version__
        assert __version__ is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src package: {e}")

def test_requirements_exist():
    """Verify requirements.txt exists in the project root."""
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    assert os.path.isfile(req_path), "requirements.txt not found"

def test_dependencies_installable():
    """Basic check that dependencies can be imported (if installed)."""
    # This test will be skipped if dependencies aren't installed yet
    deps = ["numpy", "pandas", "scipy", "astropy", "requests"]
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            pytest.skip(f"Dependency {dep} not installed yet")