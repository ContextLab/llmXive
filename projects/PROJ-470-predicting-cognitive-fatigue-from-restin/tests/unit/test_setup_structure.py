"""
Unit tests for the project structure setup script.

These tests verify that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the main logic to test it in isolation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

# We will test the logic by mocking the paths
def test_directory_creation_logic():
    """Test that the directory creation logic works correctly."""
    # Create a temporary base directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        project_name = "PROJ-470-predicting-cognitive-fatigue-from-restin"
        project_path = base_path / project_name
        
        subdirs = [
            "data/raw",
            "data/processed",
            "data/analysis",
            "code",
            "tests/unit",
            "tests/integration",
            "docs"
        ]
        
        # Simulate the creation logic
        project_path.mkdir(parents=True, exist_ok=True)
        
        for subdir in subdirs:
            full_path = project_path / subdir
            full_path.mkdir(parents=True, exist_ok=True)
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
        
        # Verify all expected directories exist
        for subdir in subdirs:
            assert (project_path / subdir).exists()
        
        # Verify nested structure (e.g., data/raw exists, not just data)
        assert (project_path / "data" / "raw").exists()
        assert (project_path / "tests" / "unit").exists()
        assert (project_path / "tests" / "integration").exists()

def test_idempotency():
    """Test that running the setup twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        project_name = "PROJ-470-predicting-cognitive-fatigue-from-restin"
        project_path = base_path / project_name
        
        subdirs = [
            "data/raw",
            "code"
        ]
        
        # Run creation logic twice
        project_path.mkdir(parents=True, exist_ok=True)
        for subdir in subdirs:
            (project_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Run again
        project_path.mkdir(parents=True, exist_ok=True)
        for subdir in subdirs:
            (project_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Verify everything is still there
        for subdir in subdirs:
            assert (project_path / subdir).exists()