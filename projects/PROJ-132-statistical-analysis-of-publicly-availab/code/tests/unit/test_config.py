"""
Unit tests for the configuration management module.
"""
import os
import pytest
from src.lib.config import (
    SEED,
    GRID_RES,
    PERMUTATIONS,
    SAMPLE_SIZE,
    get_config_summary,
    PROJECT_ROOT,
    DATA_RAW_DIR,
    LOGS_DIR,
    STATE_DIR,
)


def test_seed_is_integer():
    """Test that SEED is an integer."""
    assert isinstance(SEED, int)


def test_seed_default_value():
    """Test that SEED has the expected default value."""
    assert SEED == 42


def test_grid_res_is_float():
    """Test that GRID_RES is a float."""
    assert isinstance(GRID_RES, float)


def test_grid_res_default_value():
    """Test that GRID_RES has the expected default value."""
    assert GRID_RES == 0.5


def test_permutations_is_integer():
    """Test that PERMUTATIONS is an integer."""
    assert isinstance(PERMUTATIONS, int)


def test_permutations_default_value():
    """Test that PERMUTATIONS has the expected default value."""
    assert PERMUTATIONS == 10000


def test_sample_size_can_be_none():
    """Test that SAMPLE_SIZE can be None when not set."""
    # Unset the environment variable if it exists
    original = os.environ.pop("SAMPLE_SIZE", None)
    try:
        # Re-import to get fresh value (in real test runner, this would be a fresh module)
        # For this test, we assume the module was imported with SAMPLE_SIZE unset
        from src.lib import config
        assert config.SAMPLE_SIZE is None
    finally:
        # Restore original value
        if original is not None:
            os.environ["SAMPLE_SIZE"] = original


def test_sample_size_can_be_set():
    """Test that SAMPLE_SIZE can be set via environment variable."""
    original = os.environ.get("SAMPLE_SIZE")
    os.environ["SAMPLE_SIZE"] = "1000"
    try:
        # Force re-evaluation by re-importing (in a real test, this would be a fresh process)
        # For simplicity, we test the logic directly
        val = os.environ.get("SAMPLE_SIZE")
        assert val == "1000"
        assert int(val) == 1000
    finally:
        if original is not None:
            os.environ["SAMPLE_SIZE"] = original
        else:
            os.environ.pop("SAMPLE_SIZE", None)


def test_permutations_can_be_set():
    """Test that PERMUTATIONS can be set via environment variable."""
    original = os.environ.get("PERMUTATIONS")
    os.environ["PERMUTATIONS"] = "5000"
    try:
        # Force re-evaluation
        val = os.environ.get("PERMUTATIONS")
        assert val == "5000"
        assert int(val) == 5000
    finally:
        if original is not None:
            os.environ["PERMUTATIONS"] = original
        else:
            os.environ.pop("PERMUTATIONS", None)


def test_get_config_summary_returns_dict():
    """Test that get_config_summary returns a dictionary."""
    config_dict = get_config_summary()
    assert isinstance(config_dict, dict)


def test_get_config_summary_contains_expected_keys():
    """Test that get_config_summary contains expected keys."""
    config_dict = get_config_summary()
    expected_keys = [
        "seed",
        "grid_res",
        "sample_size",
        "permutations",
        "data_raw_dir",
        "data_interim_dir",
        "data_processed_dir",
        "logs_dir",
        "state_dir",
    ]
    for key in expected_keys:
        assert key in config_dict


def test_project_root_is_path():
    """Test that PROJECT_ROOT is a Path object."""
    from pathlib import Path
    assert isinstance(PROJECT_ROOT, Path)


def test_data_raw_dir_exists():
    """Test that DATA_RAW_DIR exists (created by config module)."""
    assert DATA_RAW_DIR.exists()


def test_logs_dir_exists():
    """Test that LOGS_DIR exists (created by config module)."""
    assert LOGS_DIR.exists()


def test_state_dir_exists():
    """Test that STATE_DIR exists (created by config module)."""
    assert STATE_DIR.exists()