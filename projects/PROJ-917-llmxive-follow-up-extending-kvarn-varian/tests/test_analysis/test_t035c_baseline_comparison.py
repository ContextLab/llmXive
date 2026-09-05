"""
Tests for T035c: MLP vs Baseline comparison logic.
"""

import pytest
import numpy as np
import torch
from pathlib import Path
import json
import tempfile
import os

# Import the function to test
from analysis.stats import compare_mlp_vs_baseline, load_training_data, load_model_weights
from model_training.mlp_model import create_model


class TestBaselineComparison:
    """Test suite for baseline comparison logic."""

    @pytest.fixture
    def sample_data(self):
        """Create sample features and labels for testing."""
        # Create synthetic but realistic data
        np.random.seed(42)
        n_samples = 100

        # Generate variance values (avoiding zero)
        variances = np.abs(np.random.randn(n_samples)) + 0.1
        means = np.random.randn(n_samples) * 0.5

        features = np.column_stack([means, variances]).astype(np.float32)

        # Create labels with some relationship to variance
        # Baseline would be 1/variance, add some noise
        labels = (1.0 / variances) + np.random.randn(n_samples) * 0.1
        labels = labels.astype(np.float32)

        return features, labels

    @pytest.fixture
    def simple_mlp_model(self):
        """Create a simple MLP model for testing."""
        model = create_model()
        # Initialize with small weights
        with torch.no_grad():
            for param in model.parameters():
                param.normal_(0, 0.01)
        model.eval()
        return model

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_comparison_produces_valid_results(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that comparison produces valid JSON output with required fields."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        # Verify required fields exist
        required_fields = [
            "mlp_mse", "baseline_mse", "relative_improvement",
            "t_statistic", "p_value", "captures_nontrivial_relationship",
            "sample_size", "method"
        ]

        for field in required_fields:
            assert field in results, f"Missing required field: {field}"

        # Verify types
        assert isinstance(results["mlp_mse"], float)
        assert isinstance(results["baseline_mse"], float)
        assert isinstance(results["relative_improvement"], float)
        assert isinstance(results["p_value"], float)
        assert isinstance(results["captures_nontrivial_relationship"], bool)

        # Verify sample size
        assert results["sample_size"] == len(labels)

    def test_comparison_file_created(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that the output JSON file is actually written."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        # Ensure file doesn't exist yet
        assert not os.path.exists(output_path)

        compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        # Verify file exists
        assert os.path.exists(output_path)

        # Verify it's valid JSON
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)

        assert "mlp_mse" in loaded_results
        assert "baseline_mse" in loaded_results

    def test_mse_values_are_positive(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that MSE values are non-negative."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        assert results["mlp_mse"] >= 0
        assert results["baseline_mse"] >= 0

    def test_p_value_in_valid_range(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that p-value is in valid range [0, 1]."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        assert 0 <= results["p_value"] <= 1

    def test_t_statistic_is_numeric(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that t-statistic is a valid number."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        assert np.isfinite(results["t_statistic"])

    def test_relative_improvement_calculation(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that relative improvement is calculated correctly."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_comparison.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        # Verify the formula: (baseline_mse - mlp_mse) / baseline_mse
        expected_improvement = (results["baseline_mse"] - results["mlp_mse"]) / results["baseline_mse"]
        assert np.isclose(results["relative_improvement"], expected_improvement)

    def test_handles_small_variance(self, temp_output_dir):
        """Test that the comparison handles small variance values gracefully."""
        np.random.seed(123)
        n_samples = 50

        # Create features with very small variance
        variances = np.abs(np.random.randn(n_samples)) * 0.001 + 0.0001
        means = np.random.randn(n_samples) * 0.1

        features = np.column_stack([means, variances]).astype(np.float32)
        labels = (1.0 / variances) + np.random.randn(n_samples) * 0.01
        labels = labels.astype(np.float32)

        model = create_model()
        model.eval()

        output_path = os.path.join(temp_output_dir, "test_small_var.json")

        # Should not raise an exception
        results = compare_mlp_vs_baseline(model, features, labels, output_path)

        assert "mlp_mse" in results
        assert results["mlp_mse"] >= 0

    def test_captures_nontrivial_logic(self, simple_mlp_model, sample_data, temp_output_dir):
        """Test that captures_nontrivial_relationship is set based on p-value and improvement."""
        features, labels = sample_data
        output_path = os.path.join(temp_output_dir, "test_nontrivial.json")

        results = compare_mlp_vs_baseline(simple_mlp_model, features, labels, output_path)

        # The boolean should be True only if p < 0.05 AND improvement > 0
        expected = (results["p_value"] < 0.05) and (results["relative_improvement"] > 0)
        assert results["captures_nontrivial_relationship"] == expected