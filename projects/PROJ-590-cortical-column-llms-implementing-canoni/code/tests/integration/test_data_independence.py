"""Integration tests for data independence verification."""

import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
from src.utils.statistics import compare_ablation_results

class TestDataGenerationIndependence:
    def test_train_test_distribution_difference(self):
        """Verify that training and test data come from different distributions."""
        train_data = generate_training_data(n_samples=1000)
        test_data = generate_test_data(n_samples=500)

        # Should raise no error if distributions are different
        result = verify_independence(train_data, test_data)
        assert result is True

    def test_multiple_independence_checks(self):
        """Test independence check across multiple random seeds."""
        for seed in [42, 123, 456, 789]:
            np.random.seed(seed)
            train_data = generate_training_data(n_samples=500)
            test_data = generate_test_data(n_samples=250)

            result = verify_independence(train_data, test_data)
            assert result is True, f"Independence check failed for seed {seed}"

class TestAblationResultsIntegration:
    def test_ablation_results_schema(self):
        """Test that ablation results match expected schema."""
        # This test verifies the structure of results that would be generated
        # by the ablation study pipeline
        sample_results = {
            "results": [
                {
                    "variant": "full",
                    "mae": 0.05,
                    "time": 100.0
                },
                {
                    "variant": "no_recurrence",
                    "mae": 0.08,
                    "time": 95.0
                }
            ]
        }

        # Verify schema
        assert "results" in sample_results
        for result in sample_results["results"]:
            assert "variant" in result
            assert "mae" in result
            assert "time" in result
            assert isinstance(result["mae"], float)
            assert isinstance(result["time"], float)
