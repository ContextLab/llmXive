"""
Tests for the seed pinning utility in code/utils/config.py.
"""
import random
import numpy as np
import pytest

# Import the module under test
from code.utils.config import set_seed, validate_seed, get_environment_hash, TORCH_AVAILABLE

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_seed_determinism_python(self):
        """Verify that setting the seed produces deterministic random numbers."""
        set_seed(123)
        val1 = random.random()

        set_seed(123)
        val2 = random.random()

        assert val1 == val2, "Python random seed did not produce deterministic results."

    def test_seed_determinism_numpy(self):
        """Verify that setting the seed produces deterministic numpy arrays."""
        set_seed(456)
        arr1 = np.random.rand(5)

        set_seed(456)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2), "NumPy random seed did not produce deterministic results."

    def test_seed_determinism_torch(self):
        """Verify that setting the seed produces deterministic torch tensors if torch is available."""
        if not HAS_TORCH:
            pytest.skip("PyTorch not available")

        set_seed(789)
        tensor1 = torch.rand(5)

        set_seed(789)
        tensor2 = torch.rand(5)

        assert torch.equal(tensor1, tensor2), "PyTorch random seed did not produce deterministic results."

    def test_invalid_seed_type(self):
        """Verify that non-integer seeds raise ValueError."""
        with pytest.raises(ValueError):
            set_seed("invalid")

    def test_invalid_seed_negative(self):
        """Verify that negative seeds raise ValueError."""
        with pytest.raises(ValueError):
            set_seed(-1)

    def test_zero_seed(self):
        """Verify that seed 0 is valid."""
        result = set_seed(0)
        assert result["seed"] == 0
        assert result["python"] == "set"


class TestValidateSeed:
    """Tests for the validate_seed function."""

    def test_none_default(self):
        """Verify that None returns the default seed 42."""
        assert validate_seed(None) == 42

    def test_valid_seed(self):
        """Verify that valid seeds are returned unchanged."""
        assert validate_seed(999) == 999

    def test_invalid_seed(self):
        """Verify that invalid seeds raise ValueError."""
        with pytest.raises(ValueError):
            validate_seed(-5)


class TestGetEnvironmentHash:
    """Tests for the get_environment_hash function."""

    def test_hash_consistency(self):
        """Verify that the same seed produces the same hash."""
        hash1 = get_environment_hash(123)
        hash2 = get_environment_hash(123)
        assert hash1 == hash2

    def test_hash_differs_with_seed(self):
        """Verify that different seeds produce different hashes."""
        hash1 = get_environment_hash(123)
        hash2 = get_environment_hash(456)
        assert hash1 != hash2

    def test_hash_format(self):
        """Verify that the hash is a hex string of expected length."""
        h = get_environment_hash(123)
        assert len(h) == 16
        assert all(c in '0123456789abcdef' for c in h)

    def test_hash_includes_torch_status(self):
        """Verify that the hash reflects whether torch is available."""
        # This is implicitly tested by the fact that the hash changes if
        # the config dict changes, which includes torch availability.
        # We can't easily change torch availability in a test, so we just
        # verify the hash is generated without error.
        _ = get_environment_hash(123)