"""
Integration test for T002: Directory Creation.
Verifies that the required directory structure exists after running setup_directories.py.
"""
import os
import pytest
import subprocess
import sys

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "artifacts",
    "artifacts/logs",
    "artifacts/weights",
    "artifacts/metrics",
    "data",
    "data/raw",
    "data/processed",
    "data/assets",
    "data/processed/splits"
]

@pytest.fixture(scope="module", autouse=True)
def run_setup_script():
    """Ensure the setup script has been run before testing."""
    # Run the setup script to ensure directories are created
    result = subprocess.run(
        [sys.executable, "code/setup_directories.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    yield

def test_directories_exist():
    """Assert that all required directories created by T002 exist."""
    missing_dirs = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing_dirs.append(d)
    
    assert not missing_dirs, f"The following directories are missing: {missing_dirs}"

def test_code_module_is_importable():
    """Assert that the code directory contains an __init__.py making it a package."""
    init_path = os.path.join("code", "__init__.py")
    assert os.path.isfile(init_path), f"Missing {init_path}"

def test_tests_module_is_importable():
    """Assert that the tests directory contains an __init__.py making it a package."""
    init_path = os.path.join("tests", "__init__.py")
    assert os.path.isfile(init_path), f"Missing {init_path}"

def test_artifacts_module_is_importable():
    """Assert that the artifacts directory contains an __init__.py making it a package."""
    init_path = os.path.join("artifacts", "__init__.py")
    assert os.path.isfile(init_path), f"Missing {init_path}"