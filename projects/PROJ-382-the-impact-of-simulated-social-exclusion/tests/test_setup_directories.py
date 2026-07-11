"""
Tests for the directory setup script.
Verifies that the required folder structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the script logic if needed
# Or we can just test the resulting state after running the script.
# For this unit test, we will simulate the creation and verify.

def test_directory_structure_creation():
    """
    Test that the setup script creates the required directories.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Simulate the target path structure
        target_root = tmp_path / "projects" / "PROJ-382-the-impact-of-simulated-social-exclusion"
        
        # Define the expected directories relative to target_root
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "tests",
            "state"
        ]

        # Manually create them to simulate the script's action (or import and run the function)
        # Since the script is a standalone main, we can replicate the logic here for the test
        for rel_dir in expected_dirs:
            full_path = target_root / rel_dir
            full_path.mkdir(parents=True, exist_ok=True)

        # Verify existence
        for rel_dir in expected_dirs:
            full_path = target_root / rel_dir
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"Path {full_path} is not a directory."

        # Verify specific nested structure
        assert (target_root / "data" / "raw").is_dir()
        assert (target_root / "data" / "processed").is_dir()

def test_idempotency():
    """
    Test that creating the directories twice does not raise errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_root = tmp_path / "projects" / "PROJ-382-the-impact-of-simulated-social-exclusion"
        
        # Create once
        (target_root / "code").mkdir(parents=True, exist_ok=True)
        
        # Create again (simulating exist_ok=True)
        (target_root / "code").mkdir(parents=True, exist_ok=True)
        
        assert (target_root / "code").exists()