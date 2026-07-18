"""
Tests for the centralized configuration module.
Verifies that paths are resolved correctly and constants are valid.
"""
import pytest
import os
from pathlib import Path
from code.config import (
    PROJECT_ROOT, 
    DATA_DIR, 
    DATA_PROCESSED_DIR, 
    ensure_directories,
    get_config,
    MIN_SAMPLE_SIZE,
    CORRELATION_THRESHOLD
)

def test_project_root_exists():
    """Verify that the project root is a valid directory."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()
    # Check for a marker file or directory that typically exists in the repo
    assert (PROJECT_ROOT / "tasks.md").exists() or (PROJECT_ROOT / "README.md").exists()

def test_data_directories_exist():
    """Verify that data directories are defined and can be created."""
    assert isinstance(DATA_DIR, Path)
    assert isinstance(DATA_PROCESSED_DIR, Path)
    
    # Ensure they exist (side effect of test)
    ensure_directories()
    
    assert DATA_DIR.exists()
    assert DATA_PROCESSED_DIR.exists()

def test_config_constants():
    """Verify that key configuration constants have expected types and values."""
    assert isinstance(MIN_SAMPLE_SIZE, int)
    assert MIN_SAMPLE_SIZE > 0
    
    assert isinstance(CORRELATION_THRESHOLD, float)
    assert 0.0 <= CORRELATION_THRESHOLD <= 1.0

def test_get_config_returns_dict():
    """Verify that get_config returns a dictionary with expected keys."""
    config = get_config()
    assert isinstance(config, dict)
    assert "project_root" in config
    assert "data_dir" in config
    assert "huggingface_dataset" in config
    assert "min_sample_size" in config
    assert config["min_sample_size"] == MIN_SAMPLE_SIZE

def test_path_resolution_relative_to_code():
    """
    Verify that paths are resolved relative to the code/ directory,
    not the current working directory.
    """
    # The config file is in code/config.py
    # PROJECT_ROOT should be parent of code/
    expected_code_dir = PROJECT_ROOT / "code"
    assert expected_code_dir.exists()
    assert (expected_code_dir / "config.py").exists()