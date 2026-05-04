"""
Unit tests for DPGMM model edge cases.

Tests cover:
- Empty/zero-variance time series
- Missing value handling
- Extreme outlier values
- Very short/long time series
- NaN/Inf values
- Memory edge cases
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.models.dpgmm import DPGMMModel, DPGMMConfig, compute_anomaly_score, compute_anomaly_scores_batch
from src.models.anomaly_score import AnomalyScore
from src.data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig


class TestDPGMMZeroVariance:
    """Test DPGMM with zero-variance (constant) time series."""
    
    def test_constant_series_single_value(self):
        """Test with all identical values."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # All same value
        constant_data = np.ones(100) * 5.0
        
        # Should not crash, should produce scores
        scores = compute_anomaly_scores_batch(model, constant_data)
        assert len(scores) == 100
        assert all(isinstance(s, AnomalyScore) for s in scores)
    
    def test_constant_series_streaming(self):
        """Test streaming update with constant values."""
        config = DPGMMConfig(
            n_components_max=3,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        constant_value = 10.0
        for i in range(50):
            model.update(np.array([constant_value]))
        
        # Should have converged to single component
        assert model.n_active_components <= 3
    
    def test_very_low_variance(self):
        """Test with extremely small variance."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Very small variance
        data = np.ones(100) * 5.0 + np.random.normal(0, 1e-10, 100)
        
        scores = compute_anomaly_scores_batch(model, data)
        assert len(scores) == 100
        assert all(isinstance(s, AnomalyScore) for s in scores)
        assert not any(np.isnan(s.score) for s in scores)
        assert not any(np.isinf(s.score) for s in scores)

class TestDPGMMMissingValues:
    """Test DPGMM with missing/NaN values."""
    
    def test_nan_values_in_batch(self):
        """Test handling of NaN values in batch scoring."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Train on clean data first
        clean_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([clean_data[i]]))
        
        # Score data with NaN
        data_with_nan = np.array([1.0, np.nan, 2.0, np.nan, 3.0])
        scores = compute_anomaly_scores_batch(model, data_with_nan)
        
        # NaN values should produce NaN scores (not crash)
        assert len(scores) == 5
        assert scores[1].score is None or np.isnan(scores[1].score)
        assert scores[3].score is None or np.isnan(scores[3].score)
        assert not np.isnan(scores[0].score)
    
    def test_inf_values(self):
        """Test handling of infinite values."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Train on normal data
        clean_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([clean_data[i]]))
        
        # Score data with inf
        data_with_inf = np.array([1.0, np.inf, -np.inf, 2.0])
        scores = compute_anomaly_scores_batch(model, data_with_inf)
        
        assert len(scores) == 4
        # Inf values should produce very high anomaly scores
        assert scores[1].score > 100.0  # Should be flagged as anomaly
        assert scores[2].score > 100.0
    
    def test_mixed_missing_strategy(self):
        """Test different strategies for missing values."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42,
            missing_value_strategy='skip'  # Skip NaN values
        )
        model = DPGMMModel(config)
        
        clean_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([clean_data[i]]))
        
        data_with_nan = np.array([1.0, np.nan, 2.0, np.nan, 3.0])
        scores = compute_anomaly_scores_batch(model, data_with_nan)
        
        # With skip strategy, NaN positions should have None scores
        assert len(scores) == 5
        assert scores[1].score is None
        assert scores[3].score is None

