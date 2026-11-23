"""
Basic test to verify project structure and imports are valid.
"""
import importlib
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_code_package_imports():
    """Verify that core packages can be imported without errors."""
    packages = [
        "code",
        "code.env",
        "code.agent",
        "code.utils",
        "code.experiments",
        "tests",
    ]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError as e:
            raise AssertionError(f"Failed to import {pkg}: {e}")

def test_data_directories_exist():
    """Verify that required data directories exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = [
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "raw", "synthetic_graphs"),
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Directory missing: {d}"
