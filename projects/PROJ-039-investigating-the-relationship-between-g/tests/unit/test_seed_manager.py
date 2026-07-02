"""
Unit tests for the seed manager module.

Tests verify:
- Seed generation from project structure
- Seed setting across different libraries
- Context manager functionality
- Configuration save/load
"""
import os
import sys
import tempfile
from pathlib import Path
import json
import random
import hashlib

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from seed_manager import (
    set_seed, get_seed, generate_seed, 
    save_seed_config, load_seed_config,
    SeedContext, SeedManager, get_random_state
)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class TestSeedGeneration:
    """Test seed generation functionality."""

    def test_generate_seed_deterministic(self):
        """Test that generate_seed produces deterministic results."""
        seed1 = generate_seed("test_salt")
        seed2 = generate_seed("test_salt")
        assert seed1 == seed2, "Seed generation should be deterministic"

    def test_generate_seed_different_salt(self):
        """Test that different salts produce different seeds."""
        seed1 = generate_seed("salt1")
        seed2 = generate_seed("salt2")
        assert seed1 != seed2, "Different salts should produce different seeds"

    def test_generate_seed_no_salt(self):
        """Test seed generation without salt."""
        seed = generate_seed()
        assert isinstance(seed, int), "Seed should be an integer"
        assert seed >= 0, "Seed should be non-negative"


class TestSeedSetting:
    """Test seed setting functionality."""

    def test_set_seed_integer(self):
        """Test setting seed with an integer."""
        set_seed(42)
        assert get_seed() == 42, "Seed should be set to 42"

    def test_set_seed_string(self):
        """Test setting seed with a string."""
        set_seed("test_string")
        assert get_seed() is not None, "Seed should be set from string"

    def test_set_seed_none(self):
        """Test setting seed with None (auto-generate)."""
        set_seed(None)
        assert get_seed() is not None, "Seed should be auto-generated"

    def test_seed_reproducibility(self):
        """Test that setting the same seed produces same results."""
        set_seed(12345)
        val1 = random.random()
        
        set_seed(12345)
        val2 = random.random()
        
        assert val1 == val2, "Same seed should produce same random values"

    def test_numpy_seed_reproducibility(self):
        """Test numpy seed reproducibility."""
        if not HAS_NUMPY:
            return

        set_seed(54321)
        arr1 = np.random.rand(5)
        
        set_seed(54321)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "Numpy should be reproducible with same seed"


class TestContextManager:
    """Test SeedContext functionality."""

    def test_context_manager_sets_seed(self):
        """Test that context manager sets the seed."""
        set_seed(999)
        with SeedContext(111):
            assert get_seed() == 111, "Context should set seed to 111"
        # After context, seed should be restored
        assert get_seed() == 999, "Seed should be restored after context"

    def test_context_manager_nested(self):
        """Test nested context managers."""
        set_seed(100)
        with SeedContext(200):
            assert get_seed() == 200
            with SeedContext(300):
                assert get_seed() == 300
            assert get_seed() == 200
        assert get_seed() == 100

    def test_context_manager_exception(self):
        """Test that context manager restores seed even on exception."""
        set_seed(400)
        try:
            with SeedContext(500):
                assert get_seed() == 500
                raise ValueError("Test exception")
        except ValueError:
            pass
        assert get_seed() == 400, "Seed should be restored even after exception"


class TestConfiguration:
    """Test seed configuration save/load."""

    def test_save_and_load_config(self):
        """Test saving and loading seed configuration."""
        set_seed(777)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_seed_config(temp_path)
            loaded_seed = load_seed_config(temp_path)
            assert loaded_seed == 777, "Loaded seed should match saved seed"
        finally:
            os.unlink(temp_path)

    def test_save_config_creates_directory(self):
        """Test that save_config creates directory if needed."""
        set_seed(888)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'subdir' / 'config.json'
            save_seed_config(config_path)
            assert config_path.exists(), "Config file should be created"

    def test_load_nonexistent_config(self):
        """Test loading a nonexistent configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent = Path(temp_dir) / 'nonexistent.json'
            try:
                load_seed_config(nonexistent)
                assert False, "Should raise FileNotFoundError"
            except FileNotFoundError:
                pass  # Expected


class TestRandomState:
    """Test random state generation."""

    def test_get_random_state_with_seed(self):
        """Test getting random state with explicit seed."""
        rs = get_random_state(999)
        assert rs is not None, "Random state should be created"

    def test_random_state_reproducibility(self):
        """Test that random state produces reproducible results."""
        rs1 = get_random_state(123)
        val1 = rs1.random() if HAS_NUMPY else rs1.random()
        
        rs2 = get_random_state(123)
        val2 = rs2.random() if HAS_NUMPY else rs2.random()
        
        assert val1 == val2, "Same seed should produce same random values"

class TestSeedManagerSingleton:
    """Test SeedManager singleton behavior."""

    def test_singleton_instance(self):
        """Test that SeedManager returns same instance."""
        manager1 = SeedManager()
        manager2 = SeedManager()
        assert manager1 is manager2, "SeedManager should be a singleton"

    def test_seed_history(self):
        """Test seed history tracking."""
        set_seed(10)
        set_seed(20)
        set_seed(30)
        
        history = SeedManager().get_seed_history()
        assert len(history) >= 3, "Should track seed history"
        
        seeds = [h['seed'] for h in history]
        assert 10 in seeds and 20 in seeds and 30 in seeds, "All seeds should be in history"
