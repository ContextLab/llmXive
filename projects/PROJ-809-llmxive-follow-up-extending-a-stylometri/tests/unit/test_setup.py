"""
Unit tests for project setup verification (T001).
Ensures the directory structure created by setup_project.py is correct.
"""
import os
import pytest
from pathlib import Path

# Assume tests are in tests/unit/, so root is 3 levels up from this file
# or we can dynamically find the project root
def get_project_root():
    current = Path(__file__).resolve()
    # Go up: tests/unit -> tests -> project_root
    return current.parent.parent

@pytest.fixture
def root_path():
    return get_project_root()

def test_base_directories_exist(root_path):
    """Verify all base directories from T001 exist."""
    base_dirs = [
        "code", "data", "artifacts", "contracts", "tests", "state", "docs", "specs"
    ]
    for d in base_dirs:
        path = root_path / d
        assert path.exists(), f"Base directory missing: {path}"
        assert path.is_dir(), f"Path is not a directory: {path}"

def test_data_subdirectories_exist(root_path):
    """Verify data subdirectories exist."""
    sub_dirs = ["data/raw", "data/processed", "data/hybrid"]
    for d in sub_dirs:
        path = root_path / d
        assert path.exists(), f"Data subdirectory missing: {path}"

def test_artifacts_subdirectories_exist(root_path):
    """Verify artifacts subdirectories exist."""
    sub_dirs = ["artifacts/models", "artifacts/metrics", "artifacts/figures"]
    for d in sub_dirs:
        path = root_path / d
        assert path.exists(), f"Artifacts subdirectory missing: {path}"

def test_tests_subdirectories_exist(root_path):
    """Verify tests subdirectories exist."""
    sub_dirs = ["tests/unit", "tests/contract", "tests/integration"]
    for d in sub_dirs:
        path = root_path / d
        assert path.exists(), f"Tests subdirectory missing: {path}"

def test_requirements_file_exists(root_path):
    """Verify requirements.txt exists at root."""
    req_file = root_path / "requirements.txt"
    assert req_file.exists(), "requirements.txt missing"
    # Check it's not empty
    assert req_file.stat().st_size > 0, "requirements.txt is empty"

def test_setup_script_exists(root_path):
    """Verify the setup script exists."""
    setup_script = root_path / "code" / "setup_project.py"
    assert setup_script.exists(), "code/setup_project.py missing"
    # Verify it's executable (syntactically valid python)
    try:
        with open(setup_script, 'r') as f:
            compile(f.read(), setup_script, 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in setup script: {e}")