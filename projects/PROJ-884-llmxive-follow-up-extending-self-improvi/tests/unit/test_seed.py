import pytest
import random
import os
from code.utils.seed import (
    set_seed, 
    get_seed, 
    generate_seed_from_string, 
    reset_seed, 
    set_deterministic_mode
)

def test_set_seed():
    """Test that set_seed correctly sets the seed."""
    set_seed(123)
    assert get_seed() == 123
    assert random.random() is not None  # Should not raise

def test_seed_reproducibility():
    """Test that the same seed produces the same random numbers."""
    set_seed(42)
    first_run = [random.random() for _ in range(5)]
    
    set_seed(42)
    second_run = [random.random() for _ in range(5)]
    
    assert first_run == second_run

def test_generate_seed_from_string():
    """Test deterministic seed generation from string."""
    seed1 = generate_seed_from_string("test_string")
    seed2 = generate_seed_from_string("test_string")
    seed3 = generate_seed_from_string("different_string")
    
    assert seed1 == seed2
    assert seed1 != seed3
    assert isinstance(seed1, int)

def test_reset_seed():
    """Test that reset_seed clears the seed."""
    set_seed(999)
    assert get_seed() == 999
    
    reset_seed()
    assert get_seed() is None

def test_set_deterministic_mode():
    """Test deterministic mode setup."""
    set_deterministic_mode(777)
    assert get_seed() == 777

def test_environment_variable_set():
    """Test that PYTHONHASHSEED is set."""
    set_seed(42)
    assert os.environ.get('PYTHONHASHSEED') == '42'
