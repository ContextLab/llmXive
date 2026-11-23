"""
Tests for the data directory setup script.
Verifies that the required directories and .gitkeep files are created.
"""
import os
import pytest
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir
from setup_data_dirs import create_directories


def test_create_directories_creates_folders():
    """Test that create_directories creates the required folders."""
    # Run the setup
    create_directories()
    
    # Verify directories exist
    assert get_raw_data_dir().exists(), f"Directory {get_raw_data_dir()} does not exist"
    assert get_processed_data_dir().exists(), f"Directory {get_processed_data_dir()} does not exist"
    assert get_consent_dir().exists(), f"Directory {get_consent_dir()} does not exist"
    
    # Verify they are directories
    assert get_raw_data_dir().is_dir(), f"{get_raw_data_dir()} is not a directory"
    assert get_processed_data_dir().is_dir(), f"{get_processed_data_dir()} is not a directory"
    assert get_consent_dir().is_dir(), f"{get_consent_dir()} is not a directory"


def test_gitkeep_files_exist():
    """Test that .gitkeep files are created in each directory."""
    create_directories()
    
    # Check for .gitkeep files
    raw_gitkeep = get_raw_data_dir() / ".gitkeep"
    processed_gitkeep = get_processed_data_dir() / ".gitkeep"
    consent_gitkeep = get_consent_dir() / ".gitkeep"
    
    assert raw_gitkeep.exists(), f".gitkeep missing in {get_raw_data_dir()}"
    assert processed_gitkeep.exists(), f".gitkeep missing in {get_processed_data_dir()}"
    assert consent_gitkeep.exists(), f".gitkeep missing in {get_consent_dir()}"
    
    # Verify they are files
    assert raw_gitkeep.is_file(), f"{raw_gitkeep} is not a file"
    assert processed_gitkeep.is_file(), f"{processed_gitkeep} is not a file"
    assert consent_gitkeep.is_file(), f"{consent_gitkeep} is not a file"


def test_directory_structure_matches_spec():
    """Test that the directory structure matches the project specification."""
    create_directories()
    
    # Verify the structure under data/
    data_dir = get_project_root() / "data"
    assert data_dir.exists(), "data/ directory does not exist"
    
    # Check subdirectories
    assert (data_dir / "raw").exists(), "data/raw/ missing"
    assert (data_dir / "processed").exists(), "data/processed/ missing"
    assert (data_dir / "consent").exists(), "data/consent/ missing"
    
    # Verify .gitkeep files
    assert (data_dir / "raw" / ".gitkeep").exists(), "data/raw/.gitkeep missing"
    assert (data_dir / "processed" / ".gitkeep").exists(), "data/processed/.gitkeep missing"
    assert (data_dir / "consent" / ".gitkeep").exists(), "data/consent/.gitkeep missing"