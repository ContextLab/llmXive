"""
Unit tests for T005a: Project directory structure creation.
Verifies that the required directories exist after running create_project_structure.py.
"""
import os
import pytest
from pathlib import Path
import subprocess
import sys

# The project root is assumed to be the parent of the 'code' directory
# when running tests from the 'code' directory or via pytest from root.
# We calculate it relative to this test file.
TEST_FILE_DIR = Path(__file__).parent
CODE_DIR = TEST_FILE_DIR.parent
PROJECT_ROOT = CODE_DIR.parent

REQUIRED_DIRECTORIES = [
    "src",
    "tests",
    "contracts",
    "data",
    "analysis",
    "src/data",
    "src/utils",
    "src/analysis",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "analysis/results",
    "figures",
    "state",
    "state/projects",
    "docs",
]

def test_directory_exists():
    """
    Test that all required project directories exist.
    This test assumes that scripts/create_project_structure.py has been run.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRECTORIES:
        full_path = PROJECT_ROOT / dir_name
        if not full_path.exists():
            missing_dirs.append(dir_name)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_name} (exists but is not a directory)")
    
    if missing_dirs:
        pytest.fail(f"The following required directories are missing or invalid:\n{os.linesep.join(missing_dirs)}")

def test_config_files_exist():
    """
    Test that the configuration files created by T005b exist in the root.
    (T005b creates pyproject.toml and requirements.txt)
    """
    config_files = [
        "pyproject.toml",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_name in config_files:
        full_path = PROJECT_ROOT / file_name
        if not full_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        pytest.fail(f"The following configuration files are missing (expected from T005b):\n{os.linesep.join(missing_files)}")

def test_structure_created_by_script():
    """
    Integration-style test: Run the creation script and verify it reports success.
    This ensures the script itself works as expected.
    """
    script_path = PROJECT_ROOT / "scripts" / "create_project_structure.py"
    
    if not script_path.exists():
        pytest.skip("Creation script not found; assuming structure already exists or script not yet added.")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # The script should exit with code 0 on success
    assert result.returncode == 0, f"Script failed with output: {result.stderr}"
    
    # Verify the directories exist after running
    for dir_name in REQUIRED_DIRECTORIES:
        full_path = PROJECT_ROOT / dir_name
        assert full_path.exists() and full_path.is_dir(), f"Directory {dir_name} does not exist after running script."