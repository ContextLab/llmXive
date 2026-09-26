"""
Unit tests for GLM fitter module.

Tests cover:
- GLM fitting on synthetic data
- Effect size estimation
- Convergence tracking
- Batch processing
- Error handling
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from code.analysis.glm_fitter import (
    GLMFitError,
    fit_glm,
    estimate_effect_size,
    fit_glm_batch
)


class TestFitGLM:
    """Tests for the fit_glm function."""

    def test_basic_glm_fit(self):
        """Test basic GLM fitting on simple linear data."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 1)
        y = 2 * X.flatten() + np.random.randn(n) * 0.5

        results, conv_info = fit_glm(y, X)

        assert results is not None
        assert conv_info["converged"] is True
        assert conv_info["max_iterations"] == 100
        assert conv_info["tolerance"] == 1e-4
        assert conv_info["n_iterations"] > 0
        assert "converged" in conv_info["message"]

    def test_glm_with_custom_parameters(self):
        """Test GLM fitting with custom max_iter and tol."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 1)
        y = 2 * X.flatten() + np.random.randn(n) * 0.5

        results, conv_info = fit_glm(y, X, max_iter=50, tol=1e-5)

        assert results is not None
        assert conv_info["max_iterations"] == 50
        assert conv_info["tolerance"] == 1e-5

    def test_glm_empty_input(self):
        """Test GLM fitting with empty arrays."""
        X = np.array([]).reshape(0, 1)
        y = np.array([])

        with pytest.raises(GLMFitError, match="cannot be empty"):
            fit_glm(y, X)

    def test_glm_mismatched_dimensions(self):
        """Test GLM fitting with mismatched X and y dimensions."""
        X = np.random.randn(100, 1)
        y = np.random.randn(50)

        with pytest.raises(GLMFitError, match="must match"):
            fit_glm(y, X)

    def test_glm_none_input(self):
        """Test GLM fitting with None inputs."""
        with pytest.raises(GLMFitError, match="cannot be None"):
            fit_glm(None, np.random.randn(10, 1))

        with pytest.raises(GLMFitError, match="cannot be None"):
            fit_glm(np.random.randn(10), None)


class TestEstimateEffectSize:
    """Tests for the estimate_effect_size function."""

    def test_effect_size_calculation(self):
        """Test effect size estimation on known data."""
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 1)
        y = 1.5 * X.flatten() + np.random.randn(n) * 0.3

        results, _ = fit_glm(y, X)
        d = estimate_effect_size(results, coefficient_idx=1)

        assert isinstance(d, float)
        assert not np.isnan(d)
        assert not np.isinf(d)
        # With beta=1.5 and sigma_residual ~0.3, d should be ~5.0
        assert 4.0 < d < 6.0

    def test_effect_size_zero_residual(self):
        """Test effect size when residual std is zero."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 1)
        # Perfect linear relationship
        y = 2 * X.flatten()

        results, _ = fit_glm(y, X)
        d = estimate_effect_size(results, coefficient_idx=1)

        # Should return inf for non-zero beta
        assert np.isinf(d)

    def test_effect_size_invalid_index(self):
        """Test effect size with invalid coefficient index."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 1)
        y = np.random.randn(n)

        results, _ = fit_glm(y, X)

        with pytest.raises(ValueError, match="exceeds number of parameters"):
            estimate_effect_size(results, coefficient_idx=10)

    def test_effect_size_none_results(self):
        """Test effect size with None results."""
        with pytest.raises(ValueError, match="Cannot estimate effect size from None"):
            estimate_effect_size(None)


class TestFitGLMBatch:
    """Tests for the fit_glm_batch function."""

    def test_batch_processing(self):
        """Test batch processing of multiple ROIs."""
        np.random.seed(42)
        n = 100
        design_matrix = np.random.randn(n, 1)

        roi_data = {
            "roi_1": np.random.randn(n),
            "roi_2": np.random.randn(n),
            "roi_3": np.random.randn(n)
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "convergence_log.json"

            result = fit_glm_batch(
                roi_data=roi_data,
                design_matrix=design_matrix,
                output_path=output_path,
                iteration_id=0
            )

            # Check structure
            assert "effect_sizes" in result
            assert "p_values" in result
            assert "convergence_logs" in result
            assert "summary" in result

            # Check counts
            assert len(result["effect_sizes"]) == 3
            assert len(result["p_values"]) == 3
            assert len(result["convergence_logs"]) == 3

            # Check summary
            assert result["summary"]["total_rois"] == 3
            assert result["summary"]["successful_fits"] == 3
            assert result["summary"]["failed_fits"] == 0

            # Check file was written
            assert output_path.exists()
            with open(output_path, 'r') as f:
                logs = json.load(f)
            assert len(logs) == 3
            assert all("iteration_id" in log for log in logs)
            assert all("converged" in log for log in logs)

    def test_batch_with_failed_fits(self):
        """Test batch processing with some failed fits."""
        np.random.seed(42)
        n = 100
        design_matrix = np.random.randn(n, 1)

        roi_data = {
            "roi_good": np.random.randn(n),
            "roi_bad": np.array([0.0] * n)  # Might cause issues
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "convergence_log.json"

            result = fit_glm_batch(
                roi_data=roi_data,
                design_matrix=design_matrix,
                output_path=output_path,
                iteration_id=1
            )

            # Should have at least one successful fit
            assert len(result["effect_sizes"]) >= 1
            assert len(result["convergence_logs"]) == 2

            # Check iteration ID in logs
            for log in result["convergence_logs"]:
                assert log["iteration_id"] == 1

    def test_batch_without_output_path(self):
        """Test batch processing without output path."""
        np.random.seed(42)
        n = 100
        design_matrix = np.random.randn(n, 1)

        roi_data = {
            "roi_1": np.random.randn(n),
            "roi_2": np.random.randn(n)
        }

        result = fit_glm_batch(
            roi_data=roi_data,
            design_matrix=design_matrix,
            output_path=None,
            iteration_id=0
        )

        assert "effect_sizes" in result
        assert "convergence_logs" in result
        # No file should be written
        # (we can't easily test this without checking filesystem,
        # but the function should work without output_path)


class TestIntegration:
    """Integration tests for the GLM fitter module."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from data to effect size estimation."""
        np.random.seed(42)
        n = 200

        # Generate realistic fMRI-like data
        time_series = np.random.randn(n) * 2 + 1  # Mean=1, std=2
        design = np.random.randn(n, 1)

        # Fit GLM
        results, conv_info = fit_glm(time_series, design)

        assert results is not None
        assert conv_info["converged"]

        # Estimate effect size
        d = estimate_effect_size(results)

        assert isinstance(d, float)
        assert not np.isnan(d)

        # Batch process
        roi_data = {"motor_roi": time_series}
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_convergence.json"

            batch_result = fit_glm_batch(
                roi_data=roi_data,
                design_matrix=design,
                output_path=output_path,
                iteration_id=5
            )

            assert len(batch_result["effect_sizes"]) == 1
            assert batch_result["summary"]["successful_fits"] == 1

            # Verify file content
            with open(output_path, 'r') as f:
                logs = json.load(f)
            assert logs[0]["iteration_id"] == 5
            assert logs[0]["converged"] is True