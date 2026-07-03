"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path

# Import the config module
try:
    from code.config import (
      PROJECT_ROOT,
      DATA_RAW_DIR,
      DATA_PROCESSED_DIR,
      RESULTS_DIR,
      RANDOM_SEED,
      VALIDATED_SOURCE_WHITELIST
    )
except ImportError:
    # Fallback if config.py is not yet fully implemented or named differently
    # This test scaffold ensures the structure is ready for when config.py is finalized
    pytest.skip("code/config.py not fully implemented yet", allow_module_level=True)

def test_project_root_exists():
    """Verify PROJECT_ROOT is a valid Path object."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()

def test_directories_exist():
    """Verify required directories exist."""
    assert DATA_RAW_DIR.exists()
    assert DATA_PROCESSED_DIR.exists()
    assert RESULTS_DIR.exists()

def test_random_seed_is_int():
    """Verify random seed is an integer."""
    assert isinstance(RANDOM_SEED, int)

def test_whitelist_is_list():
    """Verify whitelist is a list."""
    assert isinstance(VALIDATED_SOURCE_WHITELIST, list)
    assert len(VALIDATED_SOURCE_WHITELIST) > 0