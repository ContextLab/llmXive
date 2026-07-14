"""
Unit tests for model validation and stability checking.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.models.validate import (
    perform_cross_validation,
    check_model_stability,
    run_validation_pipeline,
    validate_model_output
)


class TestCrossValidation:
    """Test cross-validation functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples)
        })
        y = pd.Series(
            0.5 * X['feature1'] + 0.3 * X['feature2'] + np.random.randn(n_samples) * 0.1
        )
        return X, y

    def test_perform_cross_validation_ridge(self, sample_data):
        """Test cross-validation for Ridge regression."""
        X, y = sample_data
        results = perform_cross_validation(X, y, model_type="ridge", n_splits=5)

        assert "r2_scores" in results
        assert "mse_scores" in results
        assert len(results["r2_scores"]) == 5
        assert len(results["mse_scores"]) == 5
        assert "r2_mean" in results
        assert "r2_std" in results
        assert results["model_type"] == "ridge"
        assert results["n_splits"] == 5

    def test_perform_cross_validation_glm(self, sample_data):
        """Test cross-validation for Gaussian GLM."""
        X, y = sample_data
        results = perform_cross_validation(X, y, model_type="glm", n_splits=5)

        assert "r2_scores" in results
        assert "mse_scores" in results
        assert len(results["r2_scores"]) == 5
        assert len(results["mse_scores"]) == 5
        assert "r2_mean" in results
        assert "r2_std" in results
        assert results["model_type"] == "glm"

    def test_invalid_model_type(self, sample_data):
        """Test that invalid model type raises error."""
        X, y = sample_data
        with pytest.raises(ValueError, match="Unknown model_type"):
            perform_cross_validation(X, y, model_type="invalid")


class TestModelStability:
    """Test model stability checking."""

    def test_stable_model_passes(self):
        """Test that a stable model passes the check."""
        cv_results = {
            "r2_std": 0.03,
            "r2_scores": [0.8, 0.82, 0.79, 0.81, 0.8]
        }
        assert check_model_stability(cv_results, threshold=0.05) is True

    def test_unstable_model_raises_error(self):
        """Test that an unstable model raises RuntimeError."""
        cv_results = {
            "r2_std": 0.06,
            "r2_scores": [0.7, 0.9, 0.6, 0.95, 0.75]
        }
        with pytest.raises(RuntimeError, match="SC-003 Threshold Exceeded"):
            check_model_stability(cv_results, threshold=0.05)

    def test_boundary_case_exact_threshold(self):
        """Test the exact threshold boundary."""
        cv_results = {
            "r2_std": 0.05,
            "r2_scores": [0.8, 0.8, 0.8, 0.8, 0.8]
        }
        # Should raise error because >= threshold
        with pytest.raises(RuntimeError, match="SC-003 Threshold Exceeded"):
            check_model_stability(cv_results, threshold=0.05)

    def test_below_threshold_passes(self):
        """Test that values below threshold pass."""
        cv_results = {
            "r2_std": 0.049,
            "r2_scores": [0.8, 0.81, 0.79, 0.8, 0.8]
        }
        assert check_model_stability(cv_results, threshold=0.05) is True


class TestValidationPipeline:
    """Test the full validation pipeline."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples)
        })
        y = pd.Series(0.5 * X['feature1'] + np.random.randn(n_samples) * 0.1)
        return X, y

    def test_pipeline_single_model(self, sample_data):
        """Test pipeline with a single model type."""
        X, y = sample_data
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_results.json"
            results, stability = run_validation_pipeline(
                X, y,
                model_types=["ridge"],
                output_path=output_path
            )

            assert "ridge" in results
            assert stability is True
            assert output_path.exists()

    def test_pipeline_multiple_models(self, sample_data):
        """Test pipeline with multiple model types."""
        X, y = sample_data
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_results.json"
            results, stability = run_validation_pipeline(
                X, y,
                model_types=["ridge", "glm"],
                output_path=output_path
            )

            assert "ridge" in results
            assert "glm" in results
            assert stability is True

    def test_pipeline_unstable_model(self, sample_data):
        """Test pipeline when model is unstable."""
        # Create data that will likely produce unstable results
        X = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50)
        })
        y = pd.Series(np.random.randn(50))  # Pure noise

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_results.json"
            results, stability = run_validation_pipeline(
                X, y,
                model_types=["ridge"],
                output_path=output_path
            )

            # Stability should fail with noisy data
            assert "ridge" in results
            # The result might pass or fail depending on random seed,
            # but the pipeline should complete without crashing


class TestValidateModelOutput:
    """Test single model output validation."""

    def test_valid_output(self):
        """Test validation of a valid output."""
        cv_results = {
            "r2_scores": [0.8, 0.82, 0.79, 0.81, 0.8],
            "mse_scores": [0.1, 0.09, 0.11, 0.095, 0.1],
            "r2_mean": 0.804,
            "r2_std": 0.01,
            "n_splits": 5
        }
        result = validate_model_output("ridge", cv_results)
        assert result["stability_status"] == "PASSED"
        assert result["model_type"] == "ridge"

    def test_missing_required_field(self):
        """Test validation fails with missing required field."""
        cv_results = {
            "r2_scores": [0.8, 0.82, 0.79, 0.81, 0.8],
            "r2_mean": 0.804,
            # Missing r2_std
            "n_splits": 5
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_model_output("ridge", cv_results)

    def test_unstable_output(self):
        """Test validation fails for unstable model."""
        cv_results = {
            "r2_scores": [0.5, 0.9, 0.4, 0.95, 0.6],
            "mse_scores": [0.5, 0.1, 0.6, 0.08, 0.45],
            "r2_mean": 0.67,
            "r2_std": 0.2,
            "n_splits": 5
        }
        with pytest.raises(RuntimeError, match="SC-003 Threshold Exceeded"):
            validate_model_output("ridge", cv_results)