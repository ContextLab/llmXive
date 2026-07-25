"""
Unit tests for plotting functions.
"""
import pytest
import numpy as np
from code.plot_qq import generate_qq_plot

def test_qq_plot_generation():
    """Test that QQ-plot generation does not crash."""
    np.random.seed(42)
    pvals = np.random.rand(100)
    
    fig = generate_qq_plot(pvals, reference="uniform")
    
    assert fig is not None
