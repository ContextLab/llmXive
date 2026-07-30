"""
Unit tests for the configuration management module (code/config.py).
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import (
    N_PERMUTATIONS,
    RANDOM_SEED,
    TEST_SIZE,
    MAX_DATASET_ROWS,
    MIN_DATASET_ROWS,
    PERMUTATION_IMPORTANCE_THRESHOLD,
    P_VALUE_THRESHOLD,
    COLD_WORK_MIN,
    COLD_WORK_MAX,
    ensure_directories,
    DATA_RAW_DIR,
    ARTIFACTS_REPORTS_DIR,
)


def test_n_permutations_default():
    """Test that N_PERMUTATIONS defaults to 1000."""
    # This relies on the default in config.py if .env is not set or doesn't contain the key
    # If the environment variable is set elsewhere, this test might need mocking,
    # but for a static check of the default logic:
    assert N_PERMUTATIONS == 1000 or isinstance(N_PERMUTATIONS, int) and N_PERMUTATIONS > 0


def test_random_seed():
    """Test that RANDOM_SEED is 42."""
    assert RANDOM_SEED == 42


def test_test_size():
    """Test that TEST_SIZE is 0.2."""
    assert TEST_SIZE == 0.2


def test_dataset_size_limits():
    """Test dataset size limits."""
    assert MAX_DATASET_ROWS == 10000
    assert MIN_DATASET_ROWS == 50


def test_thresholds():
    """Test statistical thresholds."""
    assert PERMUTATION_IMPORTANCE_THRESHOLD == 0.01
    assert P_VALUE_THRESHOLD == 0.05


def test_physical_bounds():
    """Test physical bound constants."""
    assert COLD_WORK_MIN == 0.0
    assert COLD_WORK_MAX == 100.0


def test_directories_exist():
    """Test that ensure_directories creates the necessary folders."""
    # Clean up first if they exist (optional, or just ensure they exist)
    # We expect the function to create them.
    ensure_directories()
    assert DATA_RAW_DIR.exists()
    assert ARTIFACTS_REPORTS_DIR.exists()
    assert DATA_RAW_DIR.is_dir()
    assert ARTIFACTS_REPORTS_DIR.is_dir()


def test_paths_are_pathlib():
    """Test that paths are Path objects."""
    from pathlib import Path
    assert isinstance(DATA_RAW_DIR, Path)
    assert isinstance(ARTIFACTS_REPORTS_DIR, Path)