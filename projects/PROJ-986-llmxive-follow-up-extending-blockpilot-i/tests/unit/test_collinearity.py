"""
Unit tests for collinearity analysis utilities.
"""
import numpy as np
import pytest
from code.utils.collinearity import (
    calculate_vif, 
    residualize_features, 
    pca_decorrelate, 
    check_collinearity_report
)

def test_calculate_vif_perfect_collinearity():
    """Test VIF calculation with perfect collinearity."""
    # Create a matrix where column 1 = column 0
    X = np.array([
        [1.0, 1.0, 2.0],
        [2.0, 2.0, 3.0],
        [3.0, 3.0, 4.0],
        [4.0, 4.0, 5.0],
        [5.0, 5.0, 6.0]
    ])
    
    vif_values = calculate_vif(X)
    
    # Features 0 and 1 are perfectly collinear, so VIF should be inf
    assert np.isinf(vif_values[0]) or np.isinf(vif_values[1])
    # Feature 2 should have finite VIF
    assert not np.isinf(vif_values[2])


def test_calculate_vif_no_collinearity():
    """Test VIF calculation with orthogonal features."""
    # Create a nearly orthogonal matrix
    np.random.seed(42)
    X = np.random.randn(100, 3)
    
    vif_values = calculate_vif(X)
    
    # All VIFs should be close to 1 (no collinearity)
    assert all(1.0 <= vif < 2.0 for vif in vif_values)


def test_calculate_vif_with_names():
    """Test VIF calculation with feature names."""
    X = np.array([
        [1.0, 2.0, 3.0],
        [2.0, 3.0, 4.0],
        [3.0, 4.0, 5.0],
        [4.0, 5.0, 6.0],
        [5.0, 6.0, 7.0]
    ])
    names = ["A", "B", "C"]
    
    vif_values, returned_names = calculate_vif(X, names)
    
    assert returned_names == names
    assert len(vif_values) == 3


def test_residualize_features():
    """Test feature residualization."""
    # Create collinear features
    np.random.seed(42)
    X = np.random.randn(100, 3)
    X[:, 1] = X[:, 0] + 0.1 * np.random.randn(100)  # Highly correlated with col 0
    
    target_idx = 2  # Don't residualize the target
    threshold = 5.0
    
    X_res, residualized = residualize_features(X, target_idx, threshold)
    
    # Check that the shape is preserved
    assert X_res.shape == X.shape
    
    # If residualization happened, check that VIF is reduced
    if residualized:
        vif_values = calculate_vif(X_res)
        # At least some VIFs should be reduced
        assert any(vif < threshold for vif in vif_values)


def test_pca_decorrelate():
    """Test PCA decorrelation."""
    np.random.seed(42)
    X = np.random.randn(100, 5)
    
    transformed, explained_var, components = pca_decorrelate(X, n_components=3)
    
    # Check dimensions
    assert transformed.shape == (100, 3)
    assert components.shape == (3, 5)
    assert len(explained_var) == 3
    
    # Check that explained variance ratios sum to <= 1
    assert 0 < sum(explained_var) <= 1.0
    
    # Check that transformed features are uncorrelated (approximately)
    corr_matrix = np.corrcoef(transformed.T)
    # Off-diagonal elements should be close to 0
    for i in range(3):
        for j in range(3):
            if i != j:
                assert abs(corr_matrix[i, j]) < 0.1


def test_pca_decorrelate_all_components():
    """Test PCA with all components."""
    np.random.seed(42)
    X = np.random.randn(100, 5)
    
    transformed, explained_var, components = pca_decorrelate(X)
    
    # Should preserve all dimensions
    assert transformed.shape == X.shape
    assert components.shape == (5, 5)
    
    # Explained variance should sum to ~1
    assert abs(sum(explained_var) - 1.0) < 0.01


def test_check_collinearity_report():
    """Test report generation."""
    np.random.seed(42)
    X = np.random.randn(50, 3)
    X[:, 1] = X[:, 0] + 0.5 * np.random.randn(50)  # Add some correlation
    
    report = check_collinearity_report(X, ["A", "B", "C"], threshold=5.0)
    
    assert "Collinearity Analysis Report" in report
    assert "VIF" in report
    assert "A" in report
    assert "B" in report
    assert "C" in report


def test_calculate_vif_insufficient_samples():
    """Test VIF with too few samples."""
    X = np.random.randn(2, 5)  # More features than samples
    
    with pytest.raises(ValueError):
        calculate_vif(X)


def test_calculate_vif_single_feature():
    """Test VIF with only one feature."""
    X = np.random.randn(10, 1)
    
    with pytest.raises(ValueError):
        calculate_vif(X)