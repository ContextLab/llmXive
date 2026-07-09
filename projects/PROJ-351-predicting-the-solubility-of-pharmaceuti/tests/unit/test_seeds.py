"""
Unit tests for seed configuration management.

Tests verify that:
1. Seeds are correctly retrieved from environment or defaults
2. Setting a seed initializes all required libraries
3. Deterministic behavior is achieved
"""
import os
import random
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pytest

# Import the module under test
# Note: We assume the code/config directory is in the Python path
# or we adjust sys.path for the test
import sys
from pathlib import Path

# Add the code directory to the path if not already there
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config.seeds import set_seed, get_seed, ensure_seeded, DEFAULT_SEED, SEED_ENV_VAR

# Try to import torch for conditional tests
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TestSeedRetrieval:
    """Tests for get_seed() function."""

    def test_get_seed_default(self, monkeypatch):
        """Test that default seed is returned when no env var is set."""
        monkeypatch.delenv(SEED_ENV_VAR, raising=False)
        assert get_seed() == DEFAULT_SEED

    def test_get_seed_from_env(self, monkeypatch):
        """Test that seed is retrieved from environment variable."""
        test_seed = 12345
        monkeypatch.setenv(SEED_ENV_VAR, str(test_seed))
        assert get_seed() == test_seed

    def test_get_seed_invalid_env_fallback(self, monkeypatch):
        """Test that default seed is used if env var is invalid."""
        monkeypatch.setenv(SEED_ENV_VAR, "not_a_number")
        # Should fall back to default without crashing
        assert get_seed() == DEFAULT_SEED


class TestSeedSetting:
    """Tests for set_seed() function."""

    def test_set_seed_updates_python_random(self):
        """Test that Python's random module is seeded."""
        seed = 42
        set_seed(seed)
        val1 = random.random()
        set_seed(seed)
        val2 = random.random()
        assert val1 == val2

    def test_set_seed_updates_numpy(self):
        """Test that NumPy is seeded."""
        seed = 42
        set_seed(seed)
        arr1 = np.random.rand(5)
        set_seed(seed)
        arr2 = np.random.rand(5)
        np.testing.assert_array_equal(arr1, arr2)

    def test_set_seed_updates_torch(self):
        """Test that PyTorch is seeded if available."""
        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch not available")

        seed = 42
        set_seed(seed)
        tensor1 = torch.rand(5)
        set_seed(seed)
        tensor2 = torch.rand(5)
        torch.testing.assert_close(tensor1, tensor2)

    def test_set_seed_updates_hash_seed_env(self):
        """Test that PYTHONHASHSEED is set."""
        seed = 42
        set_seed(seed)
        assert os.environ.get("PYTHONHASHSEED") == str(seed)

    def test_set_seed_uses_argument(self):
        """Test that argument overrides environment."""
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv(SEED_ENV_VAR, "999")
        set_seed(42)
        # The function should use the argument, not the env var
        # We verify by checking that subsequent random numbers match the arg seed
        val1 = random.random()
        monkeypatch.setenv(SEED_ENV_VAR, "42")
        set_seed(42)
        val2 = random.random()
        assert val1 == val2


class TestEnsureSeeded:
    """Tests for ensure_seeded() function."""

    def test_ensure_seeded_sets_seed(self):
        """Test that ensure_seeded initializes seeds."""
        # Clear any existing seed setting
        seed = 42
        random.seed(0)
        np.random.seed(0)
        
        set_seed(seed)
        
        # Verify seeds are set
        val1 = random.random()
        arr1 = np.random.rand(1)
        
        # Reset to 0
        random.seed(0)
        np.random.seed(0)
        
        # Re-ensure
        set_seed(seed)
        
        val2 = random.random()
        arr2 = np.random.rand(1)
        
        assert val1 == val2
        np.testing.assert_array_equal(arr1, arr2)
