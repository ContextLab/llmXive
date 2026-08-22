import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import numpy as np

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig
from src.data.benchmarks import generate_polynomial_surface_data

class TestBaselineValidation:
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory structure mimicking the project layout."""
        data_dir = tmp_path / "data" / "results"
        logs_dir = tmp_path / "data" / "logs"
        data_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        return str(tmp_path)

    def test_validate_generalization_runs(self, temp_output_dir):
        """
        Test that validate_generalization executes without error and produces the report.
        """
        # Setup config to use temp dirs
        config = ExperimentConfig(
            data_dir=os.path.join(temp_output_dir, "data", "results"),
            results_dir=os.path.join(temp_output_dir, "data", "results"),
            log_dir=os.path.join(temp_output_dir, "data", "logs")
        )

        # Generate a small dummy test file to satisfy T008c requirement
        # Shape: (N, T, D) where last dim is target
        # T008c produces data/results/test_data_polynomial.npy
        test_data_path = os.path.join(config.data_dir, "test_data_polynomial.npy")
        dummy_data = generate_polynomial_surface_data(n_samples=100, n_features=2, seed=42)
        # Ensure shape is (N, T, D) - assume T=10, D=3 (2 inputs + 1 target)
        # generate_polynomial_surface_data returns (N, features) usually.
        # We need to reshape to match loader expectations: (N, T, D)
        # Let's create a dummy array with shape (100, 10, 3)
        dummy_array = np.random.rand(100, 10, 3).astype(np.float32)
        np.save(test_data_path, dummy_array)

        runner = BaselineRunner(config)

        # Run validation
        result = runner.validate_generalization()

        # Assertions
        assert result is not None
        assert os.path.exists(runner.report_path)
        assert result.test_mae >= 0.0
        assert result.parameter_count > 0
        assert len(result.test_data_checksum) == 64  # SHA256 length

    def test_validate_generalization_fails_if_missing_data(self, temp_output_dir):
        """
        Test that validation fails loudly if test data is missing.
        """
        config = ExperimentConfig(
            data_dir=os.path.join(temp_output_dir, "data", "results"),
            results_dir=os.path.join(temp_output_dir, "data", "results"),
            log_dir=os.path.join(temp_output_dir, "data", "logs")
        )

        # Ensure test file does NOT exist
        test_data_path = os.path.join(config.data_dir, "test_data_polynomial.npy")
        if os.path.exists(test_data_path):
            os.remove(test_data_path)

        runner = BaselineRunner(config)

        with pytest.raises(FileNotFoundError, match="Test data not found"):
            runner.validate_generalization()

    def test_report_content(self, temp_output_dir):
        """
        Verify the generated report contains required sections.
        """
        config = ExperimentConfig(
            data_dir=os.path.join(temp_output_dir, "data", "results"),
            results_dir=os.path.join(temp_output_dir, "data", "results"),
            log_dir=os.path.join(temp_output_dir, "data", "logs")
        )

        # Create dummy data
        test_data_path = os.path.join(config.data_dir, "test_data_polynomial.npy")
        np.save(test_data_path, np.random.rand(50, 10, 3).astype(np.float32))

        runner = BaselineRunner(config)
        runner.validate_generalization()

        with open(runner.report_path, 'r') as f:
            content = f.read()

        assert "# Generalization Report" in content
        assert "Test MAE" in content
        assert "Parameter Count" in content
        assert "Polynomial Surfaces" in content
        assert "Generated at:" in content