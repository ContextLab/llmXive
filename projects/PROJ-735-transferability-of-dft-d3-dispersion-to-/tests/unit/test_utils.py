import pytest
import numpy as np
from utils import bootstrap_resample, calculate_metrics, bootstrap_mae

def test_bootstrap_resample():
    """Test that bootstrap_resample generates the correct number of resampled datasets."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    n_replicates = 1000
    random_state = 42
    
    resampled = bootstrap_resample(data, n_replicates, random_state)
    
    assert len(resampled) == n_replicates
    for sample in resampled:
        assert len(sample) == len(data)
        # Check that values are from the original data
        for val in sample:
            assert val in data

def test_calculate_metrics():
    """Test MAE and RMSE calculations."""
    # Errors = Predicted - Reference
    # If Reference = [10, 20, 30] and Predicted = [12, 18, 32]
    # Errors = [2, -2, 2]
    errors = [2.0, -2.0, 2.0]
    
    metrics = calculate_metrics(errors)
    
    # MAE = mean(|2|, |-2|, |2|) = 2.0
    assert np.isclose(metrics["mae"], 2.0)
    
    # RMSE = sqrt(mean(2^2, (-2)^2, 2^2)) = sqrt(mean(4, 4, 4)) = sqrt(4) = 2.0
    assert np.isclose(metrics["rmse"], 2.0)
    
    # MSE = mean(4, 4, 4) = 4.0
    assert np.isclose(metrics["mse"], 4.0)
    
    # Mean Signed Error = mean(2, -2, 2) = 2/3
    assert np.isclose(metrics["mean_signed_error"], 2.0/3.0)

def test_bootstrap_mae():
    """Test bootstrap MAE calculation returns expected structure."""
    errors = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    mae, ci_lower, ci_upper = bootstrap_mae(errors, n_replicates=100, random_state=42)
    
    assert isinstance(mae, float)
    assert isinstance(ci_lower, float)
    assert isinstance(ci_upper, float)
    assert ci_lower <= mae <= ci_upper