"""
Unit tests for the project structure setup logic.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to simulate the module structure or import directly
# Since setup_project_structure is in code/, we add the parent to path
import sys
import importlib.util

def load_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_create_directory_structure(temp_project_root):
    """Test that create_directory_structure creates the expected folders."""
    # Load the module dynamically to avoid path issues in tests
    script_path = Path(__file__).parent.parent / "code" / "setup_project_structure.py"
    setup_module = load_module_from_path("setup_project_structure_test", script_path)
    
    # Mock the get_project_root to return our temp dir
    original_get_root = setup_module.get_project_root
    setup_module.get_project_root = lambda: temp_project_root

    try:
        created = setup_module.create_directory_structure(temp_project_root)
        
        expected_dirs = [
            "code", "tests", "data", "data/raw", "data/processed",
            "figures", "state", "state/projects", "specs", "docs"
        ]
        
        for expected in expected_dirs:
            assert (temp_project_root / expected).exists(), f"Directory {expected} was not created"
            assert (temp_project_root / expected).is_dir(), f"{expected} is not a directory"
        
        # Check that the returned list contains the created paths
        for created_path_str in created:
            assert Path(created_path_str).exists()
    finally:
        # Restore original function
        setup_module.get_project_root = original_get_root

def test_main_execution(temp_project_root, capsys):
    """Test the main function execution."""
    script_path = Path(__file__).parent.parent / "code" / "setup_project_structure.py"
    setup_module = load_module_from_path("setup_project_structure_main_test", script_path)
    
    original_get_root = setup_module.get_project_root
    setup_module.get_project_root = lambda: temp_project_root

    try:
        exit_code = setup_module.main()
        captured = capsys.readouterr()
        
        assert exit_code == 0, "Main function should return 0 on success"
        assert "Project root identified" in captured.out
        assert "Project structure setup complete" in captured.out
    finally:
        setup_module.get_project_root = original_get_root