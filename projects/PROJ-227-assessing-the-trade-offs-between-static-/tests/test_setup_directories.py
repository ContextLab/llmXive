import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
# Assuming this test runs from the project root
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

def test_directories_created():
    """
    Verify that the required directories exist after running main().
    """
    # Run the setup
    main()

    # Determine project root (parent of code dir)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent.parent / "code"
    project_root = code_dir.parent

    required_dirs = [
        "data/raw",
        "data/processed",
        "state",
        "code",
        "tests"
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

    # Check nested structure if applicable
    project_name = "PROJ-227-assessing-the-trade-offs-between-static-"
    nested_path = project_root / "projects" / project_name
    
    for dir_path in required_dirs:
        full_path = nested_path / dir_path
        assert full_path.exists(), f"Nested directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

    print("All required directories verified successfully.")
