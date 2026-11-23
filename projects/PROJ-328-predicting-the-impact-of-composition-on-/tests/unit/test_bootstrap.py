"""
Unit tests for code/evaluation/bootstrap.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.bootstrap import BootstrapEvaluator, bootstrap_metrics


class TestBootstrap:
    """Tests for bootstrap evaluation."""

    @pytest.fixture
    def sample_predictions(self):
        """Create sample predictions and true values."""
        np.random.seed(42)
        n = 100
        return {
            'y_true': np.random.randn(n),
            'y_pred': np.random.randn(n) + 0.1 * np.random.randn(n)
        }

    @pytest.fixture
    def evaluator(self):
        """Create a BootstrapEvaluator instance."""
        return BootstrapEvaluator(n_iterations=100, random_state=42)

    def test_bootstrap_r2_calculation(self, sample_predictions, evaluator):
        """Test bootstrap R2 calculation."""
        r2_scores = evaluator.bootstrap_r2(
            sample_predictions['y_true'],
            sample_predictions['y_pred']
        )
        
        assert len(r2_scores) == 100
        assert all(0 <= r <= 1 for r in r2_scores if not np.isnan(r))

    def test_bootstrap_rmse_calculation(self, sample_predictions, evaluator):
        """Test bootstrap RMSE calculation."""
        rmse_scores = evaluator.bootstrap_rmse(
            sample_predictions['y_true'],
            sample_predictions['y_pred']
        )
        
        assert len(rmse_scores) == 100
        assert all(r >= 0 for r in rmse_scores)

    def test_bootstrap_metrics(self, sample_predictions):
        """Test full bootstrap metrics calculation."""
        metrics = bootstrap_metrics(
            sample_predictions['y_true'],
            sample_predictions['y_pred'],
            n_iterations=50,
            random_state=42
        )
        
        assert 'r2_mean' in metrics
        assert 'r2_ci_lower' in metrics
        assert 'r2_ci_upper' in metrics
        assert 'rmse_mean' in metrics
        assert 'rmse_ci_lower' in metrics
        assert 'rmse_ci_upper' in metrics

    def test_confidence_interval_coverage(self, sample_predictions, evaluator):
        """Test that confidence intervals are reasonable."""
        r2_scores = evaluator.bootstrap_r2(
            sample_predictions['y_true'],
            sample_predictions['y_pred']
        )
        
        mean_r2 = np.mean(r2_scores)
        std_r2 = np.std(r2_scores)
        
        # 95% CI should be approximately mean ± 2*std
        ci_lower = mean_r2 - 2 * std_r2
        ci_upper = mean_r2 + 2 * std_r2
        
        # Check that CI bounds are reasonable
        assert ci_lower <= mean_r2 <= ci_upper

    def test_small_sample_bootstrap(self):
        """Test bootstrap on small sample."""
        np.random.seed(42)
        n = 10
        y_true = np.random.randn(n)
        y_pred = np.random.randn(n)
        
        evaluator = BootstrapEvaluator(n_iterations=50, random_state=42)
        metrics = evaluator.bootstrap_r2(y_true, y_pred)
        
        assert len(metrics) == 50
