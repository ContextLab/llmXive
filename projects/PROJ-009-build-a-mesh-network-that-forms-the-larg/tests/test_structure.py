"""
Tests to verify the project structure has been created correctly.
"""
import os
from pathlib import Path
import pytest

REQUIRED_DIRS = [
  "code/orchestrator",
  "code/orchestrator/workers",
  "code/analysis",
  "code/simulation",
  "data/raw",
  "data/processed",
  "tests/contract",
  "tests/integration",
  "tests/unit",
  "specs/001-mesh-supercomputer",
  "contracts",
  "state",
  "figures",
]

REQUIRED_PACKAGES = [
  "code",
  "code/orchestrator",
  "code/orchestrator/workers",
  "code/analysis",
  "code/simulation",
  "tests",
  "tests/contract",
  "tests/integration",
  "tests/unit",
]

def test_required_directories_exist():
    """Verify all required directories exist."""
    root = Path(".")
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = root / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
    
    assert not missing, f"Missing directories: {missing}"

def test_required_packages_have_init():
    """Verify all Python packages have __init__.py."""
    root = Path(".")
    missing_init = []
    for pkg_dir in REQUIRED_PACKAGES:
        init_file = root / pkg_dir / "__init__.py"
        if not init_file.exists():
            missing_init.append(str(init_file))
    
    assert not missing_init, f"Missing __init__.py files: {missing_init}"

def test_data_directories_writable():
    """Verify data directories are writable."""
    root = Path(".")
    test_files = []
    try:
        for data_dir in ["data/raw", "data/processed"]:
            dir_path = root / data_dir
            if dir_path.exists():
                test_file = dir_path / ".write_test"
                test_file.touch()
                test_files.append(test_file)
                test_file.unlink()
    except Exception as e:
        pytest.fail(f"Data directory not writable: {e}")

def test_code_directories_writable():
    """Verify code directories are writable."""
    root = Path(".")
    test_files = []
    try:
        for code_dir in ["code/orchestrator", "code/analysis", "code/simulation"]:
            dir_path = root / code_dir
            if dir_path.exists():
                test_file = dir_path / ".write_test"
                test_file.touch()
                test_files.append(test_file)
                test_file.unlink()
    except Exception as e:
        pytest.fail(f"Code directory not writable: {e}")
