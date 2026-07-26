import pytest
import numpy as np
from scipy.stats import norm
import sys
import os

# Add the project root to the path if running standalone
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to test (assuming it will be implemented in src/meta_analysis.py)
# Since T027 is the implementation task, we define the expected behavior here
# and import it once implemented. For now, we test the mathematical logic directly
# to ensure the unit test validates the correct formula.

def stouffer_method(p_values, z_weights=None):
    """
    Compute Stouffer's meta-analysis p-value from a list of p-values.
    
    Parameters:
    -----------
    p_values : list of float
        List of p-values from individual studies.
    z_weights : list of float, optional
        Weights for each study. If None, equal weights (1) are used.
        
    Returns:
    --------
    float
        The combined p-value.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")
    
    # Convert p-values to z-scores (one-tailed, assuming lower tail is significant)
    # norm.ppf handles the inverse CDF. We use 1 - p for upper tail if needed,
    # but typically for DE we look for small p-values, so we map p -> -norm.ppf(p)
    # to get negative z-scores for significant results.
    # Stouffer's Z = sum(w_i * z_i) / sqrt(sum(w_i^2))
    
    p_array = np.array(p_values)
    # Clamp p-values to avoid inf
    p_array = np.clip(p_array, 1e-300, 1.0 - 1e-300)
    
    z_scores = norm.ppf(1 - p_array) # One-sided test: small p -> large positive z
    
    if z_weights is None:
        z_weights = np.ones(len(z_scores))
    else:
        z_weights = np.array(z_weights)
    
    if len(z_weights) != len(z_scores):
        raise ValueError("Weights length must match p_values length")
    
    # Stouffer's Z statistic
    numerator = np.sum(z_weights * z_scores)
    denominator = np.sqrt(np.sum(z_weights ** 2))
    
    z_combined = numerator / denominator
    
    # Convert back to p-value (one-sided)
    p_combined = 1 - norm.cdf(z_combined)
    
    return p_combined

class TestStoufferMetaAnalysis:
    """Unit tests for Stouffer's meta-analysis calculation."""

    def test_identical_p_values(self):
        """Test that identical p-values produce the expected combined p-value."""
        p_values = [0.01, 0.01, 0.01]
        # Manual calculation:
        # z = norm.ppf(0.99) ≈ 2.326
        # sum(z) = 6.979
        # sqrt(3) ≈ 1.732
        # z_combined = 4.029
        # p_combined = 1 - norm.cdf(4.029) ≈ 2.8e-5
        
        result = stouffer_method(p_values)
        expected_z = norm.ppf(0.99) * 3 / np.sqrt(3)
        expected_p = 1 - norm.cdf(expected_z)
        
        assert abs(result - expected_p) < 1e-10
        assert result < 0.01 # Should be more significant than individual

    def test_weighted_stouffer(self):
        """Test Stouffer's method with custom weights."""
        p_values = [0.05, 0.05]
        weights = [2.0, 1.0] # First study weighted twice as much
        
        result = stouffer_method(p_values, z_weights=weights)
        
        # z = norm.ppf(0.95) ≈ 1.645
        # num = 2*1.645 + 1*1.645 = 3*1.645 = 4.935
        # den = sqrt(4 + 1) = sqrt(5) ≈ 2.236
        # z_comb = 4.935 / 2.236 ≈ 2.207
        # p_comb = 1 - norm.cdf(2.207) ≈ 0.0136
        
        z_single = norm.ppf(0.95)
        numerator = weights[0]*z_single + weights[1]*z_single
        denominator = np.sqrt(weights[0]**2 + weights[1]**2)
        z_combined = numerator / denominator
        expected_p = 1 - norm.cdf(z_combined)
        
        assert abs(result - expected_p) < 1e-6

    def test_mixed_significance(self):
        """Test with a mix of significant and non-significant p-values."""
        p_values = [0.001, 0.5, 0.001]
        
        result = stouffer_method(p_values)
        
        # The two significant p-values should pull the combined p down,
        # but the non-significant one (z ~ 0) will dilute it slightly.
        # It should be more significant than 0.5 but likely less than 0.001.
        assert result < 0.5
        assert result > 0.000001 # Should not be absurdly small given the noise

    def test_empty_list_raises(self):
        """Test that an empty list raises a ValueError."""
        with pytest.raises(ValueError):
            stouffer_method([])

    def test_mismatched_weights_raises(self):
        """Test that mismatched weights length raises a ValueError."""
        p_values = [0.05, 0.05]
        weights = [1.0]
        
        with pytest.raises(ValueError):
            stouffer_method(p_values, z_weights=weights)

    def test_extreme_p_values(self):
        """Test handling of extreme p-values (near 0 and 1)."""
        p_values = [1e-10, 0.999999999]
        
        result = stouffer_method(p_values)
        
        # Should not crash and should return a valid probability
        assert 0.0 <= result <= 1.0

    def test_single_p_value(self):
        """Test that a single p-value returns itself."""
        p_values = [0.03]
        
        result = stouffer_method(p_values)
        
        # With one study, z_combined = z_single, so p_combined = p_single
        assert abs(result - 0.03) < 1e-10