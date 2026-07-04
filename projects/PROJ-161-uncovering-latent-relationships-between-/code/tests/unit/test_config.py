"""
Unit tests for src/config.py.
Verifies seed pinning, configuration loading, and constant values.
"""
import os
import sys
import random
import numpy as np
import pytest

# Adjust path to include the code/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import (
    RANDOM_SEED,
    PERMUTATION_ITERATIONS,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    FIGURES_DIR,
    LOGS_DIR,
    set_seeds,
    get_config_summary
)


class TestConfigConstants:
    """Test that configuration constants are defined correctly."""

    def test_random_seed_is_integer(self):
        """Verify RANDOM_SEED is an integer."""
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_permutation_iterations_is_correct(self):
        """Verify PERMUTATION_ITERATIONS matches the requirement (1000)."""
        assert PERMUTATION_ITERATIONS == 1000

    def test_directory_paths_are_strings(self):
        """Verify all directory path constants are non-empty strings."""
        assert isinstance(RAW_DATA_DIR, str) and len(RAW_DATA_DIR) > 0
        assert isinstance(PROCESSED_DATA_DIR, str) and len(PROCESSED_DATA_DIR) > 0
        assert isinstance(FIGURES_DIR, str) and len(FIGURES_DIR) > 0
        assert isinstance(LOGS_DIR, str) and len(LOGS_DIR) > 0

    def test_paths_are_relative_to_root(self):
        """Verify paths start with 'data/' or 'figures/' or 'logs/'.
        
        Ensures we are not writing to absolute paths or outside the project tree.
        """
        assert RAW_DATA_DIR.startswith('data/')
        assert PROCESSED_DATA_DIR.startswith('data/')
        assert FIGURES_DIR.startswith('figures/')
        assert LOGS_DIR.startswith('logs/')


class TestSetSeeds:
    """Test the set_seeds function for proper seed pinning."""

    def test_set_seeds_resets_python_random(self):
        """Verify set_seeds resets the Python random module."""
        # Generate a number to change state
        _ = random.random()
        
        # Reset
        set_seeds(RANDOM_SEED)
        
        # Generate again
        val1 = random.random()
        
        # Reset again
        set_seeds(RANDOM_SEED)
        
        # Generate again
        val2 = random.random()
        
        assert val1 == val2, "Python random seed was not pinned correctly"

    def test_set_seeds_resets_numpy_random(self):
        """Verify set_seeds resets the numpy random state."""
        # Generate a number to change state
        _ = np.random.random()
        
        # Reset
        set_seeds(RANDOM_SEED)
        
        # Generate again
        val1 = np.random.random()
        
        # Reset again
        set_seeds(RANDOM_SEED)
        
        # Generate again
        val2 = np.random.random()
        
        assert val1 == val2, "Numpy random seed was not pinned correctly"

    def test_set_seeds_uses_config_seed_by_default(self):
        """Verify set_seeds uses the config's RANDOM_SEED when called without args."""
        random.seed(99999) # Set a different seed
        np.random.seed(99999)
        
        set_seeds() # Should use config's RANDOM_SEED
        
        val1 = random.random()
        
        random.seed(99999)
        np.random.seed(99999)
        
        set_seeds()
        
        val2 = random.random()
        
        assert val1 == val2, "Default seed usage failed"


class TestGetConfigSummary:
    """Test the get_config_summary function."""

    def test_returns_dictionary(self):
        """Verify get_config_summary returns a dict."""
        summary = get_config_summary()
        assert isinstance(summary, dict)

    def test_contains_expected_keys(self):
        """Verify summary contains key configuration values."""
        summary = get_config_summary()
        assert 'random_seed' in summary
        assert 'permutation_iterations' in summary
        assert 'raw_data_dir' in summary
        assert 'processed_data_dir' in summary
        assert 'figures_dir' in summary
        assert 'logs_dir' in summary

    def test_values_match_constants(self):
        """Verify summary values match the module constants."""
        summary = get_config_summary()
        assert summary['random_seed'] == RANDOM_SEED
        assert summary['permutation_iterations'] == PERMUTATION_ITERATIONS
        assert summary['raw_data_dir'] == RAW_DATA_DIR
        assert summary['processed_data_dir'] == PROCESSED_DATA_DIR
        assert summary['figures_dir'] == FIGURES_DIR
        assert summary['logs_dir'] == LOGS_DIR
