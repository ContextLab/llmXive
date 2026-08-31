"""
Contract tests for verifying the data directory structure.
Ensures that data/raw/, data/processed/, and data/consent/ exist
and contain .gitkeep files.
"""
import os
import pytest
from pathlib import Path
from config import get_raw_data_dir, get_processed_data_dir, get_consent_dir


def test_raw_data_directory_exists():
    """Verify that data/raw/ directory exists."""
    raw_dir = get_raw_data_dir()
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"


def test_processed_data_directory_exists():
    """Verify that data/processed/ directory exists."""
    processed_dir = get_processed_data_dir()
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"


def test_consent_data_directory_exists():
    """Verify that data/consent/ directory exists."""
    consent_dir = get_consent_dir()
    assert consent_dir.exists(), f"Directory {consent_dir} does not exist"
    assert consent_dir.is_dir(), f"{consent_dir} is not a directory"


def test_raw_data_has_gitkeep():
    """Verify that data/raw/ contains a .gitkeep file."""
    raw_dir = get_raw_data_dir()
    gitkeep_path = raw_dir / ".gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file not found in {raw_dir}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"


def test_processed_data_has_gitkeep():
    """Verify that data/processed/ contains a .gitkeep file."""
    processed_dir = get_processed_data_dir()
    gitkeep_path = processed_dir / ".gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file not found in {processed_dir}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"


def test_consent_data_has_gitkeep():
    """Verify that data/consent/ contains a .gitkeep file."""
    consent_dir = get_consent_dir()
    gitkeep_path = consent_dir / ".gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file not found in {consent_dir}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"


def test_all_required_directories_exist():
    """Verify that all required data directories exist."""
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]
    
    for dir_path in directories:
        assert dir_path.exists(), f"Required directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"


def test_all_directories_have_gitkeep():
    """Verify that all required data directories have .gitkeep files."""
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]
    
    for dir_path in directories:
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file not found in {dir_path}"
        assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"