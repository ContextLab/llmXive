"""
Unit tests for power_curve_generator module.

Tests the core logic of power curve generation without requiring
real data downloads.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import pytest

# Import the module under test
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analysis.power_curve_generator import (
    bootstrap_single_iteration,
    run_bootstrap_loop,
    generate_power_curve,
    fit_power_curve_model,
    save_power_curves
)
from models.simulation_config import SimulationConfig
from models.replication_result import ReplicationResult


class TestBootstrapSingleIteration:
    """Tests for bootstrap_single_iteration function."""

    def test_returns_result_on_success(self):
        """Test that function returns ReplicationResult on success."""
        # Create mock data
        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)

        # Mock the dependencies
        with patch('analysis.power_curve_generator.apply_temporal_smoothing') as mock_smooth, \
             patch('analysis.power_curve_generator.estimate_noise_parameters') as mock_noise, \
             patch('analysis.power_curve_generator.fit_glm') as mock_glm, \
             patch('analysis.power_curve_generator.estimate_effect_size') as mock_effect, \
             patch('analysis.power_curve_generator.run_split_half_validation') as mock_validate:

            # Setup mocks
            mock_smooth.return_value = timeseries
            mock_noise.return_value = {"variance": 1.0}
            mock_glm.return_value = Mock(pvalues=[0.05], fittedvalues=timeseries)
            mock_effect.return_value = 0.5
            mock_validate.return_value = Mock(replication_success=True)

            result = bootstrap_single_iteration(
                timeseries=timeseries,
                regressors=regressors,
                sample_size=50,
                kernel_size=4.0,
                seed=42
            )

            assert result is not None
            assert isinstance(result, ReplicationResult)
            assert result.effect_size_est == 0.5
            assert result.replication_success == 1

    def test_returns_none_on_glm_failure(self):
        """Test that function returns None when GLM fails."""
        from analysis.glm_fitter import GLMFitError

        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)

        with patch('analysis.power_curve_generator.apply_temporal_smoothing') as mock_smooth, \
             patch('analysis.power_curve_generator.estimate_noise_parameters') as mock_noise, \
             patch('analysis.power_curve_generator.fit_glm') as mock_glm:

            mock_smooth.return_value = timeseries
            mock_noise.return_value = {"variance": 1.0}
            mock_glm.side_effect = GLMFitError("Convergence failed")

            result = bootstrap_single_iteration(
                timeseries=timeseries,
                regressors=regressors,
                sample_size=50,
                kernel_size=4.0,
                seed=42
            )

            assert result is None

    def test_skips_small_sample_size(self):
        """Test that function skips iterations with very small sample sizes."""
        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)

        with patch('analysis.power_curve_generator.set_global_seed'), \
             patch('analysis.power_curve_generator.logger') as mock_logger:

            result = bootstrap_single_iteration(
                timeseries=timeseries,
                regressors=regressors,
                sample_size=5,  # Very small
                kernel_size=4.0,
                seed=42
            )

            assert result is None
            mock_logger.warning.assert_called()


class TestRunBootstrapLoop:
    """Tests for run_bootstrap_loop function."""

    def test_aggregates_results_correctly(self):
        """Test that loop correctly aggregates multiple iterations."""
        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)

        # Mock to return successful results
        with patch('analysis.power_curve_generator.bootstrap_single_iteration') as mock_iter:
            # Create mock results
            mock_results = [
                ReplicationResult(effect_size_est=0.5, p_value=0.04, replication_success=1, smoothing_kernel_used=4.0),
                ReplicationResult(effect_size_est=0.6, p_value=0.03, replication_success=1, smoothing_kernel_used=4.0),
                ReplicationResult(effect_size_est=0.4, p_value=0.06, replication_success=0, smoothing_kernel_used=4.0),
            ]
            mock_iter.side_effect = mock_results + [None]  # One failure

            result = run_bootstrap_loop(
                timeseries=timeseries,
                regressors=regressors,
                sample_size=50,
                kernel_size=4.0,
                num_iterations=4,
                base_seed=42
            )

            assert result["sample_size"] == 50
            assert result["kernel_size"] == 4.0
            assert result["iterations_run"] == 3
            assert result["total_iterations"] == 4
            # Empirical power = 2 successes / 3 successful iterations = 0.667
            assert abs(result["empirical_power"] - 0.6666666666666666) < 0.001

    def test_handles_all_failures(self):
        """Test handling when all iterations fail."""
        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)

        with patch('analysis.power_curve_generator.bootstrap_single_iteration') as mock_iter, \
             patch('analysis.power_curve_generator.logger') as mock_logger:

            mock_iter.return_value = None

            result = run_bootstrap_loop(
                timeseries=timeseries,
                regressors=regressors,
                sample_size=50,
                kernel_size=4.0,
                num_iterations=3,
                base_seed=42
            )

            assert result["empirical_power"] == 0.0
            assert result["iterations_run"] == 0
            mock_logger.error.assert_called()


class TestGeneratePowerCurve:
    """Tests for generate_power_curve function."""

    def test_generates_results_for_multiple_sizes_and_kernels(self):
        """Test generation across multiple sample sizes and kernels."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=4.0,
            num_iterations=2,
            random_seed=42
        )
        timeseries = np.random.randn(100, 1)
        regressors = np.random.randn(100, 2)
        sample_sizes = [10, 20]
        kernel_sizes = [4.0, 8.0]

        with patch('analysis.power_curve_generator.run_bootstrap_loop') as mock_loop:
            mock_loop.return_value = {
                "sample_size": 10,
                "kernel_size": 4.0,
                "empirical_power": 0.5,
                "mean_effect_size": 0.4,
                "mean_p_value": 0.05,
                "success_rate": 1.0,
                "iterations_run": 2,
                "total_iterations": 2
            }

            results = generate_power_curve(
                config=config,
                timeseries=timeseries,
                regressors=regressors,
                sample_sizes=sample_sizes,
                kernel_sizes=kernel_sizes
            )

            # Should have 2 sizes * 2 kernels = 4 results
            assert len(results) == 4
            mock_loop.assert_called()


