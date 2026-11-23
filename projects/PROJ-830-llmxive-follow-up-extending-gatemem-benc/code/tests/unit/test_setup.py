import os
import pytest

def test_directory_structure():
    """
    Verify that the project directory structure is correctly created.
    Asserts existence of all 12 specific directories listed in T001a.
    """
    base_dirs = [
        "src",
        "tests",
        "data",
        "contracts",
        "state",
        "logs",
        "templates",
        "data/raw",
        "data/processed",
        "data/samples",
        "src/gatekeeper",
        "src/utils",
        "src/cli",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    for dir_path in base_dirs:
        full_path = os.path.join(os.getcwd(), dir_path)
        assert os.path.isdir(full_path), f"Directory {dir_path} does not exist."
