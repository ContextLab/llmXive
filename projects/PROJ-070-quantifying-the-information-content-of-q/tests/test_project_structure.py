import os
import pytest

def test_required_directories_exist():
    """
    Test that the required project directory structure is present.
    This test ensures T001 (Project Structure) is satisfied.
    """
    required_dirs = [
        "code",
        "code/models",
        "code/utils",
        "code/validators",
        "data",
        "data/external",
        "data/processed",
        "data/generated",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "figures"
    ]

    missing = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing.append(dir_path)

    assert not missing, f"Missing required directories: {missing}"

def test_init_files_exist():
    """
    Test that __init__.py files exist in required packages.
    """
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "data/__init__.py"
    ]

    missing = []
    for file_path in init_files:
        if not os.path.isfile(file_path):
            missing.append(file_path)

    assert not missing, f"Missing required __init__.py files: {missing}"