"""
Basic sanity tests for the project configuration.
Ensures that config.py can be imported and provides expected attributes.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from config import (
    PROJECT_ROOT,
    DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    CODE_DIR,
    FIGURES_DIR,
    SEED,
    DEFAULT_HYPERPARAMETERS
)

class TestConfig:
    """Tests for project configuration constants."""

    def test_project_root_exists(self):
        """Verify PROJECT_ROOT is a valid path."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_data_directories_exist(self):
        """Verify data directories are configured correctly."""
        assert isinstance(DATA_DIR, Path)
        assert DATA_DIR == PROJECT_ROOT / "data"
        
        assert isinstance(PROCESSED_DATA_DIR, Path)
        assert PROCESSED_DATA_DIR == DATA_DIR / "processed"
        
        assert isinstance(RAW_DATA_DIR, Path)
        assert RAW_DATA_DIR == DATA_DIR / "raw"

    def test_code_directory(self):
        """Verify code directory is configured correctly."""
        assert isinstance(CODE_DIR, Path)
        assert CODE_DIR == PROJECT_ROOT / "code"

    def test_seed_is_integer(self):
        """Verify random seed is an integer."""
        assert isinstance(SEED, int)
        assert SEED > 0

    def test_hyperparameters_structure(self):
        """Verify default hyperparameters dictionary has expected keys."""
        assert isinstance(DEFAULT_HYPERPARAMETERS, dict)
        # Check for common keys expected in the project based on T007
        expected_keys = ['regularization_strength', 'tree_depth', 'n_estimators']
        for key in expected_keys:
            assert key in DEFAULT_HYPERPARAMETERS, f"Missing key: {key}"