class TestFitPowerCurveModel:
    """Tests for fit_power_curve_model function."""

    def test_fits_model_successfully(self):
        """Test that model fitting works with valid data."""
        results = [
            {"sample_size": 10, "empirical_power": 0.3, "kernel_size": 4.0},
            {"sample_size": 20, "empirical_power": 0.5, "kernel_size": 4.0},
            {"sample_size": 30, "empirical_power": 0.7, "kernel_size": 4.0},
            {"sample_size": 40, "empirical_power": 0.9, "kernel_size": 4.0},
        ]

        model, vif_stats = fit_power_curve_model(results)

        assert model is not None
        assert "feature_0" in vif_stats
        assert "feature_1" in vif_stats
        assert "feature_2" in vif_stats

    def test_raises_error_on_empty_results(self):
        """Test that empty results raise an error."""
        with pytest.raises(ValueError, match="No results to fit model"):
            fit_power_curve_model([])


class TestSavePowerCurves:
    """Tests for save_power_curves function."""

    def test_saves_valid_json(self):
        """Test that function saves valid JSON file."""
        results = [
            {"sample_size": 10, "empirical_power": 0.3, "kernel_size": 4.0},
            {"sample_size": 20, "empirical_power": 0.5, "kernel_size": 4.0},
        ]

        mock_model = Mock(
            params=np.array([0.1, 0.2, 0.3]),
            rsquared=0.85,
            rsquared_adj=0.82
        )
        vif_stats = {"feature_0": 1.2, "feature_1": 1.5, "feature_2": 1.1}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_curves.json"

            save_power_curves(results, mock_model, vif_stats, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "sample_sizes_tested" in data
            assert "empirical_rates" in data
            assert "detailed_results" in data
            assert "model_summary" in data
            assert data["sample_sizes_tested"] == [10, 20]