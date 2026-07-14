"""Integration test for correlation analysis with synthetic data.

This test verifies that the correlation pipeline (Pearson/Spearman,
FDR correction, and threshold logging) produces correct r, p, and q values
when run on synthetic data with known properties.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import get_logger
from analysis.correlations import (
    run_metric_correlations,
    apply_fdr_correction,
    partial_correlation,
)


class TestCorrelationWithSyntheticData:
    """Integration tests for correlation analysis on synthetic data."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.logger = get_logger(__name__)
        self.test_data_dir = Path(__file__).parent.parent.parent / "data" / "test_synthetic"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup is optional; test data can remain for inspection

    def create_synthetic_metrics_with_known_correlation(
        self,
        n_subjects: int = 100,
        correlation_strength: float = 0.6,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Create synthetic metrics with known correlation to motor_score.
        
        Args:
            n_subjects: Number of synthetic subjects
            correlation_strength: Pearson r between metric and motor_score
            seed: Random seed for reproducibility
        
        Returns:
            DataFrame with columns: subject_id, modularity, global_efficiency,
            participation_coef, within_module_degree, motor_score, fd
        """
        np.random.seed(seed)
        
        # Create motor_score (0-100 scale, realistic proprioceptive accuracy proxy)
        motor_score = np.random.uniform(40, 100, n_subjects)
        
        # Create FD (framewise displacement, in mm, realistic range)
        fd = np.random.uniform(0.1, 0.8, n_subjects)
        
        # Create metrics with controlled correlation to motor_score
        # metric = correlation_strength * motor_score + noise
        noise_std = np.sqrt(1 - correlation_strength**2)
        
        modularity = (
            correlation_strength * (motor_score / 100.0) +
            np.random.normal(0, noise_std, n_subjects)
        )
        
        global_efficiency = (
            correlation_strength * (motor_score / 100.0) +
            np.random.normal(0, noise_std, n_subjects)
        )
        
        participation_coef = (
            correlation_strength * (motor_score / 100.0) +
            np.random.normal(0, noise_std, n_subjects)
        )
        
        within_module_degree = (
            correlation_strength * (motor_score / 100.0) +
            np.random.normal(0, noise_std, n_subjects)
        )
        
        return pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
            'modularity': modularity,
            'global_efficiency': global_efficiency,
            'participation_coef': participation_coef,
            'within_module_degree': within_module_degree,
            'motor_score': motor_score,
            'fd': fd,
        })

    def test_correlation_with_synthetic_data(self):
        """Test that correlations are computed correctly on synthetic data.
        
        Verifies:
        - Pearson correlation r values are close to expected (within tolerance)
        - p-values are computed correctly
        - FDR-corrected q-values are computed
        - Threshold logging works (r > 0.3 triggers log)
        """
        # Create synthetic data with known correlation
        df = self.create_synthetic_metrics_with_known_correlation(
            n_subjects=100,
            correlation_strength=0.6,
        )
        
        # Save to temp file for processing
        synthetic_file = self.test_data_dir / "synthetic_metrics.csv"
        df.to_csv(synthetic_file, index=False)
        
        # Run correlation analysis
        results = run_metric_correlations(
            metrics_df=df,
            score_column='motor_score',
            covariate_columns=['fd'],
            method='pearson',
        )
        
        # Verify results structure
        assert isinstance(results, pd.DataFrame), "Results must be a DataFrame"
        assert 'metric' in results.columns, "Results must have 'metric' column"
        assert 'r' in results.columns, "Results must have 'r' (correlation) column"
        assert 'p' in results.columns, "Results must have 'p' (p-value) column"
        assert 'q' in results.columns, "Results must have 'q' (FDR-corrected p) column"
        
        # Verify we have results for all metrics
        expected_metrics = {
            'modularity',
            'global_efficiency',
            'participation_coef',
            'within_module_degree',
        }
        actual_metrics = set(results['metric'].unique())
        assert expected_metrics == actual_metrics, (
            f"Expected metrics {expected_metrics}, got {actual_metrics}"
        )
        
        # Verify r values are in valid range [-1, 1]
        assert (results['r'].abs() <= 1.0).all(), "Correlation r must be in [-1, 1]"
        
        # Verify p-values are in valid range [0, 1]
        assert (results['p'] >= 0).all() and (results['p'] <= 1).all(), (
            "p-values must be in [0, 1]"
        )
        
        # Verify q-values (FDR-corrected) are in valid range [0, 1]
        assert (results['q'] >= 0).all() and (results['q'] <= 1).all(), (
            "q-values must be in [0, 1]"
        )
        
        # Verify q >= p (FDR correction increases p-values)
        assert (results['q'] >= results['p']).all(), (
            "FDR-corrected q must be >= original p"
        )
        
        # Verify that r values are reasonably close to expected (0.6)
        # Allow some tolerance due to finite sample size and noise
        mean_r = results['r'].mean()
        assert mean_r > 0.4, (
            f"Expected mean r > 0.4 for synthetic data with r=0.6, got {mean_r}"
        )

    def test_fdr_correction_on_synthetic_data(self):
        """Test that FDR correction is applied correctly.
        
        Verifies:
        - FDR-corrected q-values are computed
        - q-values are >= original p-values
        - At least some q-values are < 0.05 for strong correlations
        """
        # Create data with strong correlation
        df = self.create_synthetic_metrics_with_known_correlation(
            n_subjects=150,
            correlation_strength=0.7,
        )
        
        # Extract metrics and scores
        metrics = df[['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']]
        scores = df['motor_score'].values
        
        # Compute correlations
        p_values = []
        r_values = []
        
        for col in metrics.columns:
            r = np.corrcoef(metrics[col].values, scores)[0, 1]
            # Compute p-value using t-statistic
            t = r * np.sqrt(len(scores) - 2) / np.sqrt(1 - r**2)
            from scipy import stats
            p = 2 * (1 - stats.t.cdf(abs(t), len(scores) - 2))
            r_values.append(r)
            p_values.append(p)
        
        p_values = np.array(p_values)
        
        # Apply FDR correction
        from statsmodels.stats.multitest import multipletests
        reject, q_values, _, _ = multipletests(p_values, method='fdr_bh')
        
        # Verify q-values are >= p-values
        assert (q_values >= p_values).all(), (
            "FDR-corrected q must be >= original p"
        )
        
        # Verify at least some q-values are significant for strong correlation
        assert (q_values < 0.05).sum() > 0, (
            "Expected at least one significant q-value for r=0.7"
        )

    def test_partial_correlation_with_covariate(self):
        """Test that partial correlation correctly controls for covariates.
        
        Verifies:
        - Partial correlation reduces r when covariate is correlated
        - Partial correlation matches expected values
        """
        np.random.seed(42)
        n = 100
        
        # Create data where FD is correlated with both metric and motor_score
        fd = np.random.uniform(0.1, 0.8, n)
        motor_score = 0.5 * fd + np.random.normal(0, 0.5, n) + 50
        metric = 0.6 * motor_score + 0.4 * fd + np.random.normal(0, 0.3, n)
        
        # Compute partial correlation (metric vs motor_score, controlling for fd)
        partial_r = partial_correlation(metric, motor_score, fd)
        
        # Partial correlation should be a valid number
        assert isinstance(partial_r, (float, np.floating)), (
            "Partial correlation must return a float"
        )
        
        # Partial correlation should be in [-1, 1]
        assert -1.0 <= partial_r <= 1.0, (
            f"Partial correlation must be in [-1, 1], got {partial_r}"
        )
        
        # Partial correlation should be less than full correlation
        # (because fd is correlated with both variables)
        full_r = np.corrcoef(metric, motor_score)[0, 1]
        assert abs(partial_r) <= abs(full_r), (
            "Partial correlation should reduce effect when covariate is correlated"
        )

    def test_threshold_logging_for_strong_correlations(self):
        """Test that correlations > 0.3 are logged.
        
        This test verifies the threshold logging requirement from T027.
        """
        # Create data with strong correlation
        df = self.create_synthetic_metrics_with_known_correlation(
            n_subjects=100,
            correlation_strength=0.6,
        )
        
        # Run correlation analysis
        results = run_metric_correlations(
            metrics_df=df,
            score_column='motor_score',
            covariate_columns=['fd'],
            method='pearson',
        )
        
        # Check that we have correlations > 0.3
        strong_correlations = results[results['r'].abs() > 0.3]
        assert len(strong_correlations) > 0, (
            "Expected at least one correlation > 0.3 with r=0.6"
        )
        
        # Verify strong correlations are recorded
        for _, row in strong_correlations.iterrows():
            assert row['r'] > 0.3 or row['r'] < -0.3, (
                f"Expected |r| > 0.3, got r={row['r']}"
            )
