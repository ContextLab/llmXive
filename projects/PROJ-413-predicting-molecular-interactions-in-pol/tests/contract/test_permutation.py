"""
Contract test for permutation test logic and p-value calculation (T031).

This test verifies that the permutation test implementation:
1. Correctly shuffles labels while preserving data structure
2. Computes MSE for each permutation
3. Calculates the p-value as the proportion of permuted MSEs >= observed MSE
4. Returns valid statistical results

This is a CONTRACT test - it verifies the interface and basic logic,
not the full performance of the permutation test.
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.seed_utils import set_seed
from utils.exceptions import DataError


class MockGATModel:
    """Mock GAT model for contract testing - returns predictable values."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        set_seed(seed)
    
    def forward(self, x: np.ndarray, edge_index: np.ndarray) -> np.ndarray:
        """Return a deterministic prediction based on input."""
        # Simple linear transformation with noise for realism
        np.random.seed(self.seed)
        return x.mean(axis=0, keepdims=True) + np.random.randn(1) * 0.1
    
    def train_epoch(self, x: np.ndarray, y: np.ndarray, edge_index: np.ndarray, 
                   learning_rate: float = 0.01) -> float:
        """Simulate training - return a mock loss."""
        pred = self.forward(x, edge_index)
        loss = np.mean((pred - y) ** 2)
        # Slightly reduce loss to simulate learning
        self.seed += 1
        return loss * 0.95
    
    def predict(self, x: np.ndarray, edge_index: np.ndarray) -> np.ndarray:
        """Return predictions."""
        return self.forward(x, edge_index)


def mock_train_model(x_train: np.ndarray, y_train: np.ndarray, 
                    edge_index_train: np.ndarray, epochs: int = 5) -> Tuple[MockGATModel, float]:
    """Mock training function that returns a model and final loss."""
    model = MockGATModel(seed=42)
    final_loss = 0.0
    for epoch in range(epochs):
        final_loss = model.train_epoch(x_train, y_train, edge_index_train)
    return model, final_loss


