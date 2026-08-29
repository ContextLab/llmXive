import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the setup_project module.
# Since this test is in tests/unit, we need to add the parent of tests to the path,
# or assume the test runner adds the project root to sys.path.
# The standard approach is to add the project root (where code/ and tests/ live) to path.
# Assuming this test is run from the project root:
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.setup_project import main

def test_structure_creation(tmp_path):
    """
    Verify that the main function creates the required directory structure.
    We run the function in a temporary directory to avoid polluting the real repo.
    """
    # Save original cwd
    original_cwd = Path.cwd()
    
    # Change to temp directory to simulate project root
    os.chdir(tmp_path)
    
    # We need to patch the Path(__file__).resolve().parent.parent logic in setup_project
    # However, since we can't easily patch the module's internal __file__ resolution
    # without mocking, we will rely on the fact that the function uses relative paths
    # from the script's location.
    # To test this robustly, we should copy the script to the temp dir and run it there,
    # or mock the base_dir calculation.
    
    # Simpler approach for this specific task:
    # The task T001 is about creating the structure. The script `code/setup_project.py`
    # calculates `base_dir` as `Path(__file__).resolve().parent.parent`.
    # If we run this script from the project root, it should create the dirs.
    
    # Let's create a mock project structure in tmp_path
    # We copy the script to tmp_path/code/setup_project.py
    script_source = project_root / "code" / "setup_project.py"
    if not script_source.exists():
        pytest.skip("Setup script not found in project root")

    # Create the code dir in tmp
    (tmp_path / "code").mkdir(exist_ok=True)
    
    # Copy the script
    import shutil
    shutil.copy(script_source, tmp_path / "code" / "setup_project.py")
    
    # Run the script from tmp_path
    import subprocess
    result = subprocess.run(
        [sys.executable, str(tmp_path / "code" / "setup_project.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Verify directories exist
    required_dirs = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs",
    ]
    
    for rel_dir in required_dirs:
        dir_path = tmp_path / rel_dir
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."
    
    # Restore cwd
    os.chdir(original_cwd)
