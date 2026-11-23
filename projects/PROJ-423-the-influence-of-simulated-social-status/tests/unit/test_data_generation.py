"""
Unit tests for data generation determinism.

Verifies that the simulation produces identical results given the same seed.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code'))

from simulate import generate_synthetic_data
from config import get_random_seed

def test_deterministic_output():
    """Verify that fixed seed produces identical output."""
    # Retrieve the seed from the project configuration
    seed = get_random_seed()
    
    # Run generation twice with the exact same seed
    df1 = generate_synthetic_data(seed=seed)
    df2 = generate_synthetic_data(seed=seed)
    
    # Assert that the DataFrames are identical in content, types, and index
    pd.testing.assert_frame_equal(df1, df2)

def test_random_seed_effect():
    """Verify that different seeds produce different output."""
    seed1 = 42
    seed2 = 123
    
    # Generate data with two different seeds
    df1 = generate_synthetic_data(seed=seed1)
    df2 = generate_synthetic_data(seed=seed2)
    
    # They should not be equal (probability of collision is negligible)
    # We check the hash of the underlying data to ensure distinctness
    hash1 = pd.util.hash_pandas_object(df1).sum()
    hash2 = pd.util.hash_pandas_object(df2).sum()
    
    assert hash1 != hash2, "Different seeds should produce different data"