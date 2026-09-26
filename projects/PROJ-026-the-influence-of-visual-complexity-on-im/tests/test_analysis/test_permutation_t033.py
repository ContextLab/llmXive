"""
Tests for T033: Permutation Test Implementation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.permutation import run_permutation_test, calculate_effect_size

def test_permutation_test_basic():
    """Test basic permutation test functionality with known data."""
    # Create synthetic D-scores for testing
    np.random.seed(42)
    d_scores_low = np.random.normal(0.5, 0.2, 20).tolist()
    d_scores_high = np.random.normal(0.8, 0.2, 20).tolist()
    
    result = run_permutation_test(d_scores_low, d_scores_high, n_permutations=100, seed=42)
    
    assert result["status"] == "valid"
    assert "p_value" in result
    assert "observed_stat" in result
    assert 0 <= result["p_value"] <= 1
    assert result["n_permutations"] == 100

def test_permutation_test_insufficient_samples():
    """Test permutation test with insufficient sample size."""
    d_scores_low = [0.5] * 10
    d_scores_high = [0.8] * 10
    
    result = run_permutation_test(d_scores_low, d_scores_high, n_permutations=100)
    
    assert result["status"] == "invalid"
    assert result["reason"] == "n < 15"
    assert np.isnan(result["p_value"])

def test_effect_size_calculation():
    """Test Cohen's d effect size calculation."""
    d_scores_low = [0.5, 0.6, 0.4, 0.55, 0.45]
    d_scores_high = [0.8, 0.9, 0.7, 0.85, 0.75]
    
    effect_size = calculate_effect_size(d_scores_low, d_scores_high)
    
    assert effect_size > 0
    assert isinstance(effect_size, float)

def test_permutation_reproducibility():
    """Test that permutation test is reproducible with fixed seed."""
    np.random.seed(42)
    d_scores_low = np.random.normal(0.5, 0.2, 20).tolist()
    d_scores_high = np.random.normal(0.8, 0.2, 20).tolist()
    
    result1 = run_permutation_test(d_scores_low, d_scores_high, n_permutations=100, seed=42)
    result2 = run_permutation_test(d_scores_low, d_scores_high, n_permutations=100, seed=42)
    
    assert result1["p_value"] == result2["p_value"]
    assert result1["observed_stat"] == result2["observed_stat"]
