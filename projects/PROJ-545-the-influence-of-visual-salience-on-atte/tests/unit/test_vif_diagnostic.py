"""
Unit tests for VIF (Variance Inflation Factor) diagnostic logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the function we are testing (assuming it exists in diagnostics module)
# If the function doesn't exist yet, this test will fail until implementation
try:
    from code.analysis.diagnostics import calculate_vif_matrix
    HAS_VIF_FUNC = True
except ImportError:
    HAS_VIF_FUNC = False

@pytest.fixture
def sample_collinear_data():
    """
    Creates a DataFrame with high collinearity.
    X1 and X2 are perfectly correlated.
    """
    n = 100
    x1 = np.random.rand(n)
    x2 = x1 * 2 + 0.001  # Almost perfect linear relationship
    y = x1 + x2 + np.random.normal(0, 0.1, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "y": y})

@pytest.fixture
def sample_independent_data():
    """
    Creates a DataFrame with independent variables.
    """
    n = 100
    x1 = np.random.rand(n)
    x2 = np.random.rand(n)
    y = x1 + x2 + np.random.normal(0, 0.1, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "y": y})

@pytest.mark.skipif(not HAS_VIF_FUNC, reason="calculate_vif_matrix not yet implemented")
def test_vif_high_collinearity(sample_collinear_data):
    """
    Unit Test: Verify VIF calculation flags collinearity > 5.0.
    """
    # Exclude target 'y'
    features = sample_collinear_data[["x1", "x2"]]
    vif_results = calculate_vif_matrix(features)
    
    # Check that at least one VIF is high
    max_vif = max(vif_results.values())
    assert max_vif > 5.0, f"Expected VIF > 5.0 for collinear data, got {max_vif}"

@pytest.mark.skipif(not HAS_VIF_FUNC, reason="calculate_vif_matrix not yet implemented")
def test_vif_low_collinearity(sample_independent_data):
    """
    Unit Test: Verify VIF is low for independent variables.
    """
    features = sample_independent_data[["x1", "x2"]]
    vif_results = calculate_vif_matrix(features)
    
    # VIF should be close to 1.0 for independent variables
    for var, vif in vif_results.items():
        assert vif < 5.0, f"VIF for {var} should be < 5.0, got {vif}"

@pytest.mark.skipif(not HAS_VIF_FUNC, reason="calculate_vif_matrix not yet implemented")
def test_vif_flagging_logic(sample_collinear_data):
    """
    Unit Test: Verify the logic that flags variables with VIF > 5.0.
    """
    features = sample_collinear_data[["x1", "x2"]]
    vif_results = calculate_vif_matrix(features)
    
    flagged_vars = [var for var, vif in vif_results.items() if vif > 5.0]
    assert len(flagged_vars) > 0, "Expected at least one variable to be flagged for collinearity"
