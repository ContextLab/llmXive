import pytest
import numpy as np
from code.utils import benjamini_hochberg_fdr

def test_benjamini_hochberg_fdr_basic():
    """Test basic FDR correction functionality."""
    p_values = [0.01, 0.04, 0.03, 0.001, 0.02]
    adjusted = benjamini_hochberg_fdr(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= x <= 1 for x in adjusted)
    
    # Check that adjusted values are monotonic with respect to original ranks
    # (simplified check: adjusted values should generally be >= original)
    assert all(adj >= orig for adj, orig in zip(adjusted, p_values))

def test_benjamini_hochberg_fdr_empty():
    """Test FDR correction with empty list."""
    adjusted = benjamini_hochberg_fdr([])
    assert len(adjusted) == 0

def test_benjamini_hochberg_fdr_all_significant():
    """Test with very small p-values."""
    p_values = [0.0001, 0.0002, 0.0003]
    adjusted = benjamini_hochberg_fdr(p_values)
    
    # Even with adjustment, these should likely remain significant (< 0.05)
    assert all(adj < 0.05 for adj in adjusted)

def test_benjamini_hochberg_fdr_all_insignificant():
    """Test with large p-values."""
    p_values = [0.5, 0.6, 0.7]
    adjusted = benjamini_hochberg_fdr(p_values)
    
    # Adjusted values should be large
    assert all(adj > 0.5 for adj in adjusted)
