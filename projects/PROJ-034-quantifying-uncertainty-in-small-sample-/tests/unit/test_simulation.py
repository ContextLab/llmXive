"""
Unit tests for the simulation module, specifically focusing on correlation matrix generation
and rank-checking logic.
"""
import numpy as np
import pytest
from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, calculate_vif

# Tolerance for floating point comparisons
RHO_TOLERANCE = 1e-3
VIF_THRESHOLD = 10.0

@pytest.fixture
def valid_config():
    """Creates a valid SimulationConfig for testing."""
    return SimulationConfig(
        N=50,
        n_predictors=3,
        rho=0.5,
        noise_std=1.0,
        true_coefficients=np.array([1.0, 2.0, 3.0]),
        seed=42
    )

@pytest.fixture
def low_sample_config():
    """Creates a config with very low sample size to test rank checking."""
    return SimulationConfig(
        N=5,
        n_predictors=3,
        rho=0.2,
        noise_std=1.0,
        true_coefficients=np.array([1.0, 1.0, 1.0]),
        seed=123
    )

def test_correlation_matrix_generation_target_rho(valid_config):
    """
    Test that the generated X matrix has a correlation matrix where the 
    off-diagonal elements match the target rho within tolerance.
    """
    dataset = generate_dataset(valid_config)
    X = dataset.X

    corr_matrix = np.corrcoef(X, rowvar=False)

    n_predictors = valid_config.n_predictors
    off_diagonal_elements = []
    for i in range(n_predictors):
        for j in range(i + 1, n_predictors):
            off_diagonal_elements.append(corr_matrix[i, j])

    for val in off_diagonal_elements:
        assert abs(val - valid_config.rho) < RHO_TOLERANCE, \
            f"Correlation {val} differs from target {valid_config.rho} by more than {RHO_TOLERANCE}"

def test_correlation_matrix_generation_high_rho(valid_config):
    """
    Test with a higher rho value (0.8) to ensure tolerance holds for stronger correlations.
    """
    config = SimulationConfig(
        N=100,
        n_predictors=3,
        rho=0.8,
        noise_std=1.0,
        true_coefficients=np.array([1.0, 2.0, 3.0]),
        seed=42
    )
    dataset = generate_dataset(config)
    X = dataset.X
    corr_matrix = np.corrcoef(X, rowvar=False)

    n_predictors = config.n_predictors
    off_diagonal_elements = []
    for i in range(n_predictors):
        for j in range(i + 1, n_predictors):
            off_diagonal_elements.append(corr_matrix[i, j])

    for val in off_diagonal_elements:
        assert abs(val - config.rho) < RHO_TOLERANCE, \
            f"Correlation {val} differs from target {config.rho} by more than {RHO_TOLERANCE}"

def test_correlation_matrix_diagonal_ones(valid_config):
    """
    Verify that the diagonal of the correlation matrix is exactly 1.0.
    """
    dataset = generate_dataset(valid_config)
    X = dataset.X
    corr_matrix = np.corrcoef(X, rowvar=False)

    assert np.allclose(np.diag(corr_matrix), 1.0), "Diagonal elements of correlation matrix should be 1.0"

def test_rank_checking_logic_low_sample(low_sample_config):
    """
    Test handling of very low sample size (N=5) to ensure the generator
    produces a matrix that is not rank-deficient (or handles it gracefully).
    Since N > p (5 > 3), it should be full rank.
    """
    dataset = generate_dataset(low_sample_config)
    X = dataset.X

    rank = np.linalg.matrix_rank(X)
    assert rank == low_sample_config.n_predictors, \
        f"Matrix rank {rank} is less than expected {low_sample_config.n_predictors} for N={low_sample_config.N}"

def test_rank_checking_logic_rank_deficient_case():
    """
    Explicitly test a case where N <= p (rank-deficient scenario).
    The generator should handle this by raising an error or ensuring N > p.
    We test that the configuration validation or generation logic prevents N <= p.
    """
    # This config violates N > p (N=3, p=5)
    bad_config = SimulationConfig(
        N=3,
        n_predictors=5,
        rho=0.2,
        noise_std=1.0,
        true_coefficients=np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
        seed=999
    )
    
    # The generate_dataset function should raise an error for N <= p
    # or the config validation should catch it. 
    # Based on typical simulation requirements, N must be > p for OLS solvability.
    # We expect a ValueError or similar.
    with pytest.raises(ValueError):
        generate_dataset(bad_config)

def test_vif_calculation_basic(valid_config):
    """
    Test that VIF calculation runs and returns expected structure.
    """
    dataset = generate_dataset(valid_config)
    X = dataset.X
    vifs = calculate_vif(X)

    assert isinstance(vifs, list), "VIF should return a list"
    assert len(vifs) == valid_config.n_predictors, "VIF list length should match number of predictors"
    
    expected_vif_approx = 1 / (1 - valid_config.rho**2)
    for vif in vifs:
        assert vif < 2.0, f"VIF {vif} is unexpectedly high for rho={valid_config.rho}"
        assert vif >= 1.0, "VIF should always be >= 1.0"

def test_vif_flagging_high_collinearity():
    """
    Test VIF flagging logic with a high correlation config.
    """
    config = SimulationConfig(
        N=200,
        n_predictors=3,
        rho=0.95,
        noise_std=1.0,
        true_coefficients=np.array([1.0, 2.0, 3.0]),
        seed=42
    )
    dataset = generate_dataset(config)
    X = dataset.X
    vifs = calculate_vif(X)

    max_vif = max(vifs)
    assert max_vif > 10.0, f"Expected at least one VIF > 10 for rho=0.95, got {max_vif}"