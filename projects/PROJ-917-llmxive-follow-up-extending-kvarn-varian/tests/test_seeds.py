"""
Tests for global random seed management.

These tests verify that set_global_seed correctly initializes
the random number generators for reproducibility.
"""
import random
import pytest
import numpy as np

# Import the module under test
from code.utils import seeds
from code.utils.seeds import (
    set_global_seed,
    get_seed,
    ensure_seed_set,
    reset_seed,
    get_seed_info
)

# Helper to generate a deterministic sequence from a seed
def generate_sequence(seed, length=5):
    """Generate a sequence of random numbers for a given seed."""
    set_global_seed(seed)
    seq = []
    # Generate from all three sources
    for _ in range(length):
        seq.append(random.random())
        seq.append(np.random.random())
        if seeds.TORCH_AVAILABLE:
            import torch
            seq.append(torch.rand(1).item())
    return seq

class TestSeedManagement:
    """Test suite for seed management functions."""

    def test_set_global_seed_initializes_all(self):
        """Test that set_global_seed initializes random, numpy, and torch."""
        seed_value = 12345
        set_global_seed(seed_value)

        assert get_seed() == seed_value
        assert get_seed_info()["is_set"] is True
        assert get_seed_info()["seed"] == seed_value

        # Verify reproducibility
        val1 = random.random()
        val2 = np.random.random()
        if seeds.TORCH_AVAILABLE:
            import torch
            val3 = torch.rand(1).item()

        # Reset and regenerate
        set_global_seed(seed_value)
        assert random.random() == val1
        assert np.random.random() == val2
        if seeds.TORCH_AVAILABLE:
            assert torch.rand(1).item() == val3

    def test_seed_determinism_across_calls(self):
        """Test that the same seed produces identical sequences."""
        seed = 42
        seq1 = generate_sequence(seed)
        seq2 = generate_sequence(seed)
        assert seq1 == seq2

    def test_different_seeds_produce_different_sequences(self):
        """Test that different seeds produce different sequences."""
        seq1 = generate_sequence(100)
        seq2 = generate_sequence(200)
        assert seq1 != seq2

    def test_reset_seed(self):
        """Test that reset_seed clears the global state."""
        set_global_seed(999)
        assert get_seed() == 999
        reset_seed()
        assert get_seed() is None
        assert get_seed_info()["is_set"] is False

    def test_ensure_seed_set_uses_default(self):
        """Test that ensure_seed_set sets a default if none exists."""
        reset_seed()
        default = 777
        result = ensure_seed_set(default_seed=default)
        assert result == default
        assert get_seed() == default

    def test_ensure_seed_set_preserves_existing(self):
        """Test that ensure_seed_set does not overwrite an existing seed."""
        existing = 888
        set_global_seed(existing)
        result = ensure_seed_set(default_seed=999)
        assert result == existing
        assert get_seed() == existing

    def test_invalid_seed_type(self):
        """Test that non-integer seeds raise TypeError."""
        with pytest.raises(TypeError):
            set_global_seed("not_an_int")
        with pytest.raises(TypeError):
            set_global_seed(3.14)

    def test_cuda_determinism_flags(self):
        """Test that CUDA determinism flags are set if CUDA is available."""
        if not seeds.TORCH_AVAILABLE:
            pytest.skip("PyTorch not available")

        import torch
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")

        set_global_seed(1234)

        assert os.environ.get('CUBLAS_WORKSPACE_CONFIG') == ':4096:8'
        assert os.environ.get('PYTHONHASHSEED') == '1234'
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False

    def test_context_manager(self):
        """Test the seed context manager."""
        set_global_seed(10)
        initial_val = random.random()

        with seeds.get_seed_context(20):
            assert get_seed() == 20
            context_val = random.random()

        # Should restore to 10
        assert get_seed() == 10
        # Regenerating should match initial
        assert random.random() == initial_val
        assert context_val != initial_val