"""
Integration test for T019c: Aggregation logic for static model evaluation scores.

Tests that the aggregation script correctly computes mean and variance
of metrics across multiple seeds and saves the results.
"""
import os
import json
import tempfile
import shutil
import pytest
import numpy as np

# Import the function to test
from models.aggregate_static_results import aggregate_metrics, save_aggregated_results


class TestAggregation:
    """Test suite for aggregation logic."""

    @pytest.fixture
    def sample_eval_data(self):
        """Create sample evaluation data with multiple seeds."""
        return {
            "seeds": [
                {"seed": 0, "metrics": {"accuracy": 0.85, "precision": 0.84, "recall": 0.86, "f1": 0.85}},
                {"seed": 1, "metrics": {"accuracy": 0.87, "precision": 0.86, "recall": 0.88, "f1": 0.87}},
                {"seed": 2, "metrics": {"accuracy": 0.83, "precision": 0.82, "recall": 0.84, "f1": 0.83}},
            ]
        }

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_aggregate_metrics_computation(self, sample_eval_data):
        """Test that mean and std are computed correctly."""
        result = aggregate_metrics(sample_eval_data)

        # Check n_seeds
        assert result["n_seeds"] == 3

        # Check mean accuracy: (0.85 + 0.87 + 0.83) / 3 = 0.85
        assert np.isclose(result["metrics"]["mean_accuracy"], 0.85, atol=1e-5)

        # Check std accuracy: sqrt(((0.0)^2 + (0.02)^2 + (-0.02)^2)/3) ≈ 0.0163
        expected_std = np.std([0.85, 0.87, 0.83])
        assert np.isclose(result["metrics"]["std_accuracy"], expected_std, atol=1e-5)

        # Check that seed_values are populated
        assert len(result["seed_values"]) > 0

    def test_aggregate_metrics_missing_keys(self, temp_output_dir):
        """Test handling of missing metric keys in some seeds."""
        partial_data = {
            "seeds": [
                {"seed": 0, "metrics": {"accuracy": 0.85}},
                {"seed": 1, "metrics": {"accuracy": 0.87, "precision": 0.86}},
                {"seed": 2, "metrics": {"accuracy": 0.83}},
            ]
        }

        result = aggregate_metrics(partial_data)

        # Accuracy should be aggregated
        assert "mean_accuracy" in result["metrics"]
        # Precision should be skipped or handled gracefully
        # (depending on implementation, it might be missing or have a warning)

    def test_save_aggregated_results(self, sample_eval_data, temp_output_dir):
        """Test that results are saved correctly to JSON."""
        aggregated = aggregate_metrics(sample_eval_data)
        output_path = os.path.join(temp_output_dir, "test_aggregated.json")

        save_aggregated_results(aggregated, output_path)

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["n_seeds"] == 3
        assert "mean_accuracy" in saved_data["metrics"]
        assert "std_accuracy" in saved_data["metrics"]

    def test_empty_seeds_raises_error(self):
        """Test that empty seeds list raises ValueError."""
        empty_data = {"seeds": []}
        with pytest.raises(ValueError, match="No seed results found"):
            aggregate_metrics(empty_data)
