"""
Unit tests for code/evaluation/stats.py (T042c).
Tests statistical analysis functions: load_data_for_analysis, run_beta_regression,
run_logistic_regression, and run_spearman_correlation.
"""
import json
import math
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the module under test
# Note: The import path assumes the tests are run with code/ in sys.path or PYTHONPATH
from evaluation.stats import (
    StatisticalAnalysisError,
    load_data_for_analysis,
    run_beta_regression,
    run_logistic_regression,
    run_spearman_correlation,
)


class TestLoadDataForAnalysis:
    """Tests for load_data_for_analysis function."""

    def test_load_valid_data(self, tmp_path):
        """Test loading valid benchmark and feature data."""
        # Create temporary data files
        benchmark_data = [
            {
                "trace_id": "trace_001",
                "baseline_acc": 0.95,
                "compressed_acc": 0.92,
                "delta_acc": 0.03,
                "fidelity_loss": 0.08
            },
            {
                "trace_id": "trace_002",
                "baseline_acc": 0.98,
                "compressed_acc": 0.96,
                "delta_acc": 0.02,
                "fidelity_loss": 0.04
            }
        ]

        feature_data = [
            {
                "trace_id": "trace_001",
                "sequence_entropy": 2.5,
                "tool_repetition_freq": 0.3,
                "arg_semantic_variance": 0.8
            },
            {
                "trace_id": "trace_002",
                "sequence_entropy": 1.8,
                "tool_repetition_freq": 0.5,
                "arg_semantic_variance": 0.6
            }
        ]

        benchmark_file = tmp_path / "benchmark_results.json"
        feature_file = tmp_path / "feature_matrix.csv"

        with open(benchmark_file, "w") as f:
            json.dump(benchmark_data, f)

        with open(feature_file, "w") as f:
            f.write("trace_id,sequence_entropy,tool_repetition_freq,arg_semantic_variance\n")
            for row in feature_data:
                f.write(f"{row['trace_id']},{row['sequence_entropy']},{row['tool_repetition_freq']},{row['arg_semantic_variance']}\n")

        # Test loading
        result = load_data_for_analysis(
            benchmark_results_path=str(benchmark_file),
            feature_matrix_path=str(feature_file)
        )

        assert len(result) == 2
        assert result[0]["trace_id"] == "trace_001"
        assert "fidelity_loss" in result[0]
        assert "sequence_entropy" in result[0]
        assert "tool_repetition_freq" in result[0]
        assert "arg_semantic_variance" in result[0]

    def test_load_data_with_mismatched_traces(self, tmp_path):
        """Test handling of trace ID mismatches between files."""
        benchmark_data = [
            {
                "trace_id": "trace_001",
                "baseline_acc": 0.95,
                "compressed_acc": 0.92,
                "fidelity_loss": 0.08
            }
        ]

        feature_data = [
            {
                "trace_id": "trace_002",  # Different ID
                "sequence_entropy": 2.5,
                "tool_repetition_freq": 0.3,
                "arg_semantic_variance": 0.8
            }
        ]

        benchmark_file = tmp_path / "benchmark_results.json"
        feature_file = tmp_path / "feature_matrix.csv"

        with open(benchmark_file, "w") as f:
            json.dump(benchmark_data, f)

        with open(feature_file, "w") as f:
            f.write("trace_id,sequence_entropy,tool_repetition_freq,arg_semantic_variance\n")
            for row in feature_data:
                f.write(f"{row['trace_id']},{row['sequence_entropy']},{row['tool_repetition_freq']},{row['arg_semantic_variance']}\n")

        # Should return empty list when no matching traces
        result = load_data_for_analysis(
            benchmark_results_path=str(benchmark_file),
            feature_matrix_path=str(feature_file)
        )

        assert len(result) == 0

    def test_load_missing_file(self, tmp_path):
        """Test error handling for missing input files."""
        with pytest.raises(FileNotFoundError):
            load_data_for_analysis(
                benchmark_results_path=str(tmp_path / "nonexistent.json"),
                feature_matrix_path=str(tmp_path / "nonexistent.csv")
            )

    def test_load_data_with_nan_values(self, tmp_path):
        """Test filtering of NaN values in fidelity_loss."""
        benchmark_data = [
            {
                "trace_id": "trace_001",
                "baseline_acc": 0.95,
                "compressed_acc": 0.92,
                "fidelity_loss": 0.08
            },
            {
                "trace_id": "trace_002",
                "baseline_acc": 0.98,
                "compressed_acc": 0.96,
                "fidelity_loss": float('nan')  # NaN value
            }
        ]

        feature_data = [
            {
                "trace_id": "trace_001",
                "sequence_entropy": 2.5,
                "tool_repetition_freq": 0.3,
                "arg_semantic_variance": 0.8
            },
            {
                "trace_id": "trace_002",
                "sequence_entropy": 1.8,
                "tool_repetition_freq": 0.5,
                "arg_semantic_variance": 0.6
            }
        ]

        benchmark_file = tmp_path / "benchmark_results.json"
        feature_file = tmp_path / "feature_matrix.csv"

        with open(benchmark_file, "w") as f:
            json.dump(benchmark_data, f)

        with open(feature_file, "w") as f:
            f.write("trace_id,sequence_entropy,tool_repetition_freq,arg_semantic_variance\n")
            for row in feature_data:
                f.write(f"{row['trace_id']},{row['sequence_entropy']},{row['tool_repetition_freq']},{row['arg_semantic_variance']}\n")

        result = load_data_for_analysis(
            benchmark_results_path=str(benchmark_file),
            feature_matrix_path=str(feature_file)
        )

        # Should filter out trace with NaN fidelity_loss
        assert len(result) == 1
        assert result[0]["trace_id"] == "trace_001"


