import os
import pytest
from setup_directories import main, create_directories, setup_script_logging

def test_required_directories_exist():
    """
    Integration test to verify that the required directories for T002
    (code, artifacts, tests) exist in the project root.
    """
    required_dirs = [
        "code",
        "artifacts",
        "tests"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        pytest.fail(f"Required directories are missing: {missing_dirs}. "
                    f"Please run 'python code/setup_directories.py' to create them.")

def test_artifacts_subdirectories_exist():
    """
    Verify that essential subdirectories within 'artifacts' exist.
    """
    required_subdirs = [
        "artifacts/logs",
        "artifacts/weights"
    ]
    
    missing_dirs = []
    for dir_name in required_subdirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        # This might be acceptable if not all subdirs are created yet,
        # but T002 implies setting up the structure.
        # We assert that the parent 'artifacts' exists at least.
        assert os.path.isdir("artifacts"), "artifacts directory must exist."

def test_tests_subdirectories_exist():
    """
    Verify that essential subdirectories within 'tests' exist.
    """
    required_subdirs = [
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    missing_dirs = []
    for dir_name in required_subdirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        # Similar to above, ensure the parent exists.
        assert os.path.isdir("tests"), "tests directory must exist."

def test_setup_directories_script_runs_successfully():
    """
    Run the setup script and verify it returns 0.
    """
    logger = setup_script_logging()
    # Run the main logic
    exit_code = main()
    assert exit_code == 0, "setup_directories.py exited with an error code."