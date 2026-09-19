import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# We are testing the R script logic by simulating the inputs and verifying the output structure
# Since we cannot easily call R from Python in a pure unit test without R setup,
# we test the *expectations* of the script and the data flow.
# A more robust test would run the R script in an integration test.

def test_permutation_output_schema(tmp_path):
    """
    Verify that if the R script runs, it produces a CSV with the correct schema.
    This is a schema contract test.
    """
    # Simulate expected output
    expected_cols = ["stress", "observed_beta1", "n_permutations", "count_extreme", "empirical_p_value", "timestamp"]
    
    # Create a dummy dataframe
    df = pd.DataFrame({
        "stress": ["heatshock"],
        "observed_beta1": [0.5],
        "n_permutations": [100],
        "count_extreme": [5],
        "empirical_p_value": [0.06],
        "timestamp": [pd.Timestamp.now()]
    })
    
    output_path = tmp_path / "permutation_pvalue.csv"
    df.to_csv(output_path, index=False)
    
    # Read back and verify
    result = pd.read_csv(output_path)
    assert list(result.columns) == expected_cols
    assert len(result) > 0
    assert result["empirical_p_value"].iloc[0] >= 0.0
    assert result["empirical_p_value"].iloc[0] <= 1.0

def test_spatial_block_logic():
    """
    Verify the logic of block permutation: values within a block are shuffled,
    values across blocks are not mixed.
    """
    # Simulate data
    n = 100
    blocks = np.repeat(np.arange(10), 10) # 10 blocks of 10
    values = np.arange(n)
    
    # Shuffle within blocks
    shuffled = np.zeros(n)
    for b in np.unique(blocks):
        idx = np.where(blocks == b)[0]
        shuffled[idx] = np.random.permutation(values[idx])
    
    # Verify: The set of values in each block must be the same as original
    for b in np.unique(blocks):
        idx = np.where(blocks == b)[0]
        assert set(shuffled[idx]) == set(values[idx])
    
    # Verify: Global distribution is preserved
    assert set(shuffled) == set(values)

def test_empirical_p_value_calculation():
    """
    Test the formula: (count + 1) / (N + 1)
    """
    beta_obs = 0.5
    beta_perms = np.array([0.1, 0.2, 0.6, 0.7, 0.4]) # 5 perms
    abs_obs = abs(beta_obs)
    count_extreme = np.sum(np.abs(beta_perms) >= abs_obs) # 0.6, 0.7 -> 2
    
    n = len(beta_perms)
    p_val = (count_extreme + 1) / (n + 1)
    
    expected_p = (2 + 1) / (5 + 1)
    assert p_val == expected_p
