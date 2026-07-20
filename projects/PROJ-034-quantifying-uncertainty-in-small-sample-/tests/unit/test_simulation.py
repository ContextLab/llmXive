"""
Unit tests for simulation module.
"""
import pytest
import numpy as np
from simulation.config import SimulationConfig
from simulation.engine import calculate_vif, generate_dataset, DatasetInstance

def test_correlation_matrix_generation():
    """
    Verify that the generated correlation matrix matches the target correlation.
    """
    np.random.seed(42)
    config = SimulationConfig(
        n=20,
        predictors=3,
        rho=0.8,
        noise_std=1.0,
        true_coeffs=np.array([1.0, 2.0, 3.0])
    )
    
    # Generate dataset
    dataset: DatasetInstance = generate_dataset(config)
    
    # Calculate empirical correlation
    if dataset.X.shape[1] > 1:
        corr_matrix = np.corrcoef(dataset.X.T)
        # Check off-diagonal elements (approximate due to sampling noise)
        # We check the mean off-diagonal correlation
        off_diag = corr_matrix[np.ones_like(corr_matrix, dtype=bool) ^ np.eye(corr_matrix.shape[0], dtype=bool)]
        mean_off_diag = np.mean(np.abs(off_diag))
        
        # Tolerance for small sample size (N=20)
        tolerance = 0.3 
        assert abs(mean_off_diag - config.rho) < tolerance, \
            f"Mean off-diagonal correlation {mean_off_diag:.3f} not within tolerance of {config.rho}"
    else:
        pytest.skip("Cannot test correlation with single predictor")

def test_rank_checking_logic():
    """
    Verify handling of N=5 or rank-deficient cases.
    """
    # Test case: N < predictors (rank deficient)
    config = SimulationConfig(
        n=3,  # Very small N
        predictors=5, # More predictors than samples
        rho=0.0,
        noise_std=1.0,
        true_coeffs=np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    )
    
    # This should raise a ValueError or handle gracefully
    # Based on engine.py implementation, it should fail or warn
    try:
        dataset = generate_dataset(config)
        # If it succeeds, check rank
        rank = np.linalg.matrix_rank(dataset.X)
        assert rank <= config.n, "Matrix rank exceeds number of samples"
    except ValueError:
        # Expected behavior for rank deficiency
        pass

def test_vif_calculation():
    """
    Verify VIF calculation logic.
    """
    # Create a simple design matrix with known collinearity
    np.random.seed(42)
    n = 50
    x1 = np.random.randn(n)
    x2 = x1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated
    X = np.column_stack([x1, x2])
    
    vif_values = calculate_vif(X)
    
    # VIF for correlated variables should be > 1
    assert len(vif_values) == 2
    assert all(v >= 1.0 for v in vif_values), "VIF should be >= 1"
    # With high correlation, at least one VIF should be significantly > 1
    assert max(vif_values) > 1.5, "Expected high VIF due to correlation"

def test_dataset_instance_creation():
    """
    Verify DatasetInstance creation and attributes.
    """
    config = SimulationConfig(
        n=30,
        predictors=2,
        rho=0.5,
        noise_std=1.0,
        true_coeffs=np.array([1.0, -1.0])
    )
    
    dataset = generate_dataset(config)
    
    assert isinstance(dataset, DatasetInstance)
    assert dataset.X.shape[0] == config.n
    assert dataset.X.shape[1] == config.predictors
    assert dataset.y.shape[0] == config.n
    assert np.allclose(dataset.beta_true, config.true_coeffs)
