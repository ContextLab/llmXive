"""
Unit tests for the project structure setup script.
Verifies that all required directories are created.
"""
import os
import pytest
from pathlib import Path
from config import get_project_root, get_code_dir, get_tests_dir, get_specs_dir, get_data_dir

def test_create_directories():
    """Test that create_directories creates the expected structure."""
    from setup_project_structure import create_directories
    
    created = create_directories()
    
    # Verify key directories exist
    project_root = get_project_root()
    assert (project_root / "code").exists()
    assert (project_root / "data").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "specs").exists()
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "data" / "consent").exists()
    assert (project_root / "tests" / "unit").exists()
    assert (project_root / "tests" / "integration").exists()
    assert (project_root / "tests" / "contract").exists()

def test_directory_structure_integrity():
    """Test that the directory structure is logically consistent."""
    project_root = get_project_root()
    
    # Check that parent directories exist if children exist
    assert (project_root / "data").exists()
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "data" / "consent").exists()
    
    assert (project_root / "tests").exists()
    assert (project_root / "tests" / "unit").exists()
    assert (project_root / "tests" / "integration").exists()
    assert (project_root / "tests" / "contract").exists()

def test_specs_directory_structure():
    """Test that the specs directory structure is correct."""
    project_root = get_project_root()
    specs_dir = project_root / "specs"
    feature_dir = specs_dir / "001-text-tone-emotional-support"
    contracts_dir = feature_dir / "contracts"
    
    assert specs_dir.exists()
    assert feature_dir.exists()
    assert contracts_dir.exists()