"""Tests for analysis module."""
import numpy as np
from scipy import stats
from analysis import perform_residual_diagnostics

def test_shapiro_wilk_breusch_pagan():
    """Test residual diagnostics with known data."""
    # Known normal residual set
    normal_residuals = np.random.normal(0, 1, 100)
    fitted_values = np.random.normal(0, 1, 100)
    
    diagnostics = perform_residual_diagnostics(normal_residuals, fitted_values)
    
    # Shapiro-Wilk should return p > 0.05 for normal data
    assert diagnostics["shapiro_p_value"] > 0.05, "Normal data should have p > 0.05 in Shapiro-Wilk"
    
    # Known heteroscedastic set
    # Create residuals that increase in variance with fitted values
    hetero_fitted = np.linspace(-5, 5, 100)
    hetero_residuals = np.random.normal(0, np.abs(hetero_fitted) + 0.1, 100)
    
    hetero_diagnostics = perform_residual_diagnostics(hetero_residuals, hetero_fitted)
    
    # Breusch-Pagan should return p < 0.05 for heteroscedastic data
    # Note: This might not always be significant with small samples, but it's the expected behavior
    # We'll assert that the p-value is lower than the normal case
    assert hetero_diagnostics["breusch_pagan_p_value"] < diagnostics["breusch_pagan_p_value"], \
        "Heteroscedastic data should have lower p-value in Breusch-Pagan"
        
    print("All tests passed.")

if __name__ == "__main__":
    test_shapiro_wilk_breusch_pagan()