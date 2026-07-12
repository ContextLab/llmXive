"""
Unit tests for the project setup script.
Verifies that the required directory structure is created.
"""
import os
import shutil
import tempfile
import pytest

# We will test the logic by mocking the os.makedirs and checking calls,
# or by running the script in a temp directory if needed.
# For this task, we verify the existence of the directories after running the setup.

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "reports/figures",
    "tests/unit",
    "tests/contract"
]

@pytest.fixture(scope="module", autouse=True)
def setup_environment(tmp_path_factory):
    """
    Create a temporary directory to run the setup script against,
    to avoid cluttering the actual project root during tests if run from a different context.
    However, since the script uses relative paths, we assume the test runner
    is executed from the project root or we adjust logic to test the logic directly.
    
    For robustness, we test the function logic directly if possible, or run the script
    in a temp dir and check results.
    """
    # Save current dir
    original_cwd = os.getcwd()
    # Create temp dir
    temp_dir = tmp_path_factory.mktemp("project_root")
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Restore
    os.chdir(original_cwd)

def test_directory_creation(setup_environment):
    """Test that all required directories are created."""
    # Import and run the setup logic
    # Since setup_project.py is in the code folder, we need to add it to path
    import sys
    sys.path.insert(0, os.path.join(setup_environment, "code"))
    
    # We need to import the function, but the script has a __main__ block.
    # Let's re-implement the logic here for the test to be self-contained 
    # or import the module if it's placed correctly.
    # Given the artifact is code/setup_project.py, we can import it.
    
    # Note: In a real CI, the file exists. Here we assume the file content
    # provided in the artifact is available.
    
    # Let's just verify the directory structure creation logic
    import importlib.util
    spec = importlib.util.spec_from_file_location("setup_project", os.path.join(setup_environment, "code", "setup_project.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    result = module.create_directories()
    assert result is True, "Setup script should return True on success"

    for dir_name in REQUIRED_DIRS:
        full_path = os.path.join(setup_environment, dir_name)
        assert os.path.isdir(full_path), f"Directory {dir_name} was not created"

def test_existing_directories_handling(setup_environment):
    """Test that the script handles existing directories gracefully."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("setup_project", os.path.join(setup_environment, "code", "setup_project.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Run first time
    result1 = module.create_directories()
    assert result1 is True

    # Run second time (dirs already exist)
    result2 = module.create_directories()
    assert result2 is True, "Script should succeed even if directories already exist"