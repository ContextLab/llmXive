"""
Test suite for project structure creation.
Verifies that T001a requirements are met.
"""
import os
import pytest
from pathlib import Path
import shutil

# Import the function under test
# We assume the test runs from the repo root or code directory
# Adjusting import path to be relative to the test location
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_project_structure import create_structure

@pytest.fixture
def cleanup():
    """Clean up the created directories after test."""
    yield
    # Cleanup logic if needed (optional for CI)
    # base = Path("projects") / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    # if base.exists():
    #     shutil.rmtree(base)

def test_create_structure_creates_directories(cleanup):
    """Verify that all required directories are created."""
    base_dir = Path("projects") / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    
    # Ensure clean state
    if base_dir.exists():
        shutil.rmtree(base_dir)
    
    # Run creation
    created = create_structure()
    
    # Verify base exists
    assert base_dir.exists(), "Base project directory should exist"
    assert base_dir.is_dir(), "Base project directory should be a directory"
    
    # Verify subdirectories
    expected_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    
    for rel_dir in expected_dirs:
        full_path = base_dir / rel_dir
        assert full_path.exists(), f"Directory {rel_dir} should exist"
        assert full_path.is_dir(), f"{rel_dir} should be a directory"
    
    # Verify count
    assert len(created) == len(expected_dirs), f"Should create {len(expected_dirs)} directories"

def test_create_structure_idempotent(cleanup):
    """Verify that running create_structure twice does not fail."""
    base_dir = Path("projects") / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    
    # First run
    if base_dir.exists():
        shutil.rmtree(base_dir)
    create_structure()
    
    # Second run (should not raise)
    create_structure()
    
    assert base_dir.exists(), "Base directory should still exist"
    assert (base_dir / "code").exists(), "Code directory should still exist"