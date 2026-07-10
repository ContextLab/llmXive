"""
Tests for the configuration module.
"""

import pytest
import sys
from pathlib import Path
from config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    CODE_DIR,
    TESTS_DIR,
    CONTRACTS_DIR,
    FIGURES_DIR,
    RANDOM_SEED,
    set_all_seeds,
    ensure_directories,
    HYPERPARAMETERS,
    DATA_SOURCES,
)

class TestConfig:
    def test_project_root_exists(self):
        """Verify PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_directory_paths_defined(self):
        """Verify all expected directory paths are defined."""
        assert isinstance(DATA_DIR, Path)
        assert isinstance(RAW_DATA_DIR, Path)
        assert isinstance(PROCESSED_DATA_DIR, Path)
        assert isinstance(CODE_DIR, Path)
        assert isinstance(TESTS_DIR, Path)
        assert isinstance(CONTRACTS_DIR, Path)
        assert isinstance(FIGURES_DIR, Path)

    def test_directory_structure(self):
        """Verify that directory paths are relative to PROJECT_ROOT."""
        assert DATA_DIR.parent == PROJECT_ROOT
        assert CODE_DIR.parent == PROJECT_ROOT
        assert TESTS_DIR.parent == PROJECT_ROOT

    def test_random_seed_defined(self):
        """Verify random seed is an integer."""
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_hyperparameters_structure(self):
        """Verify hyperparameters dictionary has expected keys."""
        expected_keys = ["lasso", "elastic_net", "random_forest", "gradient_boosting"]
        for key in expected_keys:
            assert key in HYPERPARAMETERS

    def test_data_sources_structure(self):
        """Verify data sources dictionary has expected keys."""
        assert "1001_genomes" in DATA_SOURCES
        assert "atrdb" in DATA_SOURCES

    def test_ensure_directories(self, tmp_path):
        """Test that ensure_directories creates the required folders."""
        # Temporarily override PROJECT_ROOT for this test
        import config
        original_root = config.PROJECT_ROOT
        
        # Create a temporary root
        temp_root = tmp_path / "test_project"
        config.PROJECT_ROOT = temp_root
        config.DATA_DIR = temp_root / "data"
        config.RAW_DATA_DIR = config.DATA_DIR / "raw"
        config.PROCESSED_DATA_DIR = config.DATA_DIR / "processed"
        config.CODE_DIR = temp_root / "code"
        config.TESTS_DIR = temp_root / "tests"
        config.CONTRACTS_DIR = temp_root / "contracts"
        config.FIGURES_DIR = config.PROCESSED_DATA_DIR / "figures"

        try:
            ensure_directories()
            
            assert config.RAW_DATA_DIR.exists()
            assert config.PROCESSED_DATA_DIR.exists()
            assert config.CODE_DIR.exists()
            assert config.TESTS_DIR.exists()
            assert config.CONTRACTS_DIR.exists()
            assert config.FIGURES_DIR.exists()
        finally:
            # Restore original root
            config.PROJECT_ROOT = original_root

    def test_set_all_seeds(self):
        """Test that set_all_seeds sets the random seeds."""
        import random
        import numpy as np
        
        seed_value = 12345
        set_all_seeds(seed_value)
        
        # Check random
        val1 = random.random()
        set_all_seeds(seed_value)
        val2 = random.random()
        
        assert val1 == val2
        
        # Check numpy
        arr1 = np.random.rand(5)
        set_all_seeds(seed_value)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)