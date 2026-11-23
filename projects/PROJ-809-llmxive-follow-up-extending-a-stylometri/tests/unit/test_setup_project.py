"""
Unit test for the `setup_project` script.

The test invokes the `main` function and then checks that all required
directories have been created under the expected location.
"""
import os
from pathlib import Path

# Import the script's main function
from setup_project import main as setup_main

def test_directory_structure_creation(tmp_path, monkeypatch):
    """
    Ensure that running `setup_main` creates the correct directory tree.

    The test uses a temporary directory as the repository root to avoid
    polluting the real project workspace.
    """
    # Patch the current working directory to a temporary location
    monkeypatch.chdir(tmp_path)

    # Run the setup script
    setup_main()

    # Define the expected base path
    base_path = tmp_path / "projects" / "PROJ-809-llmxive-follow-up-extending-a-stylometri"

    # List of directories that must exist relative to the base path
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/hybrid",
        "artifacts/models",
        "artifacts/metrics",
        "contracts",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state",
    ]

    # Verify each expected directory exists
    for rel_dir in expected_dirs:
        dir_path = base_path / rel_dir
        assert dir_path.is_dir(), f"Missing expected directory: {dir_path}"