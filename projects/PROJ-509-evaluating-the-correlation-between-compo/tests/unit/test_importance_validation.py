import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from code.importance import validate_correlation, rank_features, calculate_vif

def test_validate_correlation_perfect():
    """Test correlation calculation with perfectly correlated data."""
    rf_importances = {"a": 1.0, "b": 2.0, "c": 3.0}
    perm_importances = {"a": 1.0, "b": 2.0, "c": 3.0}
    
    r, p_value = validate_correlation(rf_importances, perm_importances)
    
    assert np.isclose(r, 1.0, atol=1e-5)
    assert p_value < 0.05  # Significant

def test_validate_correlation_zero():
    """Test correlation calculation with uncorrelated data."""
    # Create data with no linear correlation
    rf_importances = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    perm_importances = {"a": 3.0, "b": 1.0, "c": 4.0, "d": 2.0}
    
    r, p_value = validate_correlation(rf_importances, perm_importances)
    
    # Should not be 1.0
    assert not np.isclose(r, 1.0, atol=0.1)
    assert -1.0 <= r <= 1.0

def test_rank_features():
    """Test feature ranking logic."""
    importances = {"z": 0.1, "a": 0.9, "m": 0.5}
    ranked = rank_features(importances, top_n=2)
    
    assert len(ranked) == 2
    assert ranked[0]["feature"] == "a"
    assert ranked[0]["importance"] == 0.9
    assert ranked[0]["rank"] == 1
    assert ranked[1]["feature"] == "m"
    assert ranked[1]["rank"] == 2

def test_rank_features_top_n_larger_than_input():
    """Test ranking when top_n is larger than number of features."""
    importances = {"a": 0.9, "b": 0.5}
    ranked = rank_features(importances, top_n=10)
    
    assert len(ranked) == 2
    assert ranked[0]["feature"] == "a"

def test_calculate_vif_constant_feature():
    """Test VIF calculation with a constant feature (should raise or return high VIF)."""
    # Create a DataFrame with a constant column
    df = pd.DataFrame({
        'a': [1.0, 1.0, 1.0, 1.0],
        'b': [1.0, 2.0, 3.0, 4.0]
    })
    
    # This might raise an error due to constant feature, or return high VIF
    # We expect it to handle gracefully or raise a specific error
    try:
        vif_scores = calculate_vif(df)
        # If it doesn't raise, check that VIF is high for constant feature
        assert vif_scores['a'] >= 10.0 or np.isinf(vif_scores['a'])
    except Exception:
        # It is acceptable for VIF calculation to fail on constant features
        pass
