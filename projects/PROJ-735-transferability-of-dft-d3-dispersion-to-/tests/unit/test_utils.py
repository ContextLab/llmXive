import pytest
import numpy as np
from utils import bootstrap_resample, calculate_metrics, bootstrap_mae

class TestBootstrapResample:
    def test_bootstrap_resample(self):
        """Test that bootstrap_resample generates the correct number of resampled datasets."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        n_replicates = 1000
        resamples = bootstrap_resample(data, n_replicates=n_replicates)

        assert len(resamples) == n_replicates, f"Expected {n_replicates} resamples, got {len(resamples)}"
        for resample in resamples:
            assert len(resample) == len(data), "Each resample must have the same length as the original data"
            assert np.all(np.isin(resample, data)), "Resampled elements must be from the original data"

class TestCalculateMetrics:
    def test_calculate_metrics(self):
        """Test MAE and RMSE calculations."""
        errors = np.array([1.0, -2.0, 3.0, -4.0, 5.0])
        metrics = calculate_metrics(errors)

        # Manual calculation
        expected_mae = np.mean(np.abs(errors))
        expected_rmse = np.sqrt(np.mean(errors**2))

        assert np.isclose(metrics["mae"], expected_mae), f"MAE mismatch: {metrics['mae']} vs {expected_mae}"
        assert np.isclose(metrics["rmse"], expected_rmse), f"RMSE mismatch: {metrics['rmse']} vs {expected_rmse}"
        assert "mean_signed_error" in metrics
        assert "mse" in metrics

class TestBootstrapMae:
    def test_bootstrap_mae(self):
        """Test bootstrap MAE estimation."""
        errors = np.array([1.0, -2.0, 3.0, -4.0, 5.0])
        mae_est, ci_lower, ci_upper = bootstrap_mae(errors, n_replicates=1000, random_state=42)

        assert isinstance(mae_est, float)
        assert ci_lower < mae_est < ci_upper, "CI should bracket the estimate"
        assert ci_lower > 0, "MAE CI lower bound must be positive"