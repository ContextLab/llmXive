"""
Unit tests for the configuration module (code/utils/config.py).
"""

import random
import numpy as np
import pytest

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.config import (
    set_all_seeds,
    RANDOM_SEED,
    WINDOW_LENGTHS_SEC,
    WINDOW_STEP_SEC,
    MIN_TIME_POINTS_PER_WINDOW,
    MEMORY_LIMIT_GB
)


def test_random_seeds_are_set():
    """Test that set_all_seeds correctly initializes random states."""
    # Reset seeds to a known state first
    random.seed(123)
    np.random.seed(123)

    # Generate a number to ensure state is "dirty"
    _ = random.random()
    _ = np.random.rand()

    # Apply our seeds
    set_all_seeds(999)

    # Check Python random
    val1 = random.random()
    val2 = random.random()

    # Reset and re-seed to verify reproducibility
    set_all_seeds(999)
    val3 = random.random()
    val4 = random.random()

    assert val1 == val3
    assert val2 == val4

    # Check NumPy random
    set_all_seeds(999)
    arr1 = np.random.rand(5)

    set_all_seeds(999)
    arr2 = np.random.rand(5)

    assert np.array_equal(arr1, arr2)


def test_window_parameters_defined():
    """Test that required window parameters are defined and sensible."""
    assert isinstance(WINDOW_LENGTHS_SEC, list)
    assert 60 in WINDOW_LENGTHS_SEC
    assert 90 in WINDOW_LENGTHS_SEC
    # Check for intermediate values
    assert 45 in WINDOW_LENGTHS_SEC
    assert 75 in WINDOW_LENGTHS_SEC
    
    # Check ordering (should be sorted)
    assert WINDOW_LENGTHS_SEC == sorted(WINDOW_LENGTHS_SEC)

    assert isinstance(WINDOW_STEP_SEC, int)
    assert WINDOW_STEP_SEC > 0
    
    assert isinstance(MIN_TIME_POINTS_PER_WINDOW, int)
    assert MIN_TIME_POINTS_PER_WINDOW > 0


def test_memory_limit_defined():
    """Test that memory limit is defined correctly."""
    assert isinstance(MEMORY_LIMIT_GB, float)
    assert MEMORY_LIMIT_GB > 0