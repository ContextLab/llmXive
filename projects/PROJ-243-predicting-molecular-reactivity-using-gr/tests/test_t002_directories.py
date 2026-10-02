"""
Test suite for Task T002: Verify that code, artifacts, and tests directories exist.
"""
import os
import pytest
from config import get_config

def test_t002_code_directory_exists():
    """Verify 'code' directory exists at project root."""
    config = get_config()
    code_path = os.path.join(config["project_root"], "code")
    assert os.path.isdir(code_path), f"Directory 'code' does not exist at {code_path}"

def test_t002_artifacts_directory_exists():
    """Verify 'artifacts' directory exists at project root."""
    config = get_config()
    artifacts_path = os.path.join(config["project_root"], "artifacts")
    assert os.path.isdir(artifacts_path), f"Directory 'artifacts' does not exist at {artifacts_path}"

def test_t002_tests_directory_exists():
    """Verify 'tests' directory exists at project root."""
    config = get_config()
    tests_path = os.path.join(config["project_root"], "tests")
    assert os.path.isdir(tests_path), f"Directory 'tests' does not exist at {tests_path}"

def test_t002_directories_are_writable():
    """Verify that the created directories are writable."""
    config = get_config()
    dirs_to_check = ["code", "artifacts", "tests"]
    
    for dir_name in dirs_to_check:
        dir_path = os.path.join(config["project_root"], dir_name)
        test_file = os.path.join(dir_path, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except IOError as e:
            pytest.fail(f"Directory {dir_path} is not writable: {e}")
