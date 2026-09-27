import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import main

def test_setup_creates_directories_and_manifest():
    """
    Test that setup_project creates all required directories and generates the manifest.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the main function
            result = main()
            
            # Assert exit code is 0 (success)
            assert result == 0, "Main function should return 0 on success"

            # Define expected directories
            expected_dirs = [
                "code", "data", "tests", "state", "models",
                "data/raw", "data/processed", "reports"
            ]

            # Verify all directories exist
            for d in expected_dirs:
                full_path = Path(tmpdir) / d
                assert full_path.exists(), f"Directory {d} should exist"
                assert full_path.is_dir(), f"{d} should be a directory"

            # Verify manifest exists and has correct structure
            manifest_path = Path(tmpdir) / "state" / "structure_manifest.json"
            assert manifest_path.exists(), "Manifest file should exist"

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            assert "created_directories" in manifest
            assert "status" in manifest
            assert manifest["status"] == "success"
            
            # Verify all expected dirs are in the created list
            for d in expected_dirs:
                assert d in manifest["created_directories"], f"{d} should be in created_directories"

        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_setup_creates_directories_and_manifest()
    print("Test passed.")