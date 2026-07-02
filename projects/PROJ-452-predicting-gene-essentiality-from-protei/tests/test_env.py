"""
Basic environment and dependency sanity check.
Verifies that all required packages listed in requirements.txt are importable.
"""
import sys

def test_imports():
    """Verify all core dependencies can be imported."""
    modules = [
        "networkx",
        "pandas",
        "scipy",
        "statsmodels",
        "requests",
        "yaml",
        "numpy",
        "Bio",
        "dendropy",
    ]
    for mod_name in modules:
        try:
            __import__(mod_name)
        except ImportError as e:
            raise AssertionError(f"Failed to import {mod_name}: {e}")

def test_python_version():
    """Verify Python version is >= 3.11."""
    if sys.version_info < (3, 11):
        raise AssertionError(
            f"Python version {sys.version_info} is less than 3.11"
        )