"""
Unit tests for code/modeling.py functions.
"""
import pytest
import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning
import warnings
from unittest.mock import patch
import math

# Import the module under test
from code.modeling import (
    hyperbolic_function,
    fit_hyperbolic_model,
    load_and_prepare_data,
    transform_and_center,
    calculate_vif,
    run_regression
)

@pytest.fixture
def sample_data_for_modeling():
    """Generate sample data for modeling tests."""
    np.random.seed(42)
    n = 200
    data = {
        'participant_id': range(1, n + 1),
        'discount_rate_k': np.abs(np.random.lognormal(mean=0, sigma=1, size=n)) + 0.001,
        'procrastination_score': np.random.normal(loc=50, scale=10, size=n),
        'wm_accuracy': np.random.normal(loc=0.8, scale=0.1, size=n),
        'wm_rt': np.random.normal(loc=500, scale=50, size=n),
        'age': np.random.randint(18, 65, size=n),
        'gender': np.random.choice(['M', 'F'], size=n),
        'education': np.random.randint(12, 20, size=n)
    }
    return pd.DataFrame(data)

def test_hyperbolic_function():
    """Test the hyperbolic discounting function."""
    # V = A / (1 + k * D)
    A = 100
    k = 0.1
    D = 10
    expected = 100 / (1 + 0.1 * 10)
    assert hyperbolic_function(D, k) == expected

    # Test with array inputs
    D_arr = np.array([1, 5, 10])
    result = hyperbolic_function(D_arr, 0.1)
    assert isinstance(result, np.ndarray)
    assert len(result) == 3

def test_fit_hyperbolic_model(sample_data_for_modeling):
    """Test fitting the hyperbolic model to synthetic data."""
    # Create synthetic data where we know the parameters
    np.random.seed(123)
    n = 50
    D = np.linspace(1, 100, n)
    true_k = 0.05
    A = 100
    noise = np.random.normal(0, 2, n)
    V = A / (1 + true_k * D) + noise

    # Fit the model
    popt, pcov = fit_hyperbolic_model(V, D)

    # Check that fitted k is close to true k
    fitted_k = popt[0]
    assert abs(fitted_k - true_k) < 0.02  # Within 0.02 tolerance

def test_transform_and_center(sample_data_for_modeling):
    """Test log transformation and mean centering."""
    df = sample_data_for_modeling.copy()
    
    # Add log(k) column
    df['log_k'] = np.log(df['discount_rate_k'])
    
    # Apply transformation
    result = transform_and_center(df, ['log_k', 'wm_accuracy', 'age'])
    
    # Check that log_k exists
    assert 'log_k' in result.columns
    
    # Check that centered variables have mean close to 0
    for col in ['log_k', 'wm_accuracy', 'age']:
        center_col = f'{col}_centered'
        assert center_col in result.columns
        assert abs(result[center_col].mean()) < 1e-6

def test_calculate_vif(sample_data_for_modeling):
    """Test VIF calculation."""
    df = sample_data_for_modeling.copy()
    
    # Prepare features for regression (excluding categorical for simplicity)
    features = ['wm_accuracy', 'wm_rt', 'age', 'education']
    X = df[features]
    
    vif_scores = calculate_vif(X)
    
    # Check that VIF is calculated for all features
    assert len(vif_scores) == len(features)
    
    # Check that VIF > 1 (since features are not perfectly correlated)
    for vif in vif_scores:
        assert vif >= 1.0

def test_run_regression(sample_data_for_modeling):
    """Test running the full regression analysis."""
    df = sample_data_for_modeling.copy()
    
    # Prepare data with interaction term
    df['log_k'] = np.log(df['discount_rate_k'])
    df = transform_and_center(df, ['log_k', 'wm_accuracy', 'age'])
    
    # Create interaction term
    df['log_k_centered_wm_accuracy_centered'] = (
        df['log_k_centered'] * df['wm_accuracy_centered']
    )
    
    # Run regression
    results = run_regression(
        df, 
        'procrastination_score', 
        ['log_k_centered', 'wm_accuracy_centered', 'age_centered', 
         'log_k_centered_wm_accuracy_centered']
    )
    
    # Check that results contain expected keys
    assert 'coefficients' in results
    assert 'p_values' in results
    assert 'interaction_p_value' in results
    
    # Check that interaction term is present
    assert 'log_k_centered_wm_accuracy_centered' in results['coefficients']

