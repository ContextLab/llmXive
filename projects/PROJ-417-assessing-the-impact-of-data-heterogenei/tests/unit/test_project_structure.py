"""
Unit tests to verify the project directory structure created by T001.
"""
import os
import pytest
from pathlib import Path

# Expected directories relative to the project root
EXPECTED_DIRS = [
    "code/simulation",
    "code/analysis",
    "code/visualization",
    "code/reporting",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/results",
    "tests/unit",
    "tests/integration",
    "contracts",
]

# Expected __init__.py files
EXPECTED_INITS = [
    "code/__init__.py",
    "code/simulation/__init__.py",
    "code/analysis/__init__.py",
    "code/visualization/__init__.py",
    "code/reporting/__init__.py",
    "code/utils/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]

@pytest.fixture
def project_root():
    # Assume tests are run from the project root or parent of tests/
    # We look for 'code' directory to determine root
    current = Path.cwd()
    if (current / "code").exists():
        return current
    parent = current.parent
    if (parent / "code").exists():
        return parent
    raise FileNotFoundError("Could not determine project root")

def test_directories_exist(project_root):
    """Verify all required directories exist."""
    missing = []
    for dir_name in EXPECTED_DIRS:
        path = project_root / dir_name
        if not path.exists() or not path.is_dir():
            missing.append(dir_name)
    
    assert not missing, f"Missing directories: {missing}"

def test_init_files_exist(project_root):
    """Verify all required __init__.py files exist."""
    missing = []
    for file_name in EXPECTED_INITS:
        path = project_root / file_name
        if not path.exists() or not path.is_file():
            missing.append(file_name)
    
    assert not missing, f"Missing __init__.py files: {missing}"

def test_code_structure_is_package(project_root):
    """Ensure code directory is a valid Python package."""
    code_init = project_root / "code" / "__init__.py"
    assert code_init.exists(), "code/__init__.py must exist"
    
    # Try to import the package (sanity check)
    try:
        import code
        assert code is not None
    except ImportError as e:
        pytest.fail(f"Failed to import 'code' package: {e}")
