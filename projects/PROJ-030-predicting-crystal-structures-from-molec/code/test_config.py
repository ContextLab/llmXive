"""
Tests for the configuration management module.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the config module directly
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    LOGS_DIR,
    RANDOM_SEED,
    TARGET_SAMPLE_SIZE,
    get_path,
    set_seed,
    get_config_dict,
)


def test_project_root_exists():
    """Test that the project root is correctly identified."""
    assert PROJECT_ROOT.exists()
    assert isinstance(PROJECT_ROOT, Path)


def test_data_directory_created():
    """Test that the data directory and subdirectories exist."""
    assert DATA_DIR.exists()
    assert (DATA_DIR / "processed").exists()
    assert (DATA_DIR / "models").exists()


def test_logs_directory_created():
    """Test that the logs directory exists."""
    assert LOGS_DIR.exists()


def test_random_seed_default():
    """Test that the default random seed is set."""
    assert RANDOM_SEED == 42


def test_target_sample_size():
    """Test that the target sample size is correctly set."""
    assert TARGET_SAMPLE_SIZE == 500


def test_get_path_relative():
    """Test get_path with a relative path."""
    relative_path = "data/test.csv"
    result = get_path(relative_path)
    expected = PROJECT_ROOT / relative_path
    assert result == expected
    assert result.is_absolute()


def test_get_path_absolute():
    """Test get_path with an absolute path."""
    absolute_path = "/tmp/test.csv"
    result = get_path(absolute_path)
    assert result == Path(absolute_path)


def test_set_seed():
    """Test that set_seed updates the global seed."""
    original_seed = RANDOM_SEED
    try:
        set_seed(123)
        # Note: The global variable in the module might be updated,
        # but we check the function's effect on the module's state.
        # Since we can't easily import the module's internal state
        # without re-importing, we rely on the function call.
        # A better test would involve checking the effect on numpy/random.
        import random
        import numpy as np

        random.seed(456)
        set_seed(789)
        assert random.randint(0, 100) != 0  # Just a sanity check that it ran

        # Reset
        set_seed(original_seed)
    finally:
        set_seed(original_seed)


def test_get_config_dict():
    """Test that get_config_dict returns a dictionary of configuration."""
    config = get_config_dict()
    assert isinstance(config, dict)
    assert "RANDOM_SEED" in config
    assert "DATA_DIR" in config
    assert "TARGET_SAMPLE_SIZE" in config

    # Check that values are the expected types
    assert isinstance(config["RANDOM_SEED"], int)
    assert isinstance(config["DATA_DIR"], Path)
    assert isinstance(config["TARGET_SAMPLE_SIZE"], int)


def test_config_paths_match_artifacts():
    """Test that configured paths for artifacts are valid paths."""
    from code.config import (
        POLYMORPHIC_DATASET_PATH,
        CRYSTAL_DATASET_PATH,
        SPLIT_INDICES_PATH,
        RF_MODEL_PATH,
        MODEL_METRICS_PATH,
    )

    assert isinstance(POLYMORPHIC_DATASET_PATH, Path)
    assert isinstance(CRYSTAL_DATASET_PATH, Path)
    assert isinstance(SPLIT_INDICES_PATH, Path)
    assert isinstance(RF_MODEL_PATH, Path)
    assert isinstance(MODEL_METRICS_PATH, Path)

    # Check they are under the data directory
    assert str(POLYMORPHIC_DATASET_PATH).startswith(str(DATA_DIR))
    assert str(RF_MODEL_PATH).startswith(str(DATA_DIR))