# --- T011: Unit tests for hyperbolic model fitting edge cases (failure cases) ---

def test_fit_hyperbolic_model_flat_data_raises_error():
    """Test fitting hyperbolic model to flat data (no variance in V) raises error."""
    D = np.linspace(1, 100, 50)
    V = np.ones(50) * 50.0  # Constant value, no decay
    
    with pytest.raises(Exception):
        # curve_fit should fail or return invalid results for flat data
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_divergence_noisy_data():
    """Test fitting hyperbolic model to extremely noisy data that causes divergence."""
    np.random.seed(999)
    D = np.linspace(1, 100, 50)
    true_k = 0.05
    A = 100
    # Add massive noise to prevent convergence
    noise = np.random.normal(0, 500, 50) 
    V = A / (1 + true_k * D) + noise
    
    # We expect this to raise an error or return a result with very high covariance
    # depending on scipy's behavior, but we test that it doesn't crash the runner
    # or return a physically impossible k (e.g., negative huge number).
    # curve_fit often raises RuntimeError if it fails to converge.
    try:
        popt, pcov = fit_hyperbolic_model(V, D)
        # If it doesn't raise, check if k is reasonable (positive)
        assert popt[0] > 0, "Fitted k should be positive"
    except RuntimeError:
        # Expected behavior for divergence
        pass

def test_fit_hyperbolic_model_insufficient_points():
    """Test fitting hyperbolic model with too few data points."""
    D = np.array([1.0, 2.0])
    V = np.array([100.0, 90.0])
    
    # curve_fit requires at least as many points as parameters (2 here: k and A)
    # With exactly 2 points, it might work but with 0 dof, or fail depending on bounds.
    # We test that it handles the edge case gracefully or raises a specific error.
    with pytest.raises(Exception):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_negative_delay():
    """Test fitting hyperbolic model with negative delays (invalid input)."""
    D = np.array([-1.0, 2.0, 5.0])
    V = np.array([100.0, 90.0, 80.0])
    
    # Hyperbolic function 1/(1+kD) is undefined or behaves oddly for negative D if kD = -1
    # curve_fit might fail or return NaN
    with pytest.raises((RuntimeError, ValueError, FloatingPointError)):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_zero_delay_all():
    """Test fitting hyperbolic model where all delays are zero."""
    D = np.zeros(50)
    V = np.ones(50) * 100.0
    
    # If D=0, V = A / 1 = A. We can find A, but k is indeterminate.
    # This should raise an error or return a warning.
    with pytest.raises(Exception):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_nan_in_values():
    """Test fitting hyperbolic model with NaN values in V."""
    D = np.linspace(1, 100, 50)
    V = 100 / (1 + 0.05 * D)
    V[10] = np.nan
    
    with pytest.raises(Exception):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_inf_in_values():
    """Test fitting hyperbolic model with Inf values in V."""
    D = np.linspace(1, 100, 50)
    V = 100 / (1 + 0.05 * D)
    V[10] = np.inf
    
    with pytest.raises(Exception):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_mismatched_lengths():
    """Test fitting hyperbolic model with mismatched lengths of V and D."""
    D = np.linspace(1, 100, 50)
    V = np.linspace(100, 50, 40)
    
    with pytest.raises(ValueError):
        fit_hyperbolic_model(V, D)

def test_fit_hyperbolic_model_extreme_k_bounds():
    """Test fitting hyperbolic model where true k is outside reasonable default bounds."""
    np.random.seed(42)
    D = np.linspace(1, 100, 50)
    true_k = 1e6  # Extremely large k
    A = 100
    V = A / (1 + true_k * D) + np.random.normal(0, 0.1, 50)
    
    # Default bounds in curve_fit might be [0, inf) or similar. 
    # If the solver cannot find a solution within bounds or fails to converge:
    try:
        popt, pcov = fit_hyperbolic_model(V, D)
        # If it succeeds, k should be large
        assert popt[0] > 1000
    except RuntimeError:
        # Expected if bounds prevent convergence
        pass