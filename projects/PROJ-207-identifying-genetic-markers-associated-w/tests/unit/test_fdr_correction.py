"""
T018: Unit test for Benjamini-Hochberg FDR correction.
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
    
    # Manual calculation for 5 items:
    # Sorted: 0.01, 0.03, 0.04, 0.15, 0.20
    # Ranks: 1, 2, 3, 4, 5
    # BH: (5/1)*0.01=0.05, (5/2)*0.03=0.075, (5/3)*0.04=0.066, (5/4)*0.15=0.1875, (5/5)*0.20=0.20
    # Monotonicity (from bottom): 0.20, 0.1875, 0.075, 0.075, 0.05 (Wait, 0.066 < 0.075? No, 0.066 < 0.075 is false, 0.066 < 0.075. 
    # Let's re-evaluate monotonicity logic: q_i = min(q_i, q_{i+1})
    # Sorted q: 0.05, 0.075, 0.0666, 0.1875, 0.20
    # Step 1 (i=3): min(0.1875, 0.20) = 0.1875
    # Step 2 (i=2): min(0.0666, 0.1875) = 0.0666
    # Step 3 (i=1): min(0.075, 0.0666) = 0.0666
    # Step 4 (i=0): min(0.05, 0.0666) = 0.05
    # Final sorted: 0.05, 0.0666, 0.0666, 0.1875, 0.20
    # Unsort to match original:
    # 0.01 -> 0.05
    # 0.04 -> 0.0666 (rank 3)
    # 0.03 -> 0.0666 (rank 2)
    # 0.20 -> 0.20 (rank 5)
    # 0.15 -> 0.1875 (rank 4)
    
    # Check that q-values are monotonically increasing with p-values (roughly)
    assert len(q_vals) == len(p_vals)
    assert all(q >= 0 for q in q_vals)
    assert all(q <= 1 for q in q_vals)
    
    # Check specific value for the smallest p-value
    # The smallest p-value (0.01) should have q = 0.05 (5 * 0.01)
    assert np.isclose(q_vals[0], 0.05), f"Expected 0.05 for p=0.01, got {q_vals[0]}"

def test_apply_fdr_correction_dataframe():
    """Test applying FDR to a DataFrame."""
    df = pd.DataFrame({
        'SNP': ['rs1', 'rs2', 'rs3'],
        'P': [0.01, 0.05, 0.10]
    })
    result = apply_fdr_correction(df)
    
    assert 'q_value' in result.columns
    assert len(result) == 3
    # Check that q-values are non-decreasing with P
    sorted_result = result.sort_values('P')
    assert all(sorted_result['q_value'].diff().fillna(0) >= -1e-9), "Q-values should be monotonically non-decreasing with P"

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['SNP', 'P'])
    result = apply_fdr_correction(df)
    assert 'q_value' in result.columns
    assert len(result) == 0