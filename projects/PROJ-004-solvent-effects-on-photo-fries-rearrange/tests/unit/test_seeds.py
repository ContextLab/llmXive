"""
Unit tests for code.utils.seeds module.
"""
import os
import random
import numpy as np
import pytest
from code.utils import seeds


class TestSeedSetting:
    """Tests for the set_seed function."""

    def test_set_seed_affects_random(self):
        """Verify that random module is seeded correctly."""
        seeds.set_seed(12345)
        val1 = random.random()
        
        seeds.set_seed(12345)
        val2 = random.random()
        
        assert val1 == val2, "Random seed did not produce reproducible results."

    def test_set_seed_affects_numpy(self):
        """Verify that numpy random state is seeded correctly."""
        seeds.set_seed(12345)
        arr1 = np.random.rand(5)
        
        seeds.set_seed(12345)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "Numpy seed did not produce reproducible results.")

    def test_set_seed_affects_torch_if_available(self):
        """Verify that torch is seeded correctly if available."""
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not installed.")

        seeds.set_seed(12345)
        t1 = torch.rand(5)
        
        seeds.set_seed(12345)
        t2 = torch.rand(5)
        
        torch.testing.assert_close(t1, t2, "Torch seed did not produce reproducible results.")

    def test_set_seed_affects_tensorflow_if_available(self):
        """Verify that tensorflow is seeded correctly if available."""
        try:
            import tensorflow as tf
        except ImportError:
            pytest.skip("TensorFlow not installed.")

        seeds.set_seed(12345)
        t1 = tf.random.uniform((5,))
        
        seeds.set_seed(12345)
        t2 = tf.random.uniform((5,))
        
        np.testing.assert_array_equal(t1.numpy(), t2.numpy(), "TensorFlow seed did not produce reproducible results.")

    def test_environment_variable_set(self):
        """Verify that PYTHONHASHSEED is set."""
        seeds.set_seed(12345)
        assert os.environ.get('PYTHONHASHSEED') == '12345'


class TestSeedHash:
    """Tests for the get_seed_hash function."""

    def test_get_seed_hash_deterministic(self):
        """Verify that the hash is deterministic for the same seed."""
        hash1 = seeds.get_seed_hash(12345, prefix="test")
        hash2 = seeds.get_seed_hash(12345, prefix="test")
        assert hash1 == hash2

    def test_get_seed_hash_unique_for_different_seeds(self):
        """Verify that different seeds produce different hashes."""
        hash1 = seeds.get_seed_hash(12345, prefix="test")
        hash2 = seeds.get_seed_hash(67890, prefix="test")
        assert hash1 != hash2

    def test_get_seed_hash_length(self):
        """Verify the hash length is as expected."""
        h = seeds.get_seed_hash(12345)
        assert len(h) == 16


class TestResetSeeds:
    """Tests for the reset_seeds_to_default function."""

    def test_reset_to_default(self):
        """Verify that reset sets seeds to 42."""
        seeds.set_seed(99999)
        seeds.reset_seeds_to_default()
        
        # Check random
        val1 = random.random()
        seeds.reset_seeds_to_default()
        val2 = random.random()
        assert val1 == val2
        
        # Check numpy
        arr1 = np.random.rand(5)
        seeds.reset_seeds_to_default()
        arr2 = np.random.rand(5)
        np.testing.assert_array_equal(arr1, arr2)