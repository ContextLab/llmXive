"""
Basic test to verify that the project directory structure is correctly set up.
"""
import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Assert that all required directories for the project exist.
    """
    base = Path(".")
    required_dirs = [
        "data/raw",
        "data/processed",
        "results/figures",
        "code",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "contracts",
        "specs"
    ]
    
    for dir_str in required_dirs:
        dir_path = base / dir_str
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_code_init_exists():
    """
    Assert that the code/__init__.py file exists and is importable.
    """
    init_path = Path("code/__init__.py")
    assert init_path.exists(), "code/__init__.py is missing"
    
    # Try importing to ensure it's syntactically valid
    try:
        import code
    except ImportError as e:
        pytest.fail(f"Failed to import code module: {e}")