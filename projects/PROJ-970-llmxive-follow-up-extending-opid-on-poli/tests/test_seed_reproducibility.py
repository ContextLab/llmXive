"""
Tests for seed initialization and reproducibility.
"""
import random
import os
import sys
import pytest

# Ensure we can import from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import set_seed, get_seed, get_version_hash, get_config_summary
from utils.seed_manager import initialize_reproducibility, get_current_seed, get_version_info

def test_seed_initialization():
    """Test that setting a seed initializes the global state correctly."""
    test_seed = 12345
    result = set_seed(test_seed)
    
    assert result == test_seed
    assert get_seed() == test_seed
    
    # Verify random module is seeded
    val1 = random.random()
    set_seed(test_seed)
    val2 = random.random()
    assert val1 == val2

def test_default_seed():
    """Test that the default seed is used when none is specified."""
    # Reset to default
    set_seed(None)
    default = get_seed()
    assert default is not None
    assert default == 42  # As defined in config.py

def test_version_hash_changes_with_seed():
    """Test that version hash changes when seed changes."""
    hash1 = get_version_hash()
    set_seed(100)
    hash2 = get_version_hash()
    assert hash1 != hash2

def test_version_hash_deterministic():
    """Test that same seed produces same version hash."""
    set_seed(500)
    hash1 = get_version_hash()
    set_seed(500)
    hash2 = get_version_hash()
    assert hash1 == hash2

def test_config_summary():
    """Test that config summary returns correct data."""
    set_seed(999)
    summary = get_config_summary()
    assert "seed" in summary
    assert "version_hash" in summary
    assert summary["seed"] == 999

def test_seed_manager_initialization():
    """Test the seed manager utility functions."""
    info = initialize_reproducibility(777)
    assert info["seed"] == 777
    assert get_current_seed() == 777
    assert "version_hash" in info

def test_random_sequence_reproducibility():
    """Test that a sequence of random numbers is reproducible with same seed."""
    set_seed(42)
    seq1 = [random.random() for _ in range(5)]
    
    set_seed(42)
    seq2 = [random.random() for _ in range(5)]
    
    assert seq1 == seq2

def test_different_seeds_different_sequences():
    """Test that different seeds produce different random sequences."""
    set_seed(10)
    seq1 = [random.random() for _ in range(5)]
    
    set_seed(20)
    seq2 = [random.random() for _ in range(5)]
    
    assert seq1 != seq2
