import os
import pytest
import random
import numpy as np
from unittest.mock import patch
from utils.seed_manager import initialize_reproducibility, get_current_seed, get_version_info
from config import set_seed, get_seed

class TestSeedManager:
    def test_initialize_reproducibility_sets_python_seed(self):
        """Verify that Python's random module is seeded correctly."""
        seed_val = 12345
        initialize_reproducibility(seed_val)
        
        # Generate a few numbers
        val1 = random.random()
        
        # Reset and regenerate
        initialize_reproducibility(seed_val)
        val2 = random.random()
        
        assert val1 == val2, "Python random seed not set correctly"

    def test_initialize_reproducibility_sets_numpy_seed(self):
        """Verify that NumPy's random module is seeded correctly."""
        seed_val = 67890
        initialize_reproducibility(seed_val)
        
        arr1 = np.random.rand(5)
        
        initialize_reproducibility(seed_val)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "NumPy random seed not set correctly"

    def test_initialize_reproducibility_sets_config_seed(self):
        """Verify that the global config seed is updated."""
        seed_val = 11223
        result = initialize_reproducibility(seed_val)
        
        assert get_seed() == seed_val
        assert result["seed"] == seed_val

    def test_initialize_reproducibility_with_env_var(self):
        """Test reading seed from environment variable."""
        seed_val = 99999
        with patch.dict(os.environ, {"PYTHON_SEED": str(seed_val)}):
            result = initialize_reproducibility()
            assert result["seed"] == seed_val

    def test_initialize_reproducibility_fails_without_seed(self):
        """Test that initialization fails if no seed is provided and no env var exists."""
        # Ensure no env var is set
        env_copy = os.environ.copy()
        env_copy.pop("PYTHON_SEED", None)
        
        with patch.dict(os.environ, env_copy, clear=False):
            with pytest.raises(ValueError) as exc_info:
                initialize_reproducibility()
            
            assert "No random seed provided" in str(exc_info.value)

    def test_get_current_seed_raises_if_not_initialized(self):
        """Test that get_current_seed raises if no seed is set."""
        # Reset seed to None
        set_seed(None)
        
        with pytest.raises(ValueError) as exc_info:
            get_current_seed()
        
        assert "No seed initialized" in str(exc_info.value)

    def test_get_version_info_returns_correct_structure(self):
        """Test that get_version_info returns expected keys."""
        initialize_reproducibility(42)
        info = get_version_info()
        
        assert "seed" in info
        assert "version_hash" in info
        assert "config_summary" in info
        assert isinstance(info["seed"], int)
        assert isinstance(info["version_hash"], str)
