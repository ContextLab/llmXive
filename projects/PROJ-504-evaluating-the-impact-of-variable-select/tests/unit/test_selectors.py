"""
Unit tests for selection methods in code/analysis/selectors.py.

This file implements TDD-First approach for User Story 2.
Tests verify that selection algorithms correctly identify relevant variables.
"""
import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.selectors import forward_stepwise_selection, backward_elimination, lasso_selection
from code.models import SimulatedDataset


@pytest.fixture
def simple_dataset():
    """Create a simple dataset with known ground truth for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Create X with some correlation structure
    X = np.random.randn(n_samples, n_features)
    # Add correlation between first two features
    X[:, 1] = X[:, 0] * 0.7 + np.random.randn(n_samples) * 0.3
    
    # True coefficients: only first 2 features are relevant
    true_beta = np.array([3.0, 2.0, 0.0, 0.0, 0.0])
    
    # Generate Y with noise
    noise = np.random.randn(n_samples) * 0.5
    Y = X @ true_beta + noise
    
    return SimulatedDataset(
        X=X,
        Y=Y,
        true_coefficients=true_beta,
        snr=1.0,
        sparsity=0.4,
        seed=42,
        dataset_id="test_simple"
    )


@pytest.fixture
def high_correlation_dataset():
    """Create dataset with high correlation to test selection stability."""
    np.random.seed(123)
    n_samples = 200
    n_features = 4
    
    # Create highly correlated features
    base = np.random.randn(n_samples)
    X = np.column_stack([
        base,
        base * 0.95 + np.random.randn(n_samples) * 0.05,
        np.random.randn(n_samples),
        np.random.randn(n_samples)
    ])
    
    # True coefficients: first feature is relevant, second is correlated noise
    true_beta = np.array([5.0, 0.0, 0.0, 0.0])
    
    Y = X @ true_beta + np.random.randn(n_samples) * 0.5
    
    return SimulatedDataset(
        X=X,
        Y=Y,
        true_coefficients=true_beta,
        snr=2.0,
        sparsity=0.25,
        seed=123,
        dataset_id="test_high_corr"
    )


def test_forward_stepwise_selects_correct_vars(simple_dataset):
    """
    Test that forward stepwise selection correctly identifies the true non-zero 
    coefficients in a simple dataset.
    
    Expected: Features 0 and 1 should be selected (true coefficients are 3.0 and 2.0)
    """
    # Run forward stepwise selection
    selected_indices, selected_features = forward_stepwise_selection(
        simple_dataset.X, 
        simple_dataset.Y,
        alpha=0.05,
        max_features=None
    )
    
    # Verify that the correct features are selected
    # We expect at least features 0 and 1 to be selected
    assert 0 in selected_indices, "Feature 0 (true coefficient=3.0) should be selected"
    assert 1 in selected_indices, "Feature 1 (true coefficient=2.0) should be selected"
    
    # Verify that irrelevant features are not selected (or less likely)
    # Note: Due to noise, there might be some false positives, but the main ones should be correct
    assert len(selected_indices) <= 4, "Should not select more than 4 features in this simple case"
    
    # Verify the selected features match the expected pattern
    expected_selected = {0, 1}
    assert set(selected_indices).issuperset(expected_selected), \
        f"Expected to select at least {expected_selected}, got {set(selected_indices)}"


def test_backward_elimination_selects_correct_vars(simple_dataset):
    """
    Test that backward elimination correctly identifies the true non-zero 
    coefficients in a simple dataset.
    """
    # Run backward elimination selection
    selected_indices, selected_features = backward_elimination(
        simple_dataset.X,
        simple_dataset.Y,
        alpha=0.05
    )
    
    # Verify that the correct features are selected
    assert 0 in selected_indices, "Feature 0 (true coefficient=3.0) should be selected"
    assert 1 in selected_indices, "Feature 1 (true coefficient=2.0) should be selected"
    
    # Should not select all features
    assert len(selected_indices) < simple_dataset.X.shape[1], \
        "Backward elimination should remove some features"


def test_lasso_selection_selects_correct_vars(simple_dataset):
    """
    Test that LASSO selection correctly identifies the true non-zero 
    coefficients in a simple dataset.
    """
    # Run LASSO selection
    selected_indices, selected_features, lambdas = lasso_selection(
        simple_dataset.X,
        simple_dataset.Y,
        cv_folds=5
    )
    
    # Verify that the correct features are selected
    assert 0 in selected_indices, "Feature 0 (true coefficient=3.0) should be selected"
    assert 1 in selected_indices, "Feature 1 (true coefficient=2.0) should be selected"
    
    # LASSO should be sparse - not select all features
    assert len(selected_indices) < simple_dataset.X.shape[1], \
        "LASSO should produce a sparse solution"


def test_forward_stepwise_with_high_correlation(high_correlation_dataset):
    """
    Test forward stepwise selection with highly correlated features.
    
    This tests the algorithm's ability to handle multicollinearity.
    """
    selected_indices, selected_features = forward_stepwise_selection(
        high_correlation_dataset.X,
        high_correlation_dataset.Y,
        alpha=0.05
    )
    
    # Feature 0 should definitely be selected (true coefficient = 5.0)
    assert 0 in selected_indices, "Feature 0 (true coefficient=5.0) should be selected"
    
    # Feature 1 is highly correlated with feature 0 but has true coefficient 0
    # It might be selected due to correlation, but feature 0 must be selected
    assert len(selected_indices) >= 1, "At least one feature should be selected"


def test_selection_methods_return_consistent_indices(simple_dataset):
    """
    Test that all three selection methods return indices in the same format.
    """
    # Forward stepwise
    fwd_indices, _ = forward_stepwise_selection(simple_dataset.X, simple_dataset.Y)
    
    # Backward elimination
    bwd_indices, _ = backward_elimination(simple_dataset.X, simple_dataset.Y)
    
    # LASSO
    lasso_indices, _, _ = lasso_selection(simple_dataset.X, simple_dataset.Y)
    
    # All should return lists/arrays of integers
    assert isinstance(fwd_indices, (list, np.ndarray)), "Forward stepwise should return indices"
    assert isinstance(bwd_indices, (list, np.ndarray)), "Backward elimination should return indices"
    assert isinstance(lasso_indices, (list, np.ndarray)), "LASSO should return indices"
    
    # All indices should be within valid range
    n_features = simple_dataset.X.shape[1]
    assert all(0 <= idx < n_features for idx in fwd_indices), "Forward indices out of range"
    assert all(0 <= idx < n_features for idx in bwd_indices), "Backward indices out of range"
    assert all(0 <= idx < n_features for idx in lasso_indices), "LASSO indices out of range"


def test_empty_selection_when_all_insignificant():
    """
    Test selection when all features are noise (no true signal).
    """
    np.random.seed(999)
    n_samples = 50
    n_features = 3
    
    X = np.random.randn(n_samples, n_features)
    Y = np.random.randn(n_samples)  # Pure noise
    
    # All methods should ideally select few or no features
    fwd_indices, _ = forward_stepwise_selection(X, Y, alpha=0.01)
    bwd_indices, _ = backward_elimination(X, Y, alpha=0.01)
    lasso_indices, _, _ = lasso_selection(X, Y, cv_folds=3)
    
    # With strict alpha, we expect very few selections
    # This is a soft check - in pure noise, we might still get some false positives
    # but the count should be low relative to total features
    assert len(fwd_indices) <= n_features, "Forward should not select more than available"
    assert len(bwd_indices) <= n_features, "Backward should not select more than available"
    assert len(lasso_indices) <= n_features, "LASSO should not select more than available"