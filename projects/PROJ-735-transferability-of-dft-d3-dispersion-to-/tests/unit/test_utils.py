import pytest
import numpy as np
from utils import bootstrap_resample, calculate_metrics, bootstrap_mae

def test_bootstrap_resample():
    """Test that bootstrap_resample generates the correct number of resampled datasets."""
    data = [1, 2, 3, 4, 5]
    n_replicates = 1000
    resampled = bootstrap_resample(data, n_replicates)
    
    assert len(resampled) == n_replicates
    for sample in resampled:
        assert len(sample) == len(data)
        # Check that values are from the original data
        assert all(x in data for x in sample)

def test_calculate_metrics():
    """Test MAE and RMSE calculations."""
    reference = [10, 20, 30]
    predicted = [12, 18, 32]
    
    metrics = calculate_metrics(reference, predicted)
    
    # MAE = (|10-12| + |20-18| + |30-32|) / 3 = (2+2+2)/3 = 2.0
    assert np.isclose(metrics["mae"], 2.0)
    
    # RMSE = sqrt(((10-12)^2 + (20-18)^2 + (30-32)^2) / 3) = sqrt((4+4+4)/3) = sqrt(4) = 2.0
    assert np.isclose(metrics["rmse"], 2.0)
    
    # MSE = 4.0
    assert np.isclose(metrics["mse"], 4.0)

def test_bootstrap_mae():
    """Test bootstrap MAE calculation returns expected structure."""
    reference = [10, 20, 30, 40, 50]
    predicted = [12, 18, 32, 38, 52]
    
    mae, ci_lower, ci_upper = bootstrap_mae(reference, predicted, n_replicates=100)
    
    assert isinstance(mae, float)
    assert isinstance(ci_lower, float)
    assert isinstance(ci_upper, float)
    assert ci_lower <= mae <= ci_upper
