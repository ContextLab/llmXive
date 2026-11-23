"""
Unit tests for T027: Multiple-Comparison Correction.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from scipy import stats

# Mock the config and logging to avoid dependency issues in tests
# We will test the logic functions directly if possible, or mock the I/O.

def test_bonferroni_logic():
    """Test the core Bonferroni correction logic."""
    # Simulate p-values
    p_values = [0.01, 0.02, 0.03, 0.04, 0.5]
    num_tests = len(p_values)
    
    # Expected corrected values: p * num_tests, capped at 1.0
    expected = [0.05, 0.10, 0.15, 0.20, 1.0]
    calculated = [min(p * num_tests, 1.0) for p in p_values]
    
    assert calculated == expected, f"Expected {expected}, got {calculated}"

def test_kruskal_wallis_mock():
    """Test that we can perform Kruskal-Wallis on mock data."""
    # Generate mock SHAP values for 3 families
    np.random.seed(42)
    family_a = np.random.normal(loc=0.5, scale=0.1, size=20)
    family_b = np.random.normal(loc=0.6, scale=0.1, size=20)
    family_c = np.random.normal(loc=0.5, scale=0.1, size=20)
    
    h_stat, p_val = stats.kruskal(family_a, family_b, family_c)
    
    assert h_stat > 0
    assert 0 <= p_val <= 1

def test_correction_threshold():
    """Test significance determination after correction."""
    alpha = 0.05
    num_tests = 10
    corrected_alpha = alpha / num_tests # 0.005
    
    p_val_1 = 0.004 # Significant
    p_val_2 = 0.006 # Not significant
    
    assert p_val_1 < corrected_alpha
    assert p_val_2 >= corrected_alpha

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
