"""
T018: Unit test for Benjamini-Hochberg FDR correction.

This module tests the implementation of the Benjamini-Hochberg procedure
for controlling the False Discovery Rate in multiple hypothesis testing.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add code dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from utils.fdr_correction import calculate_q_values, apply_fdr_correction

def test_calculate_q_values_basic():
    """Test basic BH calculation on a known set."""
    # Simple case: 5 p-values
    p_vals = np.array([0.01, 0.04, 0.03, 0.20, 0.15])
    q_vals = calculate_q_values(p_vals)
    
    # Expected manual calculation:
    # Sorted p: [0.01, 0.03, 0.04, 0.15, 0.20]
    # Ranks (1-indexed): [1, 2, 3, 4, 5]
    # n = 5
    # BH raw: [5*0.01/1, 5*0.03/2, 5*0.04/3, 5*0.15/4, 5*0.20/5]
    #       = [0.05, 0.075, 0.0666..., 0.1875, 0.20]
    # Monotonicity enforcement (from largest to smallest rank):
    #   q[4] = 0.20
    #   q[3] = min(0.1875, 0.20) = 0.1875
    #   q[2] = min(0.0666, 0.1875) = 0.0666...
    #   q[1] = min(0.075, 0.0666) = 0.0666...
    #   q[0] = min(0.05, 0.0666) = 0.05
    # Sorted q: [0.05, 0.0666..., 0.0666..., 0.1875, 0.20]
    # Map back to original order:
    # p=0.01 (idx 0) -> 0.05
    # p=0.04 (idx 1, rank 3) -> 0.0666...
    # p=0.03 (idx 2, rank 2) -> 0.0666...
    # p=0.20 (idx 3, rank 5) -> 0.20
    # p=0.15 (idx 4, rank 4) -> 0.1875
    
    assert len(q_vals) == len(p_vals)
    assert all(q >= 0 for q in q_vals)
    assert all(q <= 1 for q in q_vals)
    
    # Check specific value for the smallest p-value
    # The smallest p-value (0.01) should have q = 0.05 (5 * 0.01)
    assert np.isclose(q_vals[0], 0.05), f"Expected 0.05 for p=0.01, got {q_vals[0]}"
    
    # Check the value for p=0.04 (rank 3) -> 5*0.04/3 = 0.0666...
    assert np.isclose(q_vals[1], 5 * 0.04 / 3), f"Expected ~0.0666 for p=0.04, got {q_vals[1]}"

def test_apply_fdr_correction_dataframe():
    """Test applying FDR to a DataFrame."""
    df = pd.DataFrame({
        'SNP': ['rs1', 'rs2', 'rs3'],
        'P': [0.01, 0.05, 0.10]
    })
    result = apply_fdr_correction(df)
    
    assert 'q_value' in result.columns
    assert len(result) == 3
    
    # Check that q-values are monotonically non-decreasing with P
    # Sort by P to check the monotonicity property
    sorted_result = result.sort_values('P').reset_index(drop=True)
    diffs = sorted_result['q_value'].diff().fillna(0)
    assert all(diffs >= -1e-9), "Q-values should be monotonically non-decreasing with P"

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['SNP', 'P'])
    result = apply_fdr_correction(df)
    assert 'q_value' in result.columns
    assert len(result) == 0

def test_all_significant():
    """Test case where all p-values are very small."""
    p_vals = np.array([0.0001, 0.0002, 0.0003])
    q_vals = calculate_q_values(p_vals)
    
    # All q-values should be small and <= 1
    assert all(q <= 1 for q in q_vals)
    assert all(q >= 0 for q in q_vals)
    # The smallest p-value should have the smallest q-value
    assert q_vals[0] <= q_vals[1] <= q_vals[2]

def test_all_non_significant():
    """Test case where all p-values are large."""
    p_vals = np.array([0.8, 0.9, 0.95])
    q_vals = calculate_q_values(p_vals)
    
    # All q-values should be large (likely > 0.05)
    assert all(q >= 0 for q in q_vals)
    assert all(q <= 1 for q in q_vals)

def test_monotonicity_enforcement():
    """Test that monotonicity is enforced correctly."""
    # Create a case where raw BH would violate monotonicity
    # p-values: 0.1, 0.05 (rank 2), 0.01 (rank 1)
    # Raw BH: 3*0.1/3=0.1, 3*0.05/2=0.075, 3*0.01/1=0.03
    # This is already monotonic. Let's try:
    # p: 0.04 (rank 2), 0.01 (rank 1), 0.15 (rank 3)
    # Raw: 3*0.04/2=0.06, 3*0.01/1=0.03, 3*0.15/3=0.15
    # Sorted by p: 0.01 (r1), 0.04 (r2), 0.15 (r3)
    # Raw q: 0.03, 0.06, 0.15 (monotonic)
    
    # Harder case:
    # p: 0.05 (r2), 0.02 (r1), 0.06 (r3)
    # Raw: 3*0.05/2=0.075, 3*0.02/1=0.06, 3*0.06/3=0.06
    # Sorted: 0.02 (0.06), 0.05 (0.075), 0.06 (0.06) -> 0.06 < 0.075 but 0.06 < 0.06 is false.
    # Wait, 0.06 (rank 3) vs 0.075 (rank 2). 0.06 < 0.075.
    # Monotonicity check from bottom:
    # q[2] (rank 3) = 0.06
    # q[1] (rank 2) = min(0.075, 0.06) = 0.06
    # q[0] (rank 1) = min(0.06, 0.06) = 0.06
    # So all become 0.06.
    
    p_vals = np.array([0.05, 0.02, 0.06])
    q_vals = calculate_q_values(p_vals)
    
    # Check that q-values are non-decreasing when sorted by p-value
    sorted_indices = np.argsort(p_vals)
    sorted_q = q_vals[sorted_indices]
    assert all(sorted_q[i] <= sorted_q[i+1] + 1e-9 for i in range(len(sorted_q)-1)), \
        "Q-values must be monotonically non-decreasing with respect to p-values"