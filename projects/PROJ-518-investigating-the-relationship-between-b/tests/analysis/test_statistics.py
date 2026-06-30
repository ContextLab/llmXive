"""
Tests for statistics module.
"""
import numpy as np
import pytest
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.statistics import fit_regression, RegressionResult

class TestFitRegression:
    """Test the fit_regression function."""
    
    def test_fit_regression_basic(self):
        """Test basic regression fitting with mock data."""
        n_samples = 50
        
        # Create mock data with known relationship
        np.random.seed(42)
        flexibility = np.random.randn(n_samples)
        age = np.random.randint(18, 65, n_samples)
        sex = np.random.randint(0, 2, n_samples)
        education = np.random.randint(12, 20, n_samples)
        static_strength = np.random.randn(n_samples)
        
        # Create creativity with some correlation to flexibility
        creativity = 0.5 * flexibility + 0.1 * age - 0.2 * sex + 0.05 * education + 0.3 * static_strength + np.random.randn(n_samples) * 0.5
        
        covariates = {
            'age': age,
            'sex': sex,
            'education': education,
            'static_connectivity_strength': static_strength
        }
        
        result = fit_regression(flexibility, creativity, covariates)
        
        # Check result type
        assert isinstance(result, RegressionResult)
        
        # Check that r and p are valid numbers
        assert isinstance(result.r, float)
        assert isinstance(result.p, float)
        assert isinstance(result.r_squared, float)
        
        # Check parameter dict has expected keys
        expected_keys = ['intercept', 'flexibility', 'age', 'sex', 'education', 'static_connectivity_strength']
        for key in expected_keys:
            assert key in result.params
        
        # Check that r_squared is between 0 and 1
        assert 0 <= result.r_squared <= 1
        
        # Check that p-value is between 0 and 1
        assert 0 <= result.p <= 1
    
    def test_fit_regression_mismatched_lengths(self):
        """Test that mismatched lengths raise ValueError."""
        flexibility = np.array([1, 2, 3])
        creativity = np.array([1, 2])  # Different length
        covariates = {
            'age': np.array([1, 2, 3]),
            'sex': np.array([0, 1, 0]),
            'education': np.array([12, 16, 18]),
            'static_connectivity_strength': np.array([0.1, 0.2, 0.3])
        }
        
        with pytest.raises(ValueError, match="must have the same length"):
            fit_regression(flexibility, creativity, covariates)
    
    def test_fit_regression_missing_covariate(self):
        """Test that missing covariate raises ValueError."""
        flexibility = np.array([1, 2, 3])
        creativity = np.array([1, 2, 3])
        covariates = {
            'age': np.array([1, 2, 3]),
            'sex': np.array([0, 1, 0]),
            # Missing 'education' and 'static_connectivity_strength'
        }
        
        with pytest.raises(ValueError, match="Missing required covariate"):
            fit_regression(flexibility, creativity, covariates)
    
    def test_fit_regression_covariate_length_mismatch(self):
        """Test that covariate with wrong length raises ValueError."""
        flexibility = np.array([1, 2, 3])
        creativity = np.array([1, 2, 3])
        covariates = {
            'age': np.array([1, 2, 3]),
            'sex': np.array([0, 1, 0]),
            'education': np.array([12, 16]),  # Wrong length
            'static_connectivity_strength': np.array([0.1, 0.2, 0.3])
        }
        
        with pytest.raises(ValueError, match="mismatched length"):
            fit_regression(flexibility, creativity, covariates)
    
    def test_regression_with_perfect_correlation(self):
        """Test regression with perfect linear relationship."""
        n_samples = 20
        flexibility = np.linspace(0, 1, n_samples)
        creativity = 2 * flexibility + 1  # Perfect linear relationship
        covariates = {
            'age': np.zeros(n_samples),
            'sex': np.zeros(n_samples),
            'education': np.zeros(n_samples),
            'static_connectivity_strength': np.zeros(n_samples)
        }
        
        result = fit_regression(flexibility, creativity, covariates)
        
        # With perfect correlation, r should be 1.0
        assert abs(result.r - 1.0) < 1e-10
        # p-value should be very small (essentially 0)
        assert result.p < 0.001
        # R-squared should be 1.0
        assert abs(result.r_squared - 1.0) < 1e-10
        # The flexibility coefficient should be close to 2
        assert abs(result.params['flexibility'] - 2.0) < 0.1
        # The intercept should be close to 1
        assert abs(result.params['intercept'] - 1.0) < 0.1
