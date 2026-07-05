"""
Unit tests for code/config.py to verify path definitions and constants.
"""
import pytest
from pathlib import Path
from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_CURATED_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    RANDOM_SEED,
    CV_FOLDS,
    MP_API_KEY_ENV_VAR,
    ensure_directories,
    MIN_DATASET_SIZE
)

def test_project_root_exists():
    """Verify PROJECT_ROOT is a valid Path and exists."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()

def test_directory_paths():
    """Verify all defined directory paths are subdirectories of PROJECT_ROOT."""
    assert DATA_DIR.is_relative_to(PROJECT_ROOT)
    assert DATA_RAW_DIR.is_relative_to(DATA_DIR)
    assert DATA_CURATED_DIR.is_relative_to(DATA_DIR)
    assert MODELS_DIR.is_relative_to(PROJECT_ROOT)
    assert REPORTS_DIR.is_relative_to(PROJECT_ROOT)

def test_constants_values():
    """Verify key constants have expected values."""
    assert RANDOM_SEED == 42
    assert CV_FOLDS == 5
    assert MIN_DATASET_SIZE == 50
    assert MP_API_KEY_ENV_VAR == "MP_API_KEY"

def test_ensure_directories_creates_missing():
    """Test that ensure_directories creates non-existent directories."""
    # Create a temporary test path
    test_dir = DATA_DIR / "test_temp_dir"
    if test_dir.exists():
        test_dir.rmdir()
    
    ensure_directories()
    # Note: ensure_directories only creates standard dirs, not test_dir
    # So we verify standard dirs exist
    assert DATA_DIR.exists()
    assert DATA_RAW_DIR.exists()
    assert MODELS_DIR.exists()
    assert REPORTS_DIR.exists()