class TestDPGMMExtremeOutliers:
    """Test DPGMM with extreme outlier values."""
    
    def test_single_extreme_outlier(self):
        """Test detection of single extreme outlier."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Train on normal data
        clean_data = np.random.normal(0, 1, 1000)
        for i in range(1000):
            model.update(np.array([clean_data[i]]))
        
        # Score with extreme outlier
        test_data = np.array([0.5, 1.0, -0.5, 1000.0, 0.0])
        scores = compute_anomaly_scores_batch(model, test_data)
        
        # Extreme outlier should have highest score
        outlier_idx = 3
        assert scores[outlier_idx].score > scores[0].score * 10
        assert scores[outlier_idx].score > scores[1].score * 10
        assert scores[outlier_idx].score > scores[2].score * 10
        assert scores[outlier_idx].score > scores[4].score * 10
    
    def test_multiple_extreme_outliers(self):
        """Test handling of multiple extreme outliers."""
        config = DPGMMConfig(
            n_components_max=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Train on normal data
        clean_data = np.random.normal(0, 1, 500)
        for i in range(500):
            model.update(np.array([clean_data[i]]))
        
        # Multiple extreme outliers
        test_data = np.array([0.5, 1000.0, -0.5, -1000.0, 0.0, 5000.0])
        scores = compute_anomaly_scores_batch(model, test_data)
        
        # Outliers should have high scores
        assert scores[1].score > 100.0
        assert scores[3].score > 100.0
        assert scores[5].score > 100.0
        
        # Normal values should have lower scores
        assert scores[0].score < 50.0
        assert scores[2].score < 50.0
        assert scores[4].score < 50.0
    
    def test_outlier_during_training(self):
        """Test model robustness when outliers appear during training."""
        config = DPGMMConfig(
            n_components_max=10,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Mix of normal and outlier data during training
        for i in range(100):
            if i % 20 == 0:
                # Every 20th point is extreme outlier
                model.update(np.array([1000.0]))
            else:
                model.update(np.array([np.random.normal(0, 1)]))
        
        # Model should still function
        test_data = np.random.normal(0, 1, 10)
        scores = compute_anomaly_scores_batch(model, test_data)
        assert len(scores) == 10
        assert all(isinstance(s, AnomalyScore) for s in scores)

class TestDPGMMLengthEdgeCases:
    """Test DPGMM with very short and very long time series."""
    
    def test_very_short_series(self):
        """Test with fewer than 10 observations."""
        config = DPGMMConfig(
            n_components_max=3,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Only 5 observations
        short_data = np.array([1.0, 2.0, 1.5, 1.8, 2.2])
        for i in range(len(short_data)):
            model.update(np.array([short_data[i]]))
        
        # Should handle gracefully
        scores = compute_anomaly_scores_batch(model, short_data)
        assert len(scores) == 5
        assert all(isinstance(s, AnomalyScore) for s in scores)
    
    def test_single_observation(self):
        """Test with only one observation."""
        config = DPGMMConfig(
            n_components_max=3,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        model.update(np.array([5.0]))
        
        # Should not crash
        scores = compute_anomaly_scores_batch(model, np.array([5.0]))
        assert len(scores) == 1
    
    def test_very_long_series(self):
        """Test with large number of observations."""
        config = DPGMMConfig(
            n_components_max=20,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # 10000 observations
        long_data = np.random.normal(0, 1, 10000)
        for i in range(10000):
            model.update(np.array([long_data[i]]))
        
        # Should complete without memory issues
        assert model.n_active_components <= 20
        
        # Score subset
        test_data = long_data[:100]
        scores = compute_anomaly_scores_batch(model, test_data)
        assert len(scores) == 100

class TestDPGMMNumericalStability:
    """Test numerical stability of DPGMM."""
    
    def test_very_large_values(self):
        """Test with very large magnitude values."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Large values
        large_data = np.array([1e6, 1e6 + 1, 1e6 - 1, 1e6 + 0.5])
        for i in range(len(large_data)):
            model.update(np.array([large_data[i]]))
        
        # Should not overflow
        scores = compute_anomaly_scores_batch(model, large_data)
        assert all(isinstance(s, AnomalyScore) for s in scores)
        assert not any(np.isnan(s.score) for s in scores if s.score is not None)
        assert not any(np.isinf(s.score) for s in scores if s.score is not None)
    
    def test_very_small_values(self):
        """Test with very small magnitude values."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Very small values
        small_data = np.array([1e-10, 1e-10 + 1e-12, 1e-10 - 1e-12])
        for i in range(len(small_data)):
            model.update(np.array([small_data[i]]))
        
        # Should not underflow
        scores = compute_anomaly_scores_batch(model, small_data)
        assert all(isinstance(s, AnomalyScore) for s in scores)
        assert not any(np.isnan(s.score) for s in scores if s.score is not None)
    
    def test_mixed_scales(self):
        """Test with values at different scales."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Mixed scales
        mixed_data = np.array([1e-6, 1.0, 1e6, 1e-3, 1e3])
        for i in range(len(mixed_data)):
            model.update(np.array([mixed_data[i]]))
        
        # Should handle without numerical issues
        scores = compute_anomaly_scores_batch(model, mixed_data)
        assert all(isinstance(s, AnomalyScore) for s in scores)
        assert not any(np.isnan(s.score) for s in scores if s.score is not None)

