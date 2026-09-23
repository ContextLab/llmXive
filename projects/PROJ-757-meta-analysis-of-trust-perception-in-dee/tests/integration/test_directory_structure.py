"""
Integration tests to verify the overall project structure and configuration.
"""
import os
from pathlib import Path

def test_project_structure(project_root):
    """Verify the main project directories exist."""
    expected_dirs = [
        "code",
        "data",
        "results",
        "tests"
    ]
    
    for dir_name in expected_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Expected directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_required_test_subdirs(project_root):
    """Verify required test subdirectories exist."""
    unit_dir = project_root / "tests" / "unit"
    integration_dir = project_root / "tests" / "integration"
    
    assert unit_dir.exists() and unit_dir.is_dir()
    assert integration_dir.exists() and integration_dir.is_dir()

def test_pytest_config_loadable(project_root):
    """Verify pytest.ini is present and readable."""
    config_path = project_root / "code" / "pytest.ini"
    assert config_path.exists()
    with open(config_path, 'r') as f:
        content = f.read()
        assert "[pytest]" in content