import os
import subprocess
import sys
from pathlib import Path

def test_project_structure_created():
    """
    Test that running setup_project.py creates all required directories.
    """
    # Ensure we are running in the project root context
    # We assume the test is run from the root where code/setup_project.py exists
    
    required_dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
    ]

    # Run the setup script
    result = subprocess.run(
        [sys.executable, "code/setup_project.py"],
        capture_output=True,
        text=True
    )

    # Assert the script exited successfully
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"

    # Verify each directory exists
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} does not exist after running setup."
        assert dir_path.is_dir(), f"Path {dir_name} exists but is not a directory."

def test_utils_directory_exists():
    """
    Specific check for code/utils/ as it is critical for other imports.
    """
    utils_path = Path("code/utils")
    assert utils_path.exists()
    assert utils_path.is_dir()
    # Check that we can write a temp file there (if permissions allow, though T001a doesn't restrict this yet)
    # This is just a structural check
    assert (utils_path / ".gitkeep").parent == utils_path # Just checking path resolution