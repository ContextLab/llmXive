import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.correlation import benjamini_hochberg

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def sample_p_values():
    """Sample p-values for testing."""
    return [0.01, 0.02, 0.03, 0.04, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]

def test_benjamini_hochberg_basic(sample_p_values):
    """Test basic BH correction functionality."""
    adjusted = benjamini_hochberg(sample_p_values)
    
    # Check that we get the same number of adjusted values
    assert len(adjusted) == len(sample_p_values)
    
    # Check that all adjusted values are between 0 and 1
    assert all(0 <= p <= 1 for p in adjusted)
    
    # Check that adjusted values are generally larger than raw values
    # (though not strictly required for all cases)
    assert all(adj >= raw for adj, raw in zip(adjusted, sample_p_values))

def test_benjamini_hochberg_monotonicity(sample_p_values):
    """Test that BH adjusted p-values maintain monotonicity."""
    adjusted = benjamini_hochberg(sample_p_values)
    
    # Sort original p-values to get corresponding adjusted values
    sorted_indices = np.argsort(sample_p_values)
    sorted_adjusted = [adjusted[i] for i in sorted_indices]
    
    # Check monotonicity (non-decreasing)
    for i in range(len(sorted_adjusted) - 1):
        assert sorted_adjusted[i] <= sorted_adjusted[i + 1]

def test_benjamini_hochberg_all_significant():
    """Test BH correction when all p-values are very small."""
    p_values = [0.001, 0.002, 0.003, 0.004, 0.005]
    adjusted = benjamini_hochberg(p_values)
    
    # All should still be significant after correction
    significant_count = sum(1 for p in adjusted if p < 0.05)
    assert significant_count == len(p_values)

def test_benjamini_hochberg_none_significant():
    """Test BH correction when no p-values are significant."""
    p_values = [0.5, 0.6, 0.7, 0.8, 0.9]
    adjusted = benjamini_hochberg(p_values)
    
    # None should be significant after correction
    significant_count = sum(1 for p in adjusted if p < 0.05)
    assert significant_count == 0

def test_benjamini_hochberg_empty_list():
    """Test BH correction with empty list."""
    adjusted = benjamini_hochberg([])
    assert adjusted == []

def test_benjamini_hochberg_single_value():
    """Test BH correction with single p-value."""
    p_values = [0.03]
    adjusted = benjamini_hochberg(p_values)
    assert len(adjusted) == 1
    assert adjusted[0] == 0.03  # Single value should remain unchanged

def test_benjamini_hochberg_duplicate_values():
    """Test BH correction with duplicate p-values."""
    p_values = [0.05, 0.05, 0.05, 0.10, 0.10]
    adjusted = benjamini_hochberg(p_values)
    
    # Check that we get the expected number of results
    assert len(adjusted) == len(p_values)
    
    # Check monotonicity
    sorted_indices = np.argsort(p_values)
    sorted_adjusted = [adjusted[i] for i in sorted_indices]
    for i in range(len(sorted_adjusted) - 1):
        assert sorted_adjusted[i] <= sorted_adjusted[i + 1]

def test_benjamini_hochberg_extreme_values():
    """Test BH correction with extreme p-values (0 and 1)."""
    p_values = [0.0, 0.5, 1.0]
    adjusted = benjamini_hochberg(p_values)
    
    # Check bounds
    assert all(0 <= p <= 1 for p in adjusted)
    
    # The smallest p-value (0) should remain 0
    sorted_indices = np.argsort(p_values)
    assert adjusted[sorted_indices[0]] == 0.0

def test_benjamini_hochberg_consistency():
    """Test that BH correction is deterministic."""
    p_values = [0.01, 0.05, 0.10, 0.20, 0.30]
    
    # Run multiple times
    result1 = benjamini_hochberg(p_values)
    result2 = benjamini_hochberg(p_values)
    
    # Results should be identical
    assert result1 == result2