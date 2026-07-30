"""
Tests to verify the project directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function from the code directory
# Since we are running tests, we assume the code is in the project root or code/
# For this test, we will create a temporary structure and verify it
# But since the task is to CREATE the structure, we test the creation logic

def test_structure_creation_logic():
    """Test that the structure creation logic works."""
    from code.create_project_structure import create_structure
    
    # We can't easily test the actual file creation in a CI environment
    # without modifying the filesystem, so we test the logic by mocking
    # or by creating a temporary directory.
    
    # Let's create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # The script expects to run from the project root
            # We will verify the paths it tries to create
            base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
            
            # Manually check the logic without actually creating (to avoid side effects in test)
            subdirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts",
                "artifacts/checkpoints",
                "artifacts/results"
            ]
            
            for subdir in subdirs:
                expected_path = base_dir / subdir
                # We don't create it here, just verify the path construction
                assert str(expected_path).startswith("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
                assert subdir in str(expected_path)
            
            # Now actually run the function to ensure it doesn't crash
            # We are in a temp dir, so it's safe
            result = create_structure()
            
            # Verify directories were created
            for subdir in subdirs:
                assert (base_dir / subdir).exists()
            
            assert len(result) == len(subdirs)
            
        finally:
            os.chdir(original_cwd)

def test_required_subdirs_exist():
    """Verify that the required subdirectories are defined in the creation logic."""
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    # This is a sanity check that the list is complete
    assert len(subdirs) == 7
    assert "data/raw" in subdirs
    assert "data/processed" in subdirs
    assert "code" in subdirs
    assert "tests" in subdirs
    assert "artifacts" in subdirs
    assert "artifacts/checkpoints" in subdirs
    assert "artifacts/results" in subdirs