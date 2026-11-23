import os
import subprocess
import tempfile
from pathlib import Path

def test_project_layout_creation():
    """
    Integration test that asserts the expected directories exist after
    executing the setup script.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        script_path = Path("code/setup_project_layout.py")
        
        # Run the script in the temporary directory context
        # We change CWD to tmpdir to simulate a fresh project init
        result = subprocess.run(
            ["python", str(script_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Setup script failed: {result.stderr}"
        
        # Verify directories
        expected_dirs = ["src", "tests", "data", "results", "contracts"]
        for dir_name in expected_dirs:
            dir_path = root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"Path {dir_name} exists but is not a directory"

if __name__ == "__main__":
    test_project_layout_creation()
    print("Test passed: Project layout directories exist.")