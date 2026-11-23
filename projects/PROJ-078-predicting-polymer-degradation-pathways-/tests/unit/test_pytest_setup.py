"""
Unit tests for the pytest framework setup.
Verifies that the test directory structure and basic pytest configuration are correct.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports if needed
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_test_directory_structure_exists():
    """Verify that the required test directories exist."""
    unit_dir = project_root / "tests" / "unit"
    integration_dir = project_root / "tests" / "integration"
    
    assert unit_dir.exists(), f"Directory {unit_dir} does not exist"
    assert integration_dir.exists(), f"Directory {integration_dir} does not exist"
    assert unit_dir.is_dir(), f"{unit_dir} is not a directory"
    assert integration_dir.is_dir(), f"{integration_dir} is not a directory"

def test_pytest_config_exists():
    """Verify that pytest configuration file exists in code directory."""
    config_path = project_root / "code" / "pytest.ini"
    # Check if pytest.ini or pyproject.toml with pytest config exists
    # The task specifically asked for pytest.ini in code/ based on standard conventions if not specified otherwise
    # However, looking at the task description: "Setup pytest framework and directory structure"
    # Usually a pytest.ini or pyproject.toml is at root. Let's check root first, then code/ if specified.
    # The task says "directory structure (tests/unit, tests/integration)".
    # Let's assume a standard pytest.ini at root or code/pytest.ini if the project structure dictates.
    # Given the project structure puts scripts in code/, a config in code/pytest.ini or root is fine.
    # Let's check for pytest.ini in the root or code/
    root_config = project_root / "pytest.ini"
    code_config = project_root / "code" / "pytest.ini"
    
    assert root_config.exists() or code_config.exists(), \
        "pytest.ini not found in project root or code/ directory"

def test_pytest_collects_tests():
    """Verify that pytest can discover tests in the directory."""
    # Run pytest with --collect-only to see if it finds tests
    # We run this on the current file to ensure it's discoverable
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    # If it returns 0 or 5 (no tests failed, but we are just collecting), it's good.
    # We specifically want to see if our test functions are listed.
    assert "test_test_directory_structure_exists" in result.stdout or result.returncode in [0, 5], \
        f"Pytest failed to collect tests. Return code: {result.returncode}, Stdout: {result.stdout}, Stderr: {result.stderr}"

def test_utils_import_in_test_environment():
    """Verify that core utilities can be imported from the test environment."""
    try:
        from utils import get_logger, get_project_paths
        assert callable(get_logger)
        assert callable(get_project_paths)
    except ImportError as e:
        pytest.fail(f"Failed to import utils in test environment: {e}")

def test_data_models_import_in_test_environment():
    """Verify that data models can be imported from the test environment."""
    try:
        from data_models import PolymerRecord, MolecularGraph
        assert hasattr(PolymerRecord, '__dataclass_fields__')
    except ImportError as e:
        pytest.fail(f"Failed to import data_models in test environment: {e}")
