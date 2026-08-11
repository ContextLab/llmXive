"""
Integration test to verify the directory structure is correctly set up.
This test runs the setup script and verifies the file system state.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

def test_full_directory_setup():
    """
    Run the setup_dirs script in a temporary environment and verify
    that all required directories are created.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock project structure in the temp dir
        # We need to place setup_dirs.py in a 'code' folder relative to tmp_dir
        # to mimic the real project structure, or adjust the script logic.
        # However, the script uses __file__ to find the root.
        # Let's create the 'code' dir and move the script there.
        
        code_dir = Path(tmp_dir) / "code"
        code_dir.mkdir()
        
        # Copy the script content into the temp location
        script_content = Path("code/setup_dirs.py").read_text()
        script_path = code_dir / "setup_dirs.py"
        script_path.write_text(script_content)

        # Run the script
        # Note: In a real CI/CD, we would run `python code/setup_dirs.py` from root.
        # Here we run it from the code dir, but the script resolves parent.
        result = subprocess.run(
            ["python", str(script_path)],
            cwd=str(code_dir),
            capture_output=True,
            text=True
        )

        # Check execution success
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Verify directories exist relative to tmp_dir (which is the root)
        root = Path(tmp_dir)
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/models",
            "tests/unit",
            "tests/integration",
            "specs"
        ]

        for d in expected_dirs:
            assert (root / d).exists(), f"Required directory {d} was not created"
        
        # Verify nested structures
        assert (root / "data" / "raw").exists()
        assert (root / "tests" / "unit").exists()