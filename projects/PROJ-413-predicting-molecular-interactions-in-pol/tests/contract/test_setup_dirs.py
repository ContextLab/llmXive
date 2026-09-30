import os
from pathlib import Path
import pytest
import sys

# Import the main function from the setup script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_dirs import main as setup_main

def test_project_structure_created():
    """Test that the project directory structure is created correctly."""
    project_root = Path(__file__).parent.parent.parent
    project_name = "PROJ-413-predicting-molecular-interactions-in-pol"
    project_path = project_root / project_name

    # Ensure the project path exists before testing
    if not project_path.exists():
        # Run the setup function to create it
        setup_main()

    assert project_path.exists(), "Project root directory must exist"

    # Define expected directories
    expected_dirs = [
        "data/raw",
        "data/curated",
        "data/processed",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "results",
        "analysis",
        "docs",
        "tests/contract",
        "tests/integration",
    ]

    for dir_name in expected_dirs:
        dir_path = project_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} must exist"
        assert dir_path.is_dir(), f"{dir_name} must be a directory"

def test_setup_main_returns_zero():
    """Test that the main function returns 0 on success."""
    # Run the main function
    result = setup_main()
    assert result == 0, "Main function should return 0 on success"