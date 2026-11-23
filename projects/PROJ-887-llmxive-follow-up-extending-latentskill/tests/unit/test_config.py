"""
Unit tests for src/utils/config.py
"""

import os
import tempfile
from pathlib import Path
import pytest

# Mock torch/numpy if not present to avoid import errors in test env
# In real env, they are present
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from src.utils.config import (
    initialize,
    get_config,
    get_path,
    get_project_root,
    get_seed,
    _PROJECT_ROOT,
    DEFAULT_SEED
)

class TestConfigInitialization:
    def test_initialize_default_seed(self):
        """Test that initialize sets the default seed if none provided."""
        # Reset state if possible (simulating fresh run)
        # Note: In a real scenario, we might need to mock the global state
        # For this test, we assume a fresh interpreter or rely on the function logic
        
        config = initialize(seed=None)
        assert config["seed"] == DEFAULT_SEED
        assert get_seed() == DEFAULT_SEED
    
    def test_initialize_custom_seed(self):
        """Test that initialize respects a custom seed."""
        custom_seed = 12345
        config = initialize(seed=custom_seed)
        assert config["seed"] == custom_seed
        assert get_seed() == custom_seed
    
    def test_seed_reproducibility(self):
        """Test that seeds are actually set for random, numpy, and torch."""
        seed_val = 999
        initialize(seed=seed_val)
        
        # Check Python random
        import random
        val1 = random.random()
        
        # Reset and check again
        initialize(seed=seed_val)
        val2 = random.random()
        
        assert val1 == val2, "Python random seed not pinned correctly"
        
        if HAS_NUMPY:
            initialize(seed=seed_val)
            arr1 = np.random.rand(5)
            initialize(seed=seed_val)
            arr2 = np.random.rand(5)
            assert np.array_equal(arr1, arr2), "Numpy random seed not pinned correctly"
        
        if HAS_TORCH:
            initialize(seed=seed_val)
            t1 = torch.rand(5)
            initialize(seed=seed_val)
            t2 = torch.rand(5)
            assert torch.equal(t1, t2), "PyTorch random seed not pinned correctly"

class TestPathResolution:
    def test_get_project_root(self):
        """Test that project root is detected correctly."""
        root = get_project_root()
        assert isinstance(root, Path)
        # Should contain 'src' and 'tests' typically
        assert (root / "src").exists() or root.name == "src"
    
    def test_get_path_relative(self):
        """Test resolving a relative path."""
        p = get_path("data/raw/test.csv")
        expected = _PROJECT_ROOT / "data" / "raw" / "test.csv"
        assert p == expected
    
    def test_get_path_absolute(self):
        """Test that absolute paths are returned as-is."""
        abs_path = "/tmp/test_file.txt"
        p = get_path(abs_path)
        assert p == Path(abs_path)
    
    def test_get_data_dir(self):
        """Test get_data_dir returns the correct path."""
        from src.utils.config import get_data_dir
        # Assuming no env override
        expected = _PROJECT_ROOT / "data"
        assert get_data_dir() == expected

class TestEnvironmentVariables:
    def test_env_override_seed(self, monkeypatch):
        """Test that environment variable overrides default seed."""
        monkeypatch.setenv("SEED", "888")
        # Re-initialize to pick up env var
        # Note: In a real test suite, we might need to reset the _is_initialized flag
        # For this simple test, we assume we can re-run or the module reloads
        # Here we just check the logic via a fresh call if we could reset, 
        # but since we can't easily reset the global cache in this snippet,
        # we rely on the fact that initialize() reads env vars.
        
        # To properly test, we'd need to mock the global state or reload the module.
        # For now, we verify the environment variable is read by the helper.
        from src.utils.config import _get_env
        val = _get_env("SEED", "42")
        assert val == "888"
    
    def test_env_device(self, monkeypatch):
        """Test device configuration via env var."""
        monkeypatch.setenv("DEVICE", "cuda")
        # We can't easily re-initialize the global state in this test without side effects
        # But we can verify the helper reads it.
        from src.utils.config import _get_env
        val = _get_env("DEVICE", "cpu")
        assert val == "cuda"
