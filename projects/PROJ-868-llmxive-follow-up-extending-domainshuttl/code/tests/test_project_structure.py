"""
Test to verify that the project directory structure has been created correctly.
This test satisfies the evidence requirement for T001.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "src/config",
    "src/data",
    "src/models",
    "src/analysis",
    "src/utils",
    "tests",
    "data/raw",
    "data/processed",
    "data/results",
    "specs/001-gene-regulation/contracts",
    "docs"
]

class TestProjectStructure:
    @pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
    def test_directory_exists(self, dir_path):
        """Verify each required directory exists."""
        path = Path(dir_path)
        assert path.exists(), f"Directory {dir_path} does not exist"
        assert path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_full_structure_snapshot(self):
        """
        Generate a snapshot of the current structure to satisfy the 'directory listing'
        evidence requirement mentioned in the rejection of T001.
        """
        missing = []
        for dir_path in REQUIRED_DIRS:
            if not Path(dir_path).exists():
                missing.append(dir_path)
        
        assert not missing, f"Missing directories: {missing}"
        
        # Print a simple tree-like representation for verification
        print("\n--- Project Structure Snapshot ---")
        for dir_path in REQUIRED_DIRS:
            p = Path(dir_path)
            # Check for subdirectories if any (e.g. src/config)
            print(f"  {dir_path}/")
            if p.is_dir():
                children = list(p.iterdir())
                if not children:
                    print(f"    (empty)")
                else:
                    for child in children:
                        print(f"    - {child.name}")
        print("--- End Snapshot ---")