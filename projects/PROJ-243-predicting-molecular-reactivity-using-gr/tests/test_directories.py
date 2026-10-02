"""
Unit tests for T002: Directory Creation Verification.
Verifies that the required project directories exist after running setup_directories.py.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "artifacts",
    "tests",
    "data/raw",
    "data/processed",
    "data/assets"
]

@pytest.mark.parametrize("directory", REQUIRED_DIRS)
def test_directory_exists(directory: str) -> None:
    """Assert that a required project directory exists."""
    full_path = os.path.join(os.getcwd(), directory)
    assert os.path.isdir(full_path), f"Directory {full_path} does not exist."

def test_artifacts_subdirectories_exist() -> None:
    """Assert that artifacts has required subdirectories."""
    base = os.path.join(os.getcwd(), "artifacts")
    assert os.path.isdir(base), "Artifacts directory missing"

    required_subdirs = ["logs", "weights", "metrics", "final_archive"]
    for subdir in required_subdirs:
        path = os.path.join(base, subdir)
        assert os.path.isdir(path), f"Missing artifacts subdirectory: {subdir}"

def test_code_subdirectories_exist() -> None:
    """Assert that code has required subdirectories."""
    base = os.path.join(os.getcwd(), "code")
    assert os.path.isdir(base), "Code directory missing"

    required_subdirs = ["data", "utils", "models"]
    for subdir in required_subdirs:
        path = os.path.join(base, subdir)
        assert os.path.isdir(path), f"Missing code subdirectory: {subdir}"
