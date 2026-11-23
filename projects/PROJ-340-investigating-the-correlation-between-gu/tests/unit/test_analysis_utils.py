"""
Unit tests for analysis utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import check_distribution, select_correlation_method

def test_check_distribution_normal():
    """Test distribution check on normal data."""
    np.random.seed(42)
    data = pd.DataFrame({
        "value": np.random.normal(0, 1, 1000)
    })
    
    result = check_distribution(data, "value")
    assert result["is_normal"], "Normal data should pass normality test"

def test_check_distribution_skewed():
    """Test distribution check on skewed data."""
    # Log-normal data is skewed
    data = pd.DataFrame({
        "value": np.random.lognormal(0, 1, 1000)
    })
    
    result = check_distribution(data, "value")
    # Log-normal is typically not normal in Shapiro-Wilk for large N
    assert not result["is_normal"], "Skewed data should fail normality test"

def test_select_correlation_method_normal():
    """Test method selection for normal data."""
    np.random.seed(42)
    data = pd.DataFrame({
        "x": np.random.normal(0, 1, 100),
        "y": np.random.normal(0, 1, 100)
    })
    
    method = select_correlation_method(data, "x", "y")
    assert method == "pearson", "Normal data should use Pearson"

def test_select_correlation_method_non_normal():
    """Test method selection for non-normal data."""
    data = pd.DataFrame({
        "x": np.random.lognormal(0, 1, 100),
        "y": np.random.lognormal(0, 1, 100)
    })
    
    method = select_correlation_method(data, "x", "y")
    assert method == "spearman", "Non-normal data should use Spearman"
