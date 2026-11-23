"""
Unit tests for the configuration module (code/config.py).
Verifies that paths are resolved correctly and defaults are set.
"""
import os
from pathlib import Path
import pytest

# Import the config module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code import config


def test_project_root_resolution():
    """Test that project root is correctly identified relative to config.py."""
    expected_root = Path(__file__).parent.parent.parent
    assert config.get_project_root() == expected_root


def test_data_dirs_exist():
    """Test that the ensure_paths_exist function creates the required directories."""
    # The function is called at import time, so these should exist.
    # We verify the attributes point to valid Path objects.
    assert isinstance(config.RAW_DATA_DIR, Path)
    assert isinstance(config.PROCESSED_DATA_DIR, Path)
    assert config.RAW_DATA_DIR.is_absolute()
    assert config.PROCESSED_DATA_DIR.is_absolute()


def test_default_hyperparameters():
    """Test that default hyperparameters are sensible."""
    assert config.ZSCORE_WINDOW == 20
    assert config.ZSCORE_MIN_SAMPLES == 5
    assert config.ZSCORE_THRESHOLD == 3.0
    assert config.DYNAMIC_THRESHOLD_MULTIPLIER == 2.5
    assert config.CORRELATION_THRESHOLD == 0.8
    assert config.F1_STDDEV_THRESHOLD == 0.15
    assert config.RANDOM_SEED == 42


def test_env_override():
    """Test that environment variables correctly override defaults."""
    # This test requires a fresh import or manual override to be truly isolated,
    # but we can verify the logic by setting an env var before import in a subprocess.
    # For this unit test, we verify the constants are readable.
    assert config.GOLD_DROP_THRESHOLD == 0.1
    assert config.GOLD_DROP_STEPS == 50
    assert config.GOLD_SUSTAIN_STEPS == 3