class TestRunBetaRegression:
    """Tests for run_beta_regression function."""

    def test_beta_regression_basic(self):
        """Test basic beta regression with valid data."""
        # Create synthetic data for testing
        n_samples = 50
        np.random.seed(42)
        
        # Generate bounded [0,1] fidelity_loss values
        fidelity_loss = np.random.beta(2, 5, n_samples)
        sequence_entropy = np.random.normal(2.0, 0.5, n_samples)
        tool_repetition = np.random.normal(0.4, 0.2, n_samples)
        arg_variance = np.random.normal(0.6, 0.3, n_samples)

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss": fidelity_loss[i],
                "sequence_entropy": sequence_entropy[i],
                "tool_repetition_freq": tool_repetition[i],
                "arg_semantic_variance": arg_variance[i]
            })

        result = run_beta_regression(data)

        assert "beta_coefficients" in result
        assert "p_values" in result
        assert "model_summary" in result
        assert result["method_used"] == "beta_regression"
        assert "sequence_entropy" in result["beta_coefficients"]
        assert "tool_repetition_freq" in result["beta_coefficients"]
        assert "arg_semantic_variance" in result["beta_coefficients"]

    def test_beta_regression_with_edge_cases(self):
        """Test beta regression with values near boundaries (0 and 1)."""
        n_samples = 30
        np.random.seed(123)
        
        # Include some values very close to 0 and 1
        fidelity_loss = np.concatenate([
            np.array([0.001, 0.999]),  # Edge cases
            np.random.beta(2, 5, n_samples - 2)
        ])
        
        sequence_entropy = np.random.normal(2.0, 0.5, n_samples)
        tool_repetition = np.random.normal(0.4, 0.2, n_samples)
        arg_variance = np.random.normal(0.6, 0.3, n_samples)

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss": fidelity_loss[i],
                "sequence_entropy": sequence_entropy[i],
                "tool_repetition_freq": tool_repetition[i],
                "arg_semantic_variance": arg_variance[i]
            })

        # Should handle edge cases with epsilon transformation
        result = run_beta_regression(data)

        assert "beta_coefficients" in result
        assert result["method_used"] == "beta_regression"

    def test_beta_regression_insufficient_data(self):
        """Test error handling for insufficient data points."""
        data = [
            {
                "fidelity_loss": 0.1,
                "sequence_entropy": 2.0,
                "tool_repetition_freq": 0.3,
                "arg_semantic_variance": 0.5
            }
        ]

        with pytest.raises(StatisticalAnalysisError):
            run_beta_regression(data)

    def test_beta_regression_convergence_failure(self):
        """Test fallback to Spearman correlation when beta regression fails."""
        # Create data that might cause convergence issues (perfect separation)
        data = [
            {
                "fidelity_loss": 0.1,
                "sequence_entropy": 1.0,
                "tool_repetition_freq": 0.1,
                "arg_semantic_variance": 0.1
            },
            {
                "fidelity_loss": 0.9,
                "sequence_entropy": 5.0,
                "tool_repetition_freq": 0.9,
                "arg_semantic_variance": 0.9
            }
            # Only 2 points with perfect separation
        ]

        # This should either raise an error or fallback gracefully
        # depending on implementation
        try:
            result = run_beta_regression(data)
            # If it succeeds, it should have the correct structure
            assert "method_used" in result
        except StatisticalAnalysisError:
            # Expected if convergence fails and no fallback implemented
            pass


