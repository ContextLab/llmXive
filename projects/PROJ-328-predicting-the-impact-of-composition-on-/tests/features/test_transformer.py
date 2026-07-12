"""
Tests for the CLR transformer.
"""
import pytest
import numpy as np
from features.transformer import CLRTransformer


class TestCLRTransformer:
    """Test cases for CLRTransformer class."""
    
    def test_fit_transform_basic(self):
        """Test basic fit and transform functionality."""
        transformer = CLRTransformer()
        # Simple composition: [0.5, 0.3, 0.2] sums to 1.0
        X = np.array([[0.5, 0.3, 0.2]])
        
        result, weights = transformer.fit_transform(X)
        
        assert result.shape == (1, 3)
        assert weights.shape == (1,)
        assert np.allclose(np.sum(np.exp(result), axis=1), 1.0, atol=1e-5)
    
    def test_transform_multiple_samples(self):
        """Test transformation of multiple samples."""
        transformer = CLRTransformer()
        X = np.array([
            [0.5, 0.3, 0.2],
            [0.1, 0.8, 0.1],
            [0.33, 0.33, 0.34]
        ])
        
        result, weights = transformer.transform(X)
        
        assert result.shape == (3, 3)
        assert weights.shape == (3,)
    
    def test_inverse_transform(self):
        """Test inverse transformation recovers original composition."""
        transformer = CLRTransformer()
        X = np.array([[0.5, 0.3, 0.2]])
        
        clr_result, _ = transformer.fit_transform(X)
        recovered = transformer.inverse_transform(clr_result)
        
        # Should recover approximately (due to numerical precision)
        assert np.allclose(recovered, X, atol=1e-5)
    
    def test_negative_values_error(self):
        """Test that negative values raise an error."""
        transformer = CLRTransformer()
        X = np.array([[-0.1, 0.6, 0.5]])
        
        with pytest.raises(ValueError, match="negative values"):
            transformer.transform(X)
    
    def test_zero_handling(self):
        """Test that zero values are handled with epsilon."""
        transformer = CLRTransformer(eps=1e-6)
        X = np.array([[0.0, 0.5, 0.5]])
        
        # Should not raise, but use epsilon for zero
        result, weights = transformer.transform(X)
        
        assert result.shape == (1, 3)
        assert not np.any(np.isnan(result))
    
    def test_fitted_flag(self):
        """Test that fitted flag is set correctly."""
        transformer = CLRTransformer()
        assert not transformer.fitted
        
        X = np.array([[0.5, 0.3, 0.2]])
        transformer.fit(X)
        
        assert transformer.fitted
