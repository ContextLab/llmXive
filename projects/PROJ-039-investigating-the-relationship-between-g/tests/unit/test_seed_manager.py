"""
Unit tests for the seed management utility.
"""
import pytest
import random
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from seed_manager import (
    SeedManager,
    set_seed,
    get_seed,
    generate_seed,
    save_seed_config,
    load_seed_config,
    SeedContext,
    get_random_state
)
from config import get_project_root


class TestSeedManager:
    """Tests for the SeedManager class."""
    
    def test_set_seed_with_value(self):
        """Test setting a specific seed value."""
        seed_value = 12345
        result = SeedManager.set_seed(seed_value)
        
        assert result == seed_value
        assert SeedManager.get_seed() == seed_value
    
    def test_set_seed_generates_new_seed_when_none(self):
        """Test that setting seed to None generates a new random seed."""
        result = SeedManager.set_seed(None)
        
        assert result is not None
        assert isinstance(result, int)
        assert SeedManager.get_seed() == result
    
    def test_set_seed_affects_python_random(self):
        """Test that setting seed affects Python's random module."""
        seed_value = 42
        SeedManager.set_seed(seed_value)
        
        # Generate a few random numbers
        rand1 = [random.random() for _ in range(3)]
        
        # Reset and regenerate
        SeedManager.set_seed(seed_value)
        rand2 = [random.random() for _ in range(3)]
        
        assert rand1 == rand2
    
    def test_generate_seed_returns_integer(self):
        """Test that generate_seed returns an integer."""
        seed = SeedManager.generate_seed()
        
        assert isinstance(seed, int)
        assert seed > 0
    
    def test_save_and_load_seed_config(self, tmp_path):
        """Test saving and loading seed configuration."""
        seed_value = 99999
        config_file = tmp_path / "test_seed_config.json"
        
        # Save
        SeedManager.save_seed_config(seed_value, str(config_file))
        
        assert config_file.exists()
        
        # Load
        loaded_seed = SeedManager.load_seed_config(str(config_file))
        
        assert loaded_seed == seed_value
    
    def test_load_seed_config_nonexistent_file(self):
        """Test loading from a non-existent file returns None."""
        result = SeedManager.load_seed_config("/nonexistent/path/file.json")
        
        assert result is None
    
    def test_seed_context_manager(self):
        """Test the SeedContext manager properly sets and restores seeds."""
        original_seed = 111
        temp_seed = 222
        
        SeedManager.set_seed(original_seed)
        
        with SeedContext(temp_seed) as context_seed:
            assert context_seed == temp_seed
            assert SeedManager.get_seed() == temp_seed
        
        # Should be restored to original
        assert SeedManager.get_seed() == original_seed
    
    def test_get_random_state(self):
        """Test that get_random_state returns expected structure."""
        seed_value = 55555
        SeedManager.set_seed(seed_value)
        
        state = SeedManager.get_random_state()
        
        assert "python_random" in state
        assert state["python_random"] is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_set_seed_function(self):
        """Test the set_seed convenience function."""
        result = set_seed(777)
        
        assert result == 777
        assert get_seed() == 777
    
    def test_generate_seed_function(self):
        """Test the generate_seed convenience function."""
        seed = generate_seed()
        
        assert isinstance(seed, int)
        assert seed > 0
    
    def test_get_seed_function(self):
        """Test the get_seed convenience function."""
        set_seed(888)
        result = get_seed()
        
        assert result == 888
    
    def test_save_seed_config_function(self, tmp_path):
        """Test the save_seed_config convenience function."""
        config_file = tmp_path / "test_config.json"
        save_seed_config(999, str(config_file))
        
        assert config_file.exists()
        with open(config_file, 'r') as f:
            data = json.load(f)
            assert data["seed"] == 999
    
    def test_load_seed_config_function(self, tmp_path):
        """Test the load_seed_config convenience function."""
        config_file = tmp_path / "test_config.json"
        save_seed_config(101010, str(config_file))
        
        result = load_seed_config(str(config_file))
        
        assert result == 101010
    
    def test_seed_context_class(self):
        """Test the SeedContext class as a context manager."""
        set_seed(123)
        
        with SeedContext(456):
            assert get_seed() == 456
        
        assert get_seed() == 123


class TestReproducibility:
    """Tests to verify reproducibility guarantees."""
    
    def test_reproducible_random_sequence(self):
        """Test that the same seed produces the same random sequence."""
        seed = 42
        
        # First run
        set_seed(seed)
        sequence1 = [random.random() for _ in range(10)]
        
        # Second run with same seed
        set_seed(seed)
        sequence2 = [random.random() for _ in range(10)]
        
        assert sequence1 == sequence2
    
    def test_reproducible_with_numpy(self):
        """Test reproducibility with numpy if available."""
        try:
            import numpy as np
            seed = 12345
            
            # First run
            set_seed(seed)
            arr1 = np.random.rand(5)
            
            # Second run with same seed
            set_seed(seed)
            arr2 = np.random.rand(5)
            
            assert np.array_equal(arr1, arr2)
        except ImportError:
            pytest.skip("numpy not installed")
    
    def test_reproducible_with_torch(self):
        """Test reproducibility with torch if available."""
        try:
            import torch
            seed = 54321
            
            # First run
            set_seed(seed)
            tensor1 = torch.rand(5)
            
            # Second run with same seed
            set_seed(seed)
            tensor2 = torch.rand(5)
            
            assert torch.equal(tensor1, tensor2)
        except ImportError:
            pytest.skip("torch not installed")


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_seed_zero(self):
        """Test that seed value 0 is valid."""
        set_seed(0)
        assert get_seed() == 0
    
    def test_seed_large_value(self):
        """Test that large seed values are handled correctly."""
        large_seed = 2**31 - 1
        set_seed(large_seed)
        assert get_seed() == large_seed
    
    def test_negative_seed(self):
        """Test that negative seed values are handled (may vary by library)."""
        # Python's random accepts negative seeds
        set_seed(-123)
        assert get_seed() == -123
    
    def test_seed_config_persistence(self, tmp_path):
        """Test that seed config persists across multiple saves."""
        config_file = tmp_path / "persist_test.json"
        
        set_seed(111, persist=False)
        save_seed_config(222, str(config_file))
        set_seed(333, persist=True)
        
        # Reload and verify the last saved seed
        loaded = load_seed_config(str(config_file))
        assert loaded == 333
    
    def test_seed_context_exception_handling(self):
        """Test that seed is restored even if exception occurs in context."""
        set_seed(100)
        
        try:
            with SeedContext(200):
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Seed should be restored
        assert get_seed() == 100