class TestRunLogisticRegression:
    """Tests for run_logistic_regression function."""

    def test_logistic_regression_basic(self):
        """Test basic logistic regression with binarized target."""
        n_samples = 50
        np.random.seed(42)
        
        # Generate binary target (0 or 1)
        target = np.random.binomial(1, 0.5, n_samples)
        sequence_entropy = np.random.normal(2.0, 0.5, n_samples)
        tool_repetition = np.random.normal(0.4, 0.2, n_samples)
        arg_variance = np.random.normal(0.6, 0.3, n_samples)

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss_binary": target[i],
                "sequence_entropy": sequence_entropy[i],
                "tool_repetition_freq": tool_repetition[i],
                "arg_semantic_variance": arg_variance[i]
            })

        result = run_logistic_regression(data)

        assert "coefficients" in result
        assert "p_values" in result
        assert "model_summary" in result
        assert result["method_used"] == "logistic_regression"

    def test_logistic_regression_imbalanced_data(self):
        """Test logistic regression with imbalanced classes."""
        n_samples = 50
        np.random.seed(42)
        
        # Highly imbalanced: 90% class 0, 10% class 1
        target = np.concatenate([
            np.zeros(int(n_samples * 0.9)),
            np.ones(int(n_samples * 0.1))
        ])
        sequence_entropy = np.random.normal(2.0, 0.5, n_samples)
        tool_repetition = np.random.normal(0.4, 0.2, n_samples)
        arg_variance = np.random.normal(0.6, 0.3, n_samples)

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss_binary": target[i],
                "sequence_entropy": sequence_entropy[i],
                "tool_repetition_freq": tool_repetition[i],
                "arg_semantic_variance": arg_variance[i]
            })

        result = run_logistic_regression(data)

        assert "coefficients" in result
        assert result["method_used"] == "logistic_regression"


class TestRunSpearmanCorrelation:
    """Tests for run_spearman_correlation function."""

    def test_spearman_correlation_basic(self):
        """Test basic Spearman correlation calculation."""
        n_samples = 50
        np.random.seed(42)
        
        # Generate data with known correlation
        x = np.random.normal(0, 1, n_samples)
        y = x * 2 + np.random.normal(0, 0.5, n_samples)  # Positive correlation

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss": (y[i] - y.min()) / (y.max() - y.min()),  # Normalize to [0,1]
                "sequence_entropy": x[i],
                "tool_repetition_freq": np.random.normal(0.4, 0.2, 1)[0],
                "arg_semantic_variance": np.random.normal(0.6, 0.3, 1)[0]
            })

        result = run_spearman_correlation(data)

        assert "spearman_coefficients" in result
        assert "p_values" in result
        assert result["method_used"] == "spearman_correlation"
        
        # Check that correlation coefficient is in valid range [-1, 1]
        for coef in result["spearman_coefficients"].values():
            assert -1.0 <= coef <= 1.0

    def test_spearman_correlation_perfect_correlation(self):
        """Test Spearman correlation with perfect linear relationship."""
        n_samples = 20
        np.random.seed(42)
        
        x = np.linspace(0, 10, n_samples)
        y = x * 3  # Perfect positive correlation

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss": (y[i] - y.min()) / (y.max() - y.min()),
                "sequence_entropy": x[i],
                "tool_repetition_freq": 0.5,
                "arg_semantic_variance": 0.5
            })

        result = run_spearman_correlation(data)

        # Perfect correlation should be close to 1.0
        assert abs(result["spearman_coefficients"]["sequence_entropy"] - 1.0) < 0.01

    def test_spearman_correlation_no_correlation(self):
        """Test Spearman correlation with random uncorrelated data."""
        n_samples = 100
        np.random.seed(42)
        
        x = np.random.normal(0, 1, n_samples)
        y = np.random.normal(0, 1, n_samples)  # No correlation

        data = []
        for i in range(n_samples):
            data.append({
                "fidelity_loss": (y[i] - y.min()) / (y.max() - y.min()) if y.max() != y.min() else 0.5,
                "sequence_entropy": x[i],
                "tool_repetition_freq": 0.5,
                "arg_semantic_variance": 0.5
            })

        result = run_spearman_correlation(data)

        # Correlation should be close to 0 (with some tolerance for randomness)
        assert abs(result["spearman_coefficients"]["sequence_entropy"]) < 0.3


class TestStatisticalAnalysisError:
    """Tests for StatisticalAnalysisError exception."""

    def test_error_creation(self):
        """Test that StatisticalAnalysisError can be created with message."""
        error = StatisticalAnalysisError("Test error message")
        assert str(error) == "Test error message"

    def test_error_with_cause(self):
        """Test that StatisticalAnalysisError can wrap another exception."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = StatisticalAnalysisError("Analysis failed", e)
            assert "Analysis failed" in str(error)
            assert error.__cause__ is not None