import os
import pytest
from pathlib import Path
from setup_structure import main

def test_directory_creation():
    """
    Verifies that the setup_structure script creates the required directories.
    This is a functional test to ensure T001 is satisfied.
    """
    required_dirs = [
        "code/simulation",
        "code/analysis",
        "code/visualization",
        "code/reporting",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "contracts",
    ]

    # Run the main function to ensure directories are created
    result = main()
    assert result == 0, "Setup script should return 0 on success"

    # Verify existence
    for dir_name in required_dirs:
        path = Path(dir_name)
        assert path.exists(), f"Directory {dir_name} should exist after running setup_structure.py"
        assert path.is_dir(), f"{dir_name} should be a directory"

def test_code_utils_exists():
    """
    Verifies that the code/utils directory exists, which is required for the logging API surface.
    """
    path = Path("code/utils")
    assert path.exists(), "code/utils must exist to support logging imports"
    assert path.is_dir()