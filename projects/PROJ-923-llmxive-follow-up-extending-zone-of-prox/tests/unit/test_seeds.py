"""
Unit tests for deterministic random seed management.
"""
import random
import numpy as np
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.seeds import (
    set_global_seed,
    get_global_seed,
    is_deterministic,
    get_seed_context,
    generate_seed,
    ensure_seed_set,
    get_rng,
    reset_to_global_seed,
    SeedContext
)


class TestSeedManagement:
    """Tests for seed management functions."""
    
    def test_set_global_seed(self):
        """Test that setting a global seed initializes all generators."""
        test_seed = 12345
        set_global_seed(test_seed)
        
        assert get_global_seed() == test_seed
        assert is_deterministic() is True
        
        # Verify generators are seeded
        val1 = random.random()
        np_val1 = np.random.random()
        
        # Reset and verify same values
        reset_to_global_seed()
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2
        assert np_val1 == np_val2
    
    def test_set_global_seed_non_deterministic(self):
        """Test setting seed with deterministic=False."""
        set_global_seed(42, deterministic=False)
        
        assert is_deterministic() is False
        assert get_global_seed() == 42
    
    def test_get_seed_context(self):
        """Test seed context manager."""
        set_global_seed(100)
        
        # Generate some values with global seed
        reset_to_global_seed()
        val1 = random.random()
        
        # Use context with different seed
        with get_seed_context(200):
            val2 = random.random()
            assert val1 != val2  # Different seed should give different value
        
        # After context, should be back to global seed
        val3 = random.random()
        reset_to_global_seed()
        val4 = random.random()
        
        assert val3 == val4  # Should match global seed behavior
    
    def test_seed_context_no_seed_provided(self):
        """Test seed context without providing a seed (uses global)."""
        set_global_seed(300)
        
        reset_to_global_seed()
        val1 = random.random()
        
        with get_seed_context():
            val2 = random.random()
        
        reset_to_global_seed()
        val3 = random.random()
        
        assert val2 == val3  # Should use global seed
    
    def test_generate_seed(self):
        """Test that generate_seed produces a valid integer."""
        seed = generate_seed()
        assert isinstance(seed, int)
        assert 0 <= seed < 2**32
    
    def test_ensure_seed_set_with_seed(self):
        """Test ensure_seed_set when seed is already set."""
        set_global_seed(42)
        seed = ensure_seed_set()
        assert seed == 42
    
    def test_ensure_seed_set_without_seed_deterministic(self):
        """Test ensure_seed_set raises error in deterministic mode without seed."""
        # Clear global seed
        from utils import seeds
        seeds._global_seed = None
        seeds._is_deterministic = True
        
        with pytest.raises(ValueError, match="Deterministic mode is enabled but no global seed is set"):
            ensure_seed_set()
    
    def test_ensure_seed_set_without_seed_non_deterministic(self):
        """Test ensure_seed_set generates seed in non-deterministic mode."""
        from utils import seeds
        seeds._global_seed = None
        seeds._is_deterministic = False
        
        seed = ensure_seed_set()
        assert isinstance(seed, int)
        assert seeds._global_seed == seed
    
    def test_get_rng_with_seed(self):
        """Test get_rng creates a seeded generator."""
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        
        val1 = rng1.random()
        val2 = rng2.random()
        
        assert val1 == val2
    
    def test_get_rng_without_seed(self):
        """Test get_rng uses global seed when none provided."""
        set_global_seed(123)
        
        rng1 = get_rng()
        rng2 = get_rng()
        
        val1 = rng1.random()
        val2 = rng2.random()
        
        assert val1 == val2
    
    def test_get_rng_without_seed_no_global(self):
        """Test get_rng generates seed when no global seed exists."""
        from utils import seeds
        seeds._global_seed = None
        
        rng = get_rng()
        assert rng is not None
        assert isinstance(rng, np.random.Generator)
    
    def test_reset_to_global_seed(self):
        """Test reset_to_global_seed restores state."""
        set_global_seed(999)
        
        # Generate some values
        reset_to_global_seed()
        val1 = random.random()
        np_val1 = np.random.random()
        
        # Change state
        random.random()
        np.random.random()
        
        # Reset
        reset_to_global_seed()
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2
        assert np_val1 == np_val2
    
    def test_seed_context_restores_state(self):
        """Test that seed context properly restores state on exit."""
        set_global_seed(500)
        
        reset_to_global_seed()
        val_before = random.random()
        np_val_before = np.random.random()
        
        with get_seed_context(600):
            val_inside = random.random()
            np_val_inside = np.random.random()
        
        val_after = random.random()
        np_val_after = np.random.random()
        
        # Values inside context should be different
        assert val_before != val_inside
        assert np_val_before != np_val_inside
        
        # Values after context should match before (same seed state)
        assert val_before == val_after
        assert np_val_before == np_val_after
    
    def test_seed_context_exception_handling(self):
        """Test that seed context restores state even on exception."""
        set_global_seed(700)
        
        reset_to_global_seed()
        val_before = random.random()
        
        try:
            with get_seed_context(800):
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        val_after = random.random()
        
        # State should be restored despite exception
        assert val_before == val_after
