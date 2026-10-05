"""
Unit tests for stability metric calculation in the LOO Jackknife robustness analysis.

This module tests the calculation of stability metrics (loading correlations)
comparing fPCA results from LOO subsamples against the full ensemble results,
as required by US3-AC1 and FR-005.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from robustness import calculate_loading_correlation, calculate_stability_metrics


class TestStabilityMetricCalculation:
    """Tests for stability metric calculation functions."""

    def test_calculate_loading_correlation_basic(self):
        """Test basic correlation calculation between two loading vectors."""
        # Create two similar loading vectors (high correlation expected)
        base_loadings = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        perturbed_loadings = base_loadings + np.random.normal(0, 0.1, size=base_loadings.shape)

        correlation = calculate_loading_correlation(base_loadings, perturbed_loadings)

        assert isinstance(correlation, float)
        assert -1.0 <= correlation <= 1.0
        assert correlation > 0.9  # Should be highly correlated

    def test_calculate_loading_correlation_perfect(self):
        """Test correlation with identical vectors."""
        vector = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        correlation = calculate_loading_correlation(vector, vector)

        assert correlation == 1.0

    def test_calculate_loading_correlation_negative(self):
        """Test correlation with perfectly anti-correlated vectors."""
        vector = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        anti_vector = -vector
        correlation = calculate_loading_correlation(vector, anti_vector)

        assert correlation == -1.0

    def test_calculate_loading_correlation_orthogonal(self):
        """Test correlation with orthogonal vectors (near zero)."""
        vector1 = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
        vector2 = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
        correlation = calculate_loading_correlation(vector1, vector2)

        # Should be close to 0 for orthogonal vectors
        assert abs(correlation) < 0.1

    def test_calculate_loading_correlation_2d_loadings(self):
        """Test correlation calculation with 2D loading matrix (multiple components)."""
        # Simulate loadings for 3 components across 5 features
        base_loadings = np.random.rand(5, 3)
        # Add small noise
        perturbed_loadings = base_loadings + np.random.normal(0, 0.05, size=base_loadings.shape)

        correlations = calculate_loading_correlation(base_loadings, perturbed_loadings)

        assert isinstance(correlations, np.ndarray)
        assert len(correlations) == 3  # One correlation per component
        assert all(-1.0 <= c <= 1.0 for c in correlations)
        assert all(c > 0.8 for c in correlations)  # Should be highly correlated

    def test_calculate_stability_metrics_basic(self):
        """Test basic stability metrics calculation."""
        # Create mock full ensemble loadings (3 components)
        full_loadings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

        # Create mock LOO subsample loadings
        loo_loadings = [
            np.array([
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]) + np.random.normal(0, 0.1, (3, 3))
            for _ in range(5)
        ]

        stability_metrics = calculate_stability_metrics(full_loadings, loo_loadings)

        assert "correlations" in stability_metrics
        assert "mean_correlation" in stability_metrics
        assert "std_correlation" in stability_metrics
        assert "min_correlation" in stability_metrics
        assert "max_correlation" in stability_metrics

        assert isinstance(stability_metrics["correlations"], list)
        assert len(stability_metrics["correlations"]) == 5  # 5 LOO iterations

    def test_calculate_stability_metrics_multiple_components(self):
        """Test stability metrics for multiple principal components."""
        # Full ensemble: 5 features, 3 components
        full_loadings = np.random.rand(5, 3)

        # 4 LOO iterations with slightly different loadings
        loo_loadings = [
            full_loadings + np.random.normal(0, 0.05, full_loadings.shape)
            for _ in range(4)
        ]

        stability_metrics = calculate_stability_metrics(full_loadings, loo_loadings)

        assert len(stability_metrics["correlations"]) == 4
        assert len(stability_metrics["component_correlations"]) == 3  # 3 components

        # Check component-wise correlations
        for comp_idx, comp_corr in enumerate(stability_metrics["component_correlations"]):
            assert "mean" in comp_corr
            assert "std" in comp_corr
            assert -1.0 <= comp_corr["mean"] <= 1.0
            assert comp_corr["std"] >= 0

    def test_calculate_stability_metrics_empty_loo(self):
        """Test behavior with empty LOO list."""
        full_loadings = np.array([[1.0, 0.0], [0.0, 1.0]])
        loo_loadings = []

        stability_metrics = calculate_stability_metrics(full_loadings, loo_loadings)

        assert stability_metrics["correlations"] == []
        assert stability_metrics["mean_correlation"] is None
        assert stability_metrics["std_correlation"] is None

    def test_calculate_stability_metrics_single_component(self):
        """Test stability metrics with single component loadings."""
        full_loadings = np.array([1.0, 2.0, 3.0, 4.0])
        loo_loadings = [
            full_loadings + np.random.normal(0, 0.1, full_loadings.shape)
            for _ in range(3)
        ]

        stability_metrics = calculate_stability_metrics(full_loadings, loo_loadings)

        assert len(stability_metrics["correlations"]) == 3
        assert len(stability_metrics["component_correlations"]) == 1

    def test_stability_metrics_threshold_flagging(self):
        """Test that stability metrics correctly identify unstable components."""
        # Create full loadings
        full_loadings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

        # Create LOO loadings where one component is unstable (low correlation)
        loo_loadings = []
        for i in range(5):
            if i == 0:
                # First iteration: stable for all components
                loo_loadings.append(full_loadings + np.random.normal(0, 0.05, full_loadings.shape))
            else:
                # Other iterations: component 2 is unstable (flipped sign)
                unstable = full_loadings.copy()
                unstable[:, 2] = -unstable[:, 2] + np.random.normal(0, 0.05, full_loadings.shape[:, 2].shape)
                loo_loadings.append(unstable)

        stability_metrics = calculate_stability_metrics(full_loadings, loo_loadings)

        # Component 2 should have lower mean correlation
        component_2_mean = stability_metrics["component_correlations"][2]["mean"]
        component_0_mean = stability_metrics["component_correlations"][0]["mean"]

        # Component 2 should be significantly less stable than component 0
        assert component_2_mean < component_0_mean

    def test_correlation_with_sign_flip(self):
        """Test that sign flips in loadings are handled correctly (absolute correlation)."""
        vector1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        vector2 = -vector1  # Perfect negative correlation

        correlation = calculate_loading_correlation(vector1, vector2)

        # The function should return the absolute correlation for stability metrics
        # or handle sign ambiguity appropriately
        assert abs(correlation) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])