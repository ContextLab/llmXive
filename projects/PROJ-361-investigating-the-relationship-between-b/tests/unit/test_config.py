"""
Unit tests for code/utils/config.py
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# We need to mock the path resolution if we want to test in a temp directory,
# but for now we test the constants and functions that don't rely on side effects
# or we test the side effects in a controlled environment.

# To test path resolution without affecting the real project structure,
# we will test the logic of the helper functions.

def test_directory_constants_are_absolute():
    """Ensure all directory constants are absolute paths."""
    from code.utils.config import (
        DATA_DIR, DATA_RAW, DATA_PROCESSED, DATA_BEHAVIORAL,
        FIGURES_DIR, CODE_DIR, TESTS_DIR, SPECS_DIR, DB_PATH
    )
    
    assert DATA_DIR.is_absolute()
    assert DATA_RAW.is_absolute()
    assert DATA_PROCESSED.is_absolute()
    assert DATA_BEHAVIORAL.is_absolute()
    assert FIGURES_DIR.is_absolute()
    assert CODE_DIR.is_absolute()
    assert TESTS_DIR.is_absolute()
    assert SPECS_DIR.is_absolute()
    assert DB_PATH.is_absolute()

def test_get_raw_path():
    """Test the construction of raw data paths."""
    from code.utils.config import get_raw_path
    
    result = get_raw_path("sub-01")
    # We expect it to end with sub-01
    assert result.name == "sub-01"
    assert result.is_absolute()

def test_get_processed_path():
    """Test the construction of processed data paths."""
    from code.utils.config import get_processed_path
    
    result = get_processed_path("test_file.csv")
    assert result.name == "test_file.csv"
    assert result.is_absolute()

def test_ensure_dirs_exist_creates_structure(tmp_path, monkeypatch):
    """
    Test that ensure_dirs_exist creates directories.
    We monkeypatch the global constants to point to a temp directory.
    """
    from code.utils import config
    
    # Create a temporary project root
    temp_root = tmp_path / "project"
    temp_root.mkdir()
    
    # Temporarily override the module's global constants
    original_data_dir = config.DATA_DIR
    original_raw_dir = config.DATA_RAW
    original_processed_dir = config.DATA_PROCESSED
    original_behavioral_dir = config.DATA_BEHAVIORAL
    original_figures_dir = config.FIGURES_DIR
    original_code_dir = config.CODE_DIR
    original_tests_dir = config.TESTS_DIR
    original_specs_dir = config.SPECS_DIR
    original_data_root = config.DATA_DIR.parent # The data dir itself
    
    # Set up new paths in temp directory
    new_data_dir = temp_root / "data"
    new_raw_dir = new_data_dir / "raw"
    new_processed_dir = new_data_dir / "processed"
    new_behavioral_dir = new_data_dir / "behavioral"
    new_figures_dir = temp_root / "figures"
    new_code_dir = temp_root / "code"
    new_tests_dir = temp_root / "tests"
    new_specs_dir = temp_root / "specs"
    
    monkeypatch.setattr(config, 'DATA_DIR', new_data_dir)
    monkeypatch.setattr(config, 'DATA_RAW', new_raw_dir)
    monkeypatch.setattr(config, 'DATA_PROCESSED', new_processed_dir)
    monkeypatch.setattr(config, 'DATA_BEHAVIORAL', new_behavioral_dir)
    monkeypatch.setattr(config, 'FIGURES_DIR', new_figures_dir)
    monkeypatch.setattr(config, 'CODE_DIR', new_code_dir)
    monkeypatch.setattr(config, 'TESTS_DIR', new_tests_dir)
    monkeypatch.setattr(config, 'SPECS_DIR', new_specs_dir)
    
    # Call the function
    config.ensure_dirs_exist()
    
    # Verify directories were created
    assert new_data_dir.exists()
    assert new_raw_dir.exists()
    assert new_processed_dir.exists()
    assert new_behavioral_dir.exists()
    assert new_figures_dir.exists()
    assert new_code_dir.exists()
    assert new_tests_dir.exists()
    assert new_specs_dir.exists()
    
    # Restore original values (though module reload would be safer in real tests)
    config.DATA_DIR = original_data_dir
    config.DATA_RAW = original_raw_dir
    config.DATA_PROCESSED = original_processed_dir
    config.DATA_BEHAVIORAL = original_behavioral_dir
    config.FIGURES_DIR = original_figures_dir
    config.CODE_DIR = original_code_dir
    config.TESTS_DIR = original_tests_dir
    config.SPECS_DIR = original_specs_dir

def test_motion_threshold_constant():
    """Verify the motion threshold constant is set correctly."""
    from code.utils.config import MOTION_THRESHOLD_MM
    assert MOTION_THRESHOLD_MM == 0.5

def test_schaefer_rois_constant():
    """Verify the Schaefer ROI count constant."""
    from code.utils.config import SCHAEFER_N_ROIS
    assert SCHAEFER_N_ROIS == 200

def test_db_path_configuration():
    """Verify the database path is correctly constructed."""
    from code.utils.config import DB_PATH
    assert DB_PATH.name == "metadata_registry.db"
    assert "data" in str(DB_PATH)

def test_validate_openneuro_credentials_missing(monkeypatch):
    """Test validation when API key is missing."""
    monkeypatch.delenv("OPENNEURO_API_KEY", raising=False)
    from code.utils.config import validate_openneuro_credentials
    assert validate_openneuro_credentials() is False

def test_validate_openneuro_credentials_present(monkeypatch):
    """Test validation when API key is present."""
    monkeypatch.setenv("OPENNEURO_API_KEY", "fake_key_123")
    from code.utils.config import validate_openneuro_credentials
    assert validate_openneuro_credentials() is True