"""
Basic integration test to verify the project structure.
This test verifies that the directory structure and basic imports work.
"""
import pytest
from pathlib import Path

def test_test_directories_exist():
    """Verify that unit and integration test directories exist."""
    project_root = Path(__file__).parent.parent
    unit_dir = project_root / "tests" / "unit"
    integration_dir = project_root / "tests" / "integration"
    
    assert unit_dir.exists(), f"Unit test directory missing: {unit_dir}"
    assert integration_dir.exists(), f"Integration test directory missing: {integration_dir}"
    assert unit_dir.is_dir(), f"Unit test path is not a directory: {unit_dir}"
    assert integration_dir.is_dir(), f"Integration test path is not a directory: {integration_dir}"

def test_pytest_config_exists():
    """Verify that pytest configuration file exists."""
    project_root = Path(__file__).parent.parent
    config_file = project_root / "pytest.ini"
    assert config_file.exists(), f"pytest.ini missing: {config_file}"