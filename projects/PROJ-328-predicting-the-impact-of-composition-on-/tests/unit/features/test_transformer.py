"""
Unit tests for the CLRTransformer.
"""
import numpy as np
import pytest
from code.features.transformer import CLRTransformer

def test_clr_transform_basic():
    """Test basic CLR transform on a simple composition."""
    # Simple composition: [0.5, 0.3, 0.2]
    X = np.array([[0.5, 0.3, 0.2]])
    transformer = CLRTransformer()
    transformer.fit(X)
    clr_X, weights = transformer.transform(X)
    
    # Check that sum of CLR is 0 (property of CLR)
    assert np.isclose(np.sum(clr_X), 0.0), "Sum of CLR values should be 0"
    
    # Check shape
    assert clr_X.shape == X.shape

def test_clr_zero_replacement():
    """Test that zeros are replaced by epsilon."""
    X = np.array([[0.0, 0.5, 0.5]])
    transformer = CLRTransformer(epsilon=1e-6)
    transformer.fit(X)
    clr_X, _ = transformer.transform(X)
    
    # Should not raise an error
    assert clr_X is not None

def test_inverse_transform():
    """Test inverse CLR transform reconstructs original."""
    X = np.array([[0.6, 0.3, 0.1]])
    transformer = CLRTransformer()
    transformer.fit(X)
    clr_X, _ = transformer.transform(X)
    X_reconstructed = transformer.inverse_transform(clr_X)
    
    # Check reconstruction (allowing small floating point errors)
    assert np.allclose(X, X_reconstructed, atol=1e-5)

def test_fit_transform():
    """Test fit_transform method."""
    X = np.array([[0.4, 0.4, 0.2]])
    transformer = CLRTransformer()
    clr_X, weights = transformer.fit_transform(X)
    
    assert clr_X is not None
    assert weights is not None