class TestDPGMMConcentrationParameter:
    """Test concentration parameter edge cases."""
    
    def test_very_small_concentration(self):
        """Test with very small concentration parameter."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=0.001,  # Very small
            random_seed=42
        )
        model = DPGMMModel(config)
        
        data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([data[i]]))
        
        # Should still work, may favor fewer components
        assert model.n_active_components <= 5
    
    def test_very_large_concentration(self):
        """Test with very large concentration parameter."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=100.0,  # Very large
            random_seed=42
        )
        model = DPGMMModel(config)
        
        data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([data[i]]))
        
        # Should still respect max components
        assert model.n_active_components <= 5
    
    def test_zero_concentration(self):
        """Test with zero concentration parameter (edge case)."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=0.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([data[i]]))
        
        # Should handle gracefully
        assert model.n_active_components >= 1

class TestDPGMMMemoryEdgeCases:
    """Test memory-related edge cases."""
    
    def test_memory_with_many_components(self):
        """Test memory usage with many mixture components."""
        config = DPGMMConfig(
            n_components_max=50,
            concentration_prior=10.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Generate data that could support many components
        data = np.concatenate([
            np.random.normal(-5, 0.5, 100),
            np.random.normal(0, 0.5, 100),
            np.random.normal(5, 0.5, 100),
        ])
        
        for i in range(len(data)):
            model.update(np.array([data[i]]))
        
        # Should not exceed max components
        assert model.n_active_components <= 50

class TestDPGMMBatchScoring:
    """Test batch scoring edge cases."""
    
    def test_empty_batch(self):
        """Test scoring empty array."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Train on some data
        train_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([train_data[i]]))
        
        # Score empty array
        scores = compute_anomaly_scores_batch(model, np.array([]))
        assert len(scores) == 0
    
    def test_single_element_batch(self):
        """Test scoring single element."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        train_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([train_data[i]]))
        
        scores = compute_anomaly_scores_batch(model, np.array([1.0]))
        assert len(scores) == 1
        assert isinstance(scores[0], AnomalyScore)
    
    def test_batch_with_all_nan(self):
        """Test batch where all values are NaN."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        train_data = np.random.normal(0, 1, 100)
        for i in range(100):
            model.update(np.array([train_data[i]]))
        
        scores = compute_anomaly_scores_batch(model, np.array([np.nan, np.nan, np.nan]))
        assert len(scores) == 3
        assert all(s.score is None or np.isnan(s.score) for s in scores)

class TestDPGMMMultivariateEdgeCases:
    """Test multivariate DPGMM edge cases."""
    
    def test_multivariate_single_feature(self):
        """Test multivariate with single feature."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Single feature as 2D array
        data = np.random.normal(0, 1, 100).reshape(-1, 1)
        for i in range(100):
            model.update(data[i])
        
        # Should work
        test_data = np.array([[1.0], [2.0], [3.0]])
        scores = compute_anomaly_scores_batch(model, test_data.flatten())
        assert len(scores) == 3
    
    def test_multivariate_correlated_features(self):
        """Test with highly correlated features."""
        config = DPGMMConfig(
            n_components_max=5,
            concentration_prior=1.0,
            random_seed=42
        )
        model = DPGMMModel(config)
        
        # Highly correlated features
        base = np.random.normal(0, 1, 100)
        data = np.column_stack([base, base * 0.99 + np.random.normal(0, 0.01, 100)])
        
        for i in range(100):
            model.update(data[i])
        
        # Should handle without numerical issues
        test_data = np.array([[1.0, 0.99], [2.0, 1.98]])
        scores = compute_anomaly_scores_batch(model, test_data.flatten())
        assert len(scores) == 2
        assert not any(np.isnan(s.score) for s in scores if s.score is not None)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
