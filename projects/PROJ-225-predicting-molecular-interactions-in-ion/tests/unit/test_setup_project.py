import os
import pytest
from code.setup_project import main

def test_directory_structure_created(tmp_path, monkeypatch):
    """
    Test that the main function creates the required directory structure.
    Uses a temporary directory to avoid polluting the real project tree during tests.
    """
    # Change CWD to tmp_path to simulate the project root
    monkeypatch.chdir(tmp_path)

    # Run the setup function
    exit_code = main()

    assert exit_code == 0

    # Verify expected directories exist
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/validation",
        "models",
        "contracts",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "specs/001-predicting-molecular-interactions-in-ion",
        "logs"
    ]

    for dir_name in expected_dirs:
        assert os.path.isdir(os.path.join(tmp_path, dir_name)), f"Directory {dir_name} was not created."

def test_idempotent(tmp_path, monkeypatch):
    """
    Test that running the script twice doesn't cause errors.
    """
    monkeypatch.chdir(tmp_path)
    
    # First run
    assert main() == 0
    
    # Second run
    assert main() == 0