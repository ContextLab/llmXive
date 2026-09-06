"""
Unit tests for the seed management utility.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import random

# Import the module under test
from seed_manager import (
    SeedManager, set_seed, get_seed, generate_seed,
    save_seed_config, load_seed_config, SeedContext, get_random_state
)

@pytest.fixture
def temp_seed_file():
    """Create a temporary file for seed configuration."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def initialized_manager(temp_seed_file):
    """Initialize a SeedManager instance."""
    manager = SeedManager()
    manager.initialize(seed=42, seed_file=temp_seed_file)
    return manager

class TestSeedManager:
    """Tests for the SeedManager class."""
    
    def test_singleton_pattern(self):
        """Test that SeedManager follows the singleton pattern."""
        manager1 = SeedManager()
        manager2 = SeedManager()
        assert manager1 is manager2
    
    def test_initialize_with_seed(self, initialized_manager):
        """Test initialization with a specific seed."""
        assert initialized_manager.get_seed() == 42
    
    def test_initialize_with_generated_seed(self, temp_seed_file):
        """Test initialization generates a seed if none provided."""
        manager = SeedManager()
        # Reset the singleton for this test
        manager._initialized = False
        manager._seed = None
        manager._seed_file = None
        
        manager.initialize(seed_file=temp_seed_file)
        seed = manager.get_seed()
        assert isinstance(seed, int)
        assert seed > 0
    
    def test_set_seed(self, initialized_manager):
        """Test setting a new seed."""
        initialized_manager.set_seed(12345)
        assert initialized_manager.get_seed() == 12345
    
    def test_get_seed_not_initialized(self):
        """Test that get_seed raises error when not initialized."""
        manager = SeedManager()
        # Ensure not initialized
        manager._initialized = False
        manager._seed = None
        
        with pytest.raises(RuntimeError, match="not initialized"):
            manager.get_seed()
    
    def test_save_seed_config(self, initialized_manager, temp_seed_file):
        """Test saving seed configuration."""
        metadata = {"test_key": "test_value"}
        initialized_manager.save_seed_config(metadata)
        
        with open(temp_seed_file, 'r') as f:
            config = json.load(f)
        
        assert config["seed"] == 42
        assert config["test_key"] == "test_value"
        assert "generated_at" in config
    
    def test_load_seed_config(self, initialized_manager, temp_seed_file):
        """Test loading seed configuration."""
        # First save
        initialized_manager.save_seed_config()
        
        # Create a new manager and load
        new_manager = SeedManager()
        new_manager._initialized = False
        new_manager._seed = None
        new_manager._seed_file = temp_seed_file
        
        loaded_seed = load_seed_config(temp_seed_file)
        assert loaded_seed == 42

class TestSetSeed:
    """Tests for the set_seed function."""
    
    def test_sets_numpy_seed(self):
        """Test that set_seed affects numpy random."""
        set_seed(123)
        val1 = np.random.rand()
        
        set_seed(123)
        val2 = np.random.rand()
        
        assert val1 == val2
    
    def test_sets_random_seed(self):
        """Test that set_seed affects random module."""
        set_seed(456)
        val1 = random.random()
        
        set_seed(456)
        val2 = random.random()
        
        assert val1 == val2
    
    def test_invalid_seed_type(self):
        """Test that non-integer seed raises TypeError."""
        with pytest.raises(TypeError):
            set_seed("not an integer")

class TestGenerateSeed:
    """Tests for the generate_seed function."""
    
    def test_generates_integer(self):
        """Test that generate_seed returns an integer."""
        seed = generate_seed()
        assert isinstance(seed, int)
        assert seed > 0
    
    def test_generates_unique_seeds(self):
        """Test that multiple calls generate different seeds."""
        seeds = [generate_seed() for _ in range(100)]
        # With high probability, all seeds should be unique
        assert len(set(seeds)) == len(seeds)

class TestSeedContext:
    """Tests for the SeedContext context manager."""
    
    def test_temporarily_sets_seed(self):
        """Test that SeedContext temporarily sets and restores seed."""
        # Set initial seed
        set_seed(100)
        initial_val = random.random()
        
        # Use context manager
        with SeedContext(200):
            context_val = random.random()
            assert context_val != initial_val
        
        # After context, seed should be restored
        restored_val = random.random()
        set_seed(100)
        expected_restored = random.random()
        assert restored_val == expected_restored
    
    def test_restores_seed_after_exception(self):
        """Test that SeedContext restores seed even after exception."""
        set_seed(300)
        initial_val = random.random()
        
        try:
            with SeedContext(400):
                _ = random.random()
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Seed should be restored
        restored_val = random.random()
        set_seed(300)
        expected_restored = random.random()
        assert restored_val == expected_restored

class TestGetRandomState:
    """Tests for the get_random_state function."""
    
    def test_returns_random_state(self):
        """Test that get_random_state returns a numpy RandomState."""
        state = get_random_state(555)
        assert isinstance(state, np.random.RandomState)
    
    def test_reproducible_with_seed(self):
        """Test that RandomState produces reproducible results."""
        state1 = get_random_state(777)
        val1 = state1.rand()
        
        state2 = get_random_state(777)
        val2 = state2.rand()
        
        assert val1 == val2
    
    def test_uses_global_seed(self):
        """Test that get_random_state uses global seed if none provided."""
        set_seed(999)
        state = get_random_state()
        val = state.rand()
        
        set_seed(999)
        state2 = get_random_state()
        val2 = state2.rand()
        
        assert val == val2

class TestLoadSeedConfigErrors:
    """Tests for error conditions in load_seed_config."""
    
    def test_file_not_found(self, temp_seed_file):
        """Test that FileNotFoundError is raised for missing file."""
        # Ensure file doesn't exist
        if os.path.exists(temp_seed_file):
            os.remove(temp_seed_file)
        
        with pytest.raises(FileNotFoundError):
            load_seed_config(temp_seed_file)
    
    def test_invalid_json(self, temp_seed_file):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with open(temp_seed_file, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_seed_config(temp_seed_file)
    
    def test_missing_seed_key(self, temp_seed_file):
        """Test that ValueError is raised if 'seed' key is missing."""
        with open(temp_seed_file, 'w') as f:
            json.dump({"other_key": "value"}, f)
        
        with pytest.raises(ValueError, match="'seed' key missing"):
            load_seed_config(temp_seed_file)
