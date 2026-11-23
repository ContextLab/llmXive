"""
Unit tests for data directory creation and structure verification.
"""
import os
import pytest
from pathlib import Path
from scripts.setup_data_dirs import create_directories, print_tree

def test_create_directories_structure():
    """Test that the required data directories are created."""
    # Get the project root relative to this test file
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent.parent
    
    # Run the creation logic
    created = create_directories()
    
    # Verify each expected directory exists
    expected_dirs = [
        "data/raw",
        "data/intermediate",
        "data/simulator_validation"
    ]
    
    for rel_path in expected_dirs:
        full_path = project_root / rel_path
        assert full_path.exists(), f"Directory {rel_path} was not created"
        assert full_path.is_dir(), f"{rel_path} exists but is not a directory"
    
    # Verify the returned list matches expectations
    assert len(created) == 3
    for rel_path in expected_dirs:
        assert rel_path in created, f"{rel_path} not in created list"

def test_data_dirs_persist():
    """Test that directories persist after creation."""
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent.parent
    
    # Ensure directories exist first
    create_directories()
    
    # Re-check existence
    raw_dir = project_root / "data" / "raw"
    intermediate_dir = project_root / "data" / "intermediate"
    validation_dir = project_root / "data" / "simulator_validation"
    
    assert raw_dir.exists()
    assert intermediate_dir.exists()
    assert validation_dir.exists()

def test_idempotent_creation():
    """Test that running create_directories multiple times doesn't fail."""
    # Run twice
    create_directories()
    create_directories()
    
    # Should still exist
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent.parent
    
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "intermediate").exists()
    assert (project_root / "data" / "simulator_validation").exists()