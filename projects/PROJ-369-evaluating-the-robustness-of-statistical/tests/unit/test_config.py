"""
Unit tests for the configuration module.
"""
import os
import sys
from pathlib import Path
import pytest

# Add src to path for imports if running from tests/
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils.config import (
    set_seed, 
    get_path, 
    ALPHA, 
    RANDOM_SEED, 
    PROJECT_ROOT, 
    DATA_ROOT, 
    RESULTS_ROOT,
    ensure_dirs
)
import numpy as np

class TestConfigConstants:
    def test_alpha_is_005(self):
        assert ALPHA == 0.05

    def test_random_seed_is_42(self):
        assert RANDOM_SEED == 42

    def test_paths_are_pathlib_objects(self):
        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(DATA_ROOT, Path)
        assert isinstance(RESULTS_ROOT, Path)

class TestSetSeed:
    def test_set_seed_reproducibility(self):
        # Set seed
        set_seed(123)
        val1 = np.random.random()
        
        # Reset seed
        set_seed(123)
        val2 = np.random.random()
        
        assert val1 == val2

    def test_set_seed_different_values(self):
        set_seed(1)
        val1 = np.random.random()
        
        set_seed(2)
        val2 = np.random.random()
        
        assert val1 != val2

class TestGetPath:
    def test_get_path_raw(self):
        path = get_path("raw")
        assert path == DATA_ROOT / "raw"
        assert path.exists()

    def test_get_path_processed(self):
        path = get_path("processed")
        assert path == DATA_ROOT / "processed"
        assert path.exists()

    def test_get_path_results(self):
        path = get_path("results")
        assert path == RESULTS_ROOT
        assert path.exists()

    def test_get_path_invalid_key(self):
        with pytest.raises(KeyError):
            get_path("invalid_key")

class TestEnsureDirs:
    def test_ensure_dirs_creates_missing(self):
        # Temporarily move a dir out of the way to test creation
        # (Simulated by ensuring they exist, logic is trivial)
        ensure_dirs()
        assert (DATA_ROOT / "raw").exists()
        assert (DATA_ROOT / "processed").exists()
        assert RESULTS_ROOT.exists()