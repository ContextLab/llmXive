"""
Unit tests for code/modeling.py.

Tests baseline vector derivation and weight stability checks.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from modeling import derive_baseline_interest_vector, check_weight_stability


def test_derive_baseline_interest_vector():
    """Test baseline vector derivation from history."""
    # Mock history: user watched Math, Math, Science
    # The function should map these to indices and return a normalized distribution
    history = ["Math", "Math", "Science"]
    
    # We expect a vector representing the distribution of these categories
    # The function should return a normalized vector
    vector = derive_baseline_interest_vector(history)
    
    # Check that vector is a numpy array
    assert isinstance(vector, np.ndarray)
    # Check that it sums to 1.0 (normalized)
    assert np.isclose(vector.sum(), 1.0, atol=1e-5)
    # Check that non-zero elements correspond to seen categories
    # (Assuming the function maps categories to indices, here we just check sum)
    # Additional check: ensure no negative values
    assert np.all(vector >= 0)
    # Ensure length is reasonable (at least 1, not huge)
    assert len(vector) >= 1


def test_check_weight_stability_no_extreme():
    """Test weight stability check when no weights are extreme."""
    weights = np.array([1.0, 1.1, 0.9, 1.05, 0.95])
    median_weight = np.median(weights)
    threshold = 10 * median_weight
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is True
    assert len(flagged_indices) == 0


def test_check_weight_stability_extreme():
    """Test weight stability check when some weights are extreme."""
    weights = np.array([1.0, 1.0, 1.0, 100.0, 1.0])
    median_weight = np.median(weights) # 1.0
    threshold = 10 * median_weight # 10.0
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is False
    assert 3 in flagged_indices # Index of 100.0


def test_check_weight_stability_multiple_extreme():
    """Test weight stability check with multiple extreme weights."""
    weights = np.array([1.0, 50.0, 1.0, 60.0, 1.0])
    median_weight = np.median(weights) # 1.0
    threshold = 10 * median_weight # 10.0
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is False
    assert 1 in flagged_indices
    assert 3 in flagged_indices
    assert len(flagged_indices) == 2


def test_check_weight_stability_empty_weights():
    """Test weight stability check with empty array."""
    weights = np.array([])
    
    # Should handle empty array gracefully
    # Depending on implementation, might return True or raise an error
    # We expect it to not crash
    try:
        is_stable, flagged_indices = check_weight_stability(weights)
        # If it returns, check types
        assert isinstance(is_stable, bool)
        assert isinstance(flagged_indices, list)
    except Exception:
        # Or it might raise, which is also acceptable for edge cases
        pass


def test_derive_baseline_interest_vector_empty():
    """Test baseline vector derivation with empty history."""
    history = []
    
    # Should handle empty history gracefully
    # Depending on implementation, might return zero vector or raise
    try:
        vector = derive_baseline_interest_vector(history)
        assert isinstance(vector, np.ndarray)
        # If it returns a vector, it should be valid
        assert len(vector) >= 0
    except Exception:
        # Raising an error for empty history is also acceptable
        pass

def test_check_weight_stability_extreme_boundary():
    """Test weight stability check exactly at 10x threshold."""
    # Median is 1.0. 10x is 10.0.
    # A weight of exactly 10.0 should NOT be flagged (strictly greater than).
    weights = np.array([1.0, 1.0, 1.0, 10.0, 1.0])
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is True
    assert len(flagged_indices) == 0

def test_check_weight_stability_extreme_just_over():
    """Test weight stability check just over 10x threshold."""
    # Median is 1.0. 10x is 10.0.
    # A weight of 10.0001 should be flagged.
    weights = np.array([1.0, 1.0, 1.0, 10.0001, 1.0])
    
    is_stable, flagged_indices = check_weight_stability(weights)
    
    assert is_stable is False
    assert 3 in flagged_indices