def compute_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Squared Error."""
    return float(np.mean((y_true - y_pred) ** 2))


def shuffle_labels(y: np.ndarray, seed: int) -> np.ndarray:
    """Shuffle labels while preserving structure."""
    set_seed(seed)
    indices = np.random.permutation(len(y))
    return y[indices]


def run_single_permutation(x: np.ndarray, y: np.ndarray, 
                          edge_index: np.ndarray, 
                          permutation_seed: int, 
                          epochs: int = 5) -> float:
    """
    Run a single permutation iteration.
    
    Args:
        x: Feature matrix
        y: Target values
        edge_index: Graph connectivity
        permutation_seed: Seed for this permutation
        epochs: Number of training epochs
    
    Returns:
        MSE on the permuted dataset
    """
    # Shuffle labels
    y_permuted = shuffle_labels(y, permutation_seed)
    
    # Train model on permuted data
    model, _ = mock_train_model(x, y_permuted, edge_index, epochs)
    
    # Evaluate
    y_pred = model.predict(x, edge_index)
    mse = compute_mse(y_permuted, y_pred)
    
    return mse


def calculate_p_value(observed_mse: float, permuted_mses: List[float]) -> float:
    """
    Calculate p-value from permutation test results.
    
    The p-value is the proportion of permuted MSEs that are >= observed MSE.
    This tests the null hypothesis that the model has no predictive power.
    
    Args:
        observed_mse: MSE from the real (non-permuted) model
        permuted_mses: List of MSEs from permutation iterations
    
    Returns:
        p-value (float between 0 and 1)
    """
    if not permuted_mses:
        raise ValueError("permuted_mses cannot be empty")
    
    count_ge = sum(1 for mse in permuted_mses if mse >= observed_mse)
    p_value = count_ge / len(permuted_mses)
    
    return p_value


def test_shuffle_labels_preserves_structure():
    """Contract: Shuffling labels preserves the array structure and values."""
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_shuffled = shuffle_labels(y, seed=42)
    
    assert len(y_shuffled) == len(y), "Length must be preserved"
    assert set(y_shuffled) == set(y), "Values must be preserved"
    assert not np.array_equal(y, y_shuffled), "Order should change (with high probability)"

def test_permutation_returns_valid_mse():
    """Contract: Permutation test returns a valid MSE value."""
    x = np.random.randn(10, 5)
    y = np.random.randn(10, 1)
    edge_index = np.array([[0, 1, 2, 3], [1, 2, 3, 4]])
    
    mse = run_single_permutation(x, y, edge_index, permutation_seed=42, epochs=5)
    
    assert isinstance(mse, float), "MSE must be a float"
    assert mse >= 0, "MSE must be non-negative"
    assert not np.isnan(mse), "MSE must not be NaN"
    assert not np.isinf(mse), "MSE must not be infinite"

def test_p_value_calculation():
    """Contract: P-value is correctly calculated from observed and permuted MSEs."""
    observed_mse = 0.5
    permuted_mses = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
    
    p_value = calculate_p_value(observed_mse, permuted_mses)
    
    # 6 values >= 0.5 out of 10
    expected_p_value = 6 / 10
    assert abs(p_value - expected_p_value) < 1e-6, f"Expected {expected_p_value}, got {p_value}"

def test_p_value_bounds():
    """Contract: P-value is always between 0 and 1."""
    observed_mse = 0.5
    
    # All permuted values lower
    p_low = calculate_p_value(observed_mse, [0.1, 0.2, 0.3, 0.4])
    assert 0 <= p_low <= 1, "P-value must be in [0, 1]"
    
    # All permuted values higher
    p_high = calculate_p_value(observed_mse, [0.6, 0.7, 0.8, 0.9])
    assert 0 <= p_high <= 1, "P-value must be in [0, 1]"

def test_p_value_empty_list_raises():
    """Contract: Empty permuted_mses list raises ValueError."""
    with pytest.raises(ValueError):
        calculate_p_value(0.5, [])

def test_permutation_test_interface():
    """Contract: Full permutation test flow works end-to-end."""
    # Generate synthetic data for testing
    set_seed(42)
    n_samples = 20
    n_features = 5
    
    x = np.random.randn(n_samples, n_features)
    y = np.random.randn(n_samples, 1)
    edge_index = np.array([
        list(range(n_samples - 1)),
        list(range(1, n_samples))
    ])
    
    # Run baseline
    baseline_model, baseline_loss = mock_train_model(x, y, edge_index, epochs=5)
    y_pred = baseline_model.predict(x, edge_index)
    observed_mse = compute_mse(y, y_pred)
    
    # Run a few permutations
    permuted_mses = []
    for i in range(5):
        mse = run_single_permutation(x, y, edge_index, permutation_seed=100+i, epochs=5)
        permuted_mses.append(mse)
    
    # Calculate p-value
    p_value = calculate_p_value(observed_mse, permuted_mses)
    
    # Verify results
    assert isinstance(observed_mse, float), "Observed MSE must be float"
    assert len(permuted_mses) == 5, "Should have 5 permuted MSEs"
    assert isinstance(p_value, float), "P-value must be float"
    assert 0 <= p_value <= 1, "P-value must be in [0, 1]"

def test_deterministic_with_seed():
    """Contract: Permutation test is deterministic when seeds are fixed."""
    set_seed(42)
    x = np.random.randn(10, 3)
    y = np.random.randn(10, 1)
    edge_index = np.array([[0, 1, 2, 3], [1, 2, 3, 4]])
    
    mse1 = run_single_permutation(x, y, edge_index, permutation_seed=123, epochs=5)
    
    set_seed(42)
    mse2 = run_single_permutation(x, y, edge_index, permutation_seed=123, epochs=5)
    
    assert abs(mse1 - mse2) < 1e-10, "Results should be identical with same seeds"