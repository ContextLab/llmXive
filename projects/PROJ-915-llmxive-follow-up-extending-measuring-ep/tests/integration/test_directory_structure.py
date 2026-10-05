import os
import sys
import subprocess
from pathlib import Path
import tempfile
import pytest

# Integration test to verify the full directory structure matches T001 requirements
# This test simulates the "Verification" step: Run `tree -L 2` and verify output

class TestDirectoryStructureIntegration:
    """Integration test for T001 directory structure verification."""

    def test_directory_tree_structure(self, tmp_path):
        """
        Verify that the directory structure matches the expected layout.
        
        Expected structure (depth 2):
        .
        ├── code/
        ├── data/
        │   ├── interim/
        │   ├── processed/
        │   ├── raw/
        │   └── results/
        ├── docs/
        ├── state/
        └── tests/
            ├── integration/
            └── unit/
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Import and run setup
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
            from setup_directories import setup_directories
            
            setup_directories()
            
            # Define expected paths relative to tmp_path
            expected_paths = [
                "code",
                "data",
                "data/raw",
                "data/processed",
                "data/interim",
                "data/results",
                "state",
                "tests",
                "tests/unit",
                "tests/integration",
                "docs",
            ]
            
            for path_str in expected_paths:
                full_path = tmp_path / path_str
                assert full_path.exists(), f"Missing expected path: {path_str}"
                assert full_path.is_dir(), f"Not a directory: {path_str}"
            
            # Verify tree output if 'tree' command is available
            try:
                result = subprocess.run(
                    ["tree", "-L", "2", str(tmp_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                tree_output = result.stdout
                
                # Basic sanity check: ensure key directories appear in output
                assert "code" in tree_output
                assert "data" in tree_output
                assert "tests" in tree_output
                assert "docs" in tree_output
                assert "state" in tree_output
                
            except FileNotFoundError:
                # 'tree' command not available, skip tree verification
                # The directory existence checks above are sufficient
                pytest.skip("tree command not available on this system")
                
        finally:
            os.chdir(original_cwd)
