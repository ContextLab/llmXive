"""Tests to verify project structure creation."""
import os
import pytest
from pathlib import Path
from code.setup_project_structure import create_project_structure
from config import get_config

def test_create_project_structure():
    """Test that all required directories are created."""
    config = get_config()
    base_path = Path(config.get('project_root', '.'))
    
    # Define expected directories
    expected_dirs = [
        base_path / 'data' / 'raw',
        base_path / 'data' / 'processed',
        base_path / 'data' / 'results',
        base_path / 'data' / 'external',
        base_path / 'code' / 'data',
        base_path / 'code' / 'models',
        base_path / 'code' / 'utils',
        base_path / 'tests' / 'unit',
        base_path / 'tests' / 'integration',
        base_path / 'tests' / 'contract',
    ]
    
    # Create structure
    created_count = create_project_structure()
    
    # Verify all directories exist
    for dir_path in expected_dirs:
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
    
    assert created_count == len(expected_dirs), f"Expected {len(expected_dirs)} directories, created {created_count}"