import os
from pathlib import Path
import subprocess
import pytest

import sys
# Add parent to path to import utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.setup_data_dirs import create_data_directories

@pytest.fixture
def project_root():
    """Get the project root directory."""
    # Assuming the test is run from the project root or a subdirectory
    return Path(__file__).resolve().parent.parent.parent

def test_project_structure_exists(project_root):
    """
    Integration test to verify that the project structure defined in T001 exists.
    This test runs the setup script and verifies the directories are present.
    """
    required_dirs = [
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        "data/raw",
        "data/processed",
        "state",
        "output",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs/paper",
        "docs/reports"
    ]

    # Ensure directories are created
    created = create_data_directories()
    
    # Verify each required directory exists
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        assert full_path.exists(), f"Required directory does not exist: {full_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

def test_run_setup_script(project_root):
    """
    Integration test to verify the setup script can be run successfully.
    """
    script_path = project_root / "code" / "utils" / "setup_data_dirs.py"
    
    assert script_path.exists(), f"Setup script not found: {script_path}"
    
    # Run the script
    result = subprocess.run(
        ["python", str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with return code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    assert "Successfully created" in result.stdout, "Script did not report success"