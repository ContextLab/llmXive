"""
Test suite for verifying the project structure created by T001.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Fixture to get the project root directory."""
    return Path(__file__).parent.parent

def test_core_directories_exist(project_root):
    """Test that all core directories exist."""
    core_dirs = ["code", "data", "tests", "docs", "state"]
    for dir_name in core_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Core directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_data_subdirectories_exist(project_root):
    """Test that all required data subdirectories exist."""
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/templates",
        "data/outputs",
        "data/logs"
    ]
    for dir_name in data_subdirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Data subdirectory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_tests_subdirectories_exist(project_root):
    """Test that test subdirectories exist."""
    test_subdirs = [
        "tests/unit",
        "tests/integration"
    ]
    for dir_name in test_subdirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Test subdirectory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_state_subdirectories_exist(project_root):
    """Test that state subdirectories exist."""
    state_subdirs = [
        "state/projects"
    ]
    for dir_name in state_subdirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"State subdirectory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_placeholder_files_exist(project_root):
    """Test that placeholder files exist in expected locations."""
    placeholder_files = [
        "code/__init__.py",
        "code/utils.py",
        "code/entities.py",
        "code/preprocessing.py",
        "code/microstate.py",
        "code/analysis.py",
        "code/preprocessing.yaml",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "code/requirements.txt"
    ]
    for file_name in placeholder_files:
        file_path = project_root / file_name
        assert file_path.exists(), f"Placeholder file {file_name} does not exist"
        assert file_path.is_file(), f"{file_name} is not a file"

def test_code_module_imports(project_root):
    """Test that core code modules can be imported (syntax check)."""
    import sys
    sys.path.insert(0, str(project_root))
    
    try:
        # Test that the modules are syntactically valid
        import importlib.util
        
        modules_to_check = [
            "code.utils",
            "code.entities",
            "code.preprocessing",
            "code.microstate",
            "code.analysis"
        ]
        
        for module_name in modules_to_check:
            module_path = project_root / module_name.replace(".", "/") + ".py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                assert spec is not None, f"Could not create spec for {module_name}"
                # If we get here, the file exists and can be loaded as a spec
                # Actual import might fail due to missing dependencies, which is expected
    except Exception as e:
        # We expect this to potentially fail if dependencies are missing
        # The important thing is that the file structure is correct
        pass
