import os
import pytest
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil

def test_full_project_structure_creation():
    """
    Integration test: Run the setup script in a fresh temporary directory
    and verify the entire expected directory tree is created.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Locate the source script
        # Assuming the test is run from the project root, so we can find the script relative to __file__
        # But since we are in a temp dir, we need to find the script from the current working directory
        # or pass it as an argument. For this test, we assume the script is in the repo.
        # We'll find the project root by going up from the test file location.
        current_file = Path(__file__).resolve()
        # tests/integration -> tests -> root
        project_root = current_file.parent.parent.parent
        
        script_path = project_root / "code" / "setup_project.py"
        
        if not script_path.exists():
            pytest.fail(f"Setup script not found at {script_path}")
        
        # Copy the script to the temp directory's code folder
        # The script expects to be at code/setup_project.py relative to base_dir
        (tmp_path / "code").mkdir(parents=True, exist_ok=True)
        shutil.copy(script_path, tmp_path / "code" / "setup_project.py")
        
        # Execute the script
        result = subprocess.run(
            [sys.executable, str(tmp_path / "code" / "setup_project.py")],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        # Assert success
        assert result.returncode == 0, f"Setup failed: {result.stderr}"
        
        # Define expected structure
        expected_structure = [
            "code/utils",
            "data/raw",
            "data/processed",
            "data/results",
            "data/metadata",
            "tests/unit",
            "tests/integration",
            "docs",
        ]
        
        # Verify each directory
        for rel_path in expected_structure:
            full_path = tmp_path / rel_path
            assert full_path.exists(), f"Missing directory: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"
        
        # Optional: Verify the output message contains creation info
        assert "Created directory" in result.stdout or "Project structure setup complete" in result.stdout