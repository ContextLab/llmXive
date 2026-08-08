"""
Unit tests for the seeding module.
"""
import random
import os
import pytest
import torch
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.seeding import (
    set_deterministic_seed,
    get_seed_config,
    verify_reproducibility,
    DeterministicContext
)


@pytest.fixture
def reset_seed():
    """Fixture to reset seeds before and after each test."""
    # Reset before
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)
    
    yield
    
    # Reset after
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)


class TestSetDeterministicSeed:
    def test_set_seed_validates_input(self, reset_seed):
        """Test that invalid seed values raise ValueError."""
        with pytest.raises(ValueError):
            set_deterministic_seed(-1)
        
        with pytest.raises(ValueError):
            set_deterministic_seed("42")
        
        with pytest.raises(ValueError):
            set_deterministic_seed(3.14)
    
    def test_sets_python_random_seed(self, reset_seed):
        """Test that Python random seed is set correctly."""
        set_deterministic_seed(42)
        state = random.getstate()
        assert state[1][0] == 42  # First value in state tuple is the seed
    
    def test_sets_numpy_seed(self, reset_seed):
        """Test that NumPy seed is set correctly."""
        set_deterministic_seed(42)
        state = np.random.get_state()
        assert state[1][0] == 42
    
    def test_sets_torch_seed(self, reset_seed):
        """Test that PyTorch seed is set correctly."""
        set_deterministic_seed(42)
        # torch.initial_seed() returns the seed modulo 2^32
        assert torch.initial_seed() % (2**32) == 42
    
    def test_sets_cudnn_deterministic(self, reset_seed):
        """Test that cudnn.deterministic is set when deterministic=True."""
        set_deterministic_seed(42, deterministic=True)
        if torch.cuda.is_available():
            assert torch.backends.cudnn.deterministic is True
    
    def test_sets_cudnn_benchmark(self, reset_seed):
        """Test that cudnn.benchmark is set when benchmark=True."""
        set_deterministic_seed(42, deterministic=False, benchmark=True)
        if torch.cuda.is_available():
            assert torch.backends.cudnn.benchmark is True
    
    def test_returns_config_dict(self, reset_seed):
        """Test that the function returns a configuration dictionary."""
        config = set_deterministic_seed(42)
        assert 'seed' in config
        assert 'deterministic' in config
        assert 'benchmark' in config
        assert config['seed'] == 42
        assert config['deterministic'] is True
        assert config['benchmark'] is False


class TestGetSeedConfig:
    def test_returns_config_without_modifying_state(self, reset_seed):
        """Test that get_seed_config doesn't modify the current state."""
        # Set a specific seed
        set_deterministic_seed(123)
        original_state = random.getstate()
        
        # Get config
        config = get_seed_config(456)
        
        # State should be unchanged
        assert random.getstate() == original_state
        assert config['seed'] == 456  # Reports the requested seed, not current


class TestVerifyReproducibility:
    def test_reproducible_results(self, reset_seed):
        """Test that reproducibility verification passes for a valid seed."""
        result = verify_reproducibility(seed=42, iterations=3)
        assert result is True
    
    def test_different_seeds_produce_different_results(self, reset_seed):
        """Test that different seeds produce different results."""
        set_deterministic_seed(42)
        tensor1 = torch.randn(10)
        
        set_deterministic_seed(123)
        tensor2 = torch.randn(10)
        
        assert not torch.allclose(tensor1, tensor2)


class TestDeterministicContext:
    def test_context_sets_seed(self, reset_seed):
        """Test that context manager sets the seed."""
        with DeterministicContext(42):
            assert torch.initial_seed() % (2**32) == 42
    
    def test_context_restores_state(self, reset_seed):
        """Test that context manager restores previous state."""
        # Set initial state
        set_deterministic_seed(123)
        initial_random_state = random.getstate()
        
        # Use context with different seed
        with DeterministicContext(456):
            inside_state = random.getstate()
            assert inside_state != initial_random_state
        
        # State should be restored
        after_state = random.getstate()
        assert after_state == initial_random_state
    
    def test_reproducibility_within_context(self, reset_seed):
        """Test that operations are reproducible within the same context."""
        with DeterministicContext(42):
            tensor1 = torch.randn(10)
            array1 = np.random.randn(10)
            random1 = [random.random() for _ in range(10)]
        
        with DeterministicContext(42):
            tensor2 = torch.randn(10)
            array2 = np.random.randn(10)
            random2 = [random.random() for _ in range(10)]
        
        assert torch.allclose(tensor1, tensor2)
        assert np.allclose(array1, array2)
        assert random1 == random2


class TestIntegration:
    def test_full_workflow(self, reset_seed):
        """Test a complete workflow using seeding utilities."""
        # Set seed
        config = set_deterministic_seed(999)
        assert config['seed'] == 999
        
        # Generate data
        data1 = {
            'torch': torch.randn(5),
            'numpy': np.random.randn(5),
            'random': [random.random() for _ in range(5)]
        }
        
        # Reset and regenerate
        set_deterministic_seed(999)
        data2 = {
            'torch': torch.randn(5),
            'numpy': np.random.randn(5),
            'random': [random.random() for _ in range(5)]
        }
        
        # Verify reproducibility
        assert torch.allclose(data1['torch'], data2['torch'])
        assert np.allclose(data1['numpy'], data2['numpy'])
        assert data1['random'] == data2['random']
        
        # Verify config
        current_config = get_seed_config(999)
        assert current_config['seed'] == 999