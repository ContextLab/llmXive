"""
Unit tests for power analysis module.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.evaluate.power_analysis import (
    FIXED_EFFECT_SIZE,
    calculate_mdes,
    run_power_analysis,
)


class TestPowerAnalysis:
    """Test cases for power analysis functions."""

    @pytest.fixture
    def temp_dataset(self):
        """Create a temporary dataset for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "test_dataset.parquet"

            # Create a synthetic dataset with known properties
            n_samples = 200
            n_predictors = 5

            data = {
                "experiment_id": range(n_samples),
                "milling_speed": np.random.uniform(100, 1000, n_samples),
                "milling_time": np.random.uniform(1, 24, n_samples),
                "ball_to_powder_ratio": np.random.uniform(1, 10, n_samples),
                "youngs_modulus": np.random.uniform(50, 200, n_samples),
                "density": np.random.uniform(2, 8, n_samples),
                "process_duration": np.random.uniform(1, 48, n_samples),
                "d10": np.random.uniform(1, 10, n_samples),
                "d50": np.random.uniform(10, 50, n_samples),
                "d90": np.random.uniform(50, 200, n_samples),
                "material_type": np.random.choice(
                    ["ceramic", "metal", "polymer"], n_samples
                ),
            }

            df = pd.DataFrame(data)
            df.to_parquet(dataset_path)

            yield str(dataset_path)

    def test_calculate_mdes_valid_input(self):
        """Test MDES calculation with valid inputs."""
        mdes = calculate_mdes(
            n_samples=200, n_predictors=5, power=0.80, alpha=0.05
        )
        assert isinstance(mdes, float)
        assert mdes >= 0

    def test_calculate_mdes_small_sample(self):
        """Test MDES calculation with small sample size."""
        mdes = calculate_mdes(
            n_samples=10, n_predictors=5, power=0.80, alpha=0.05
        )
        # Should return NaN or a very large value due to insufficient degrees of freedom
        assert np.isnan(mdes) or mdes > 1.0

    def test_calculate_mdes_invalid_params(self):
        """Test MDES calculation with invalid parameters."""
        with pytest.raises(ValueError):
            calculate_mdes(n_samples=0, n_predictors=5)

        with pytest.raises(ValueError):
            calculate_mdes(n_samples=100, n_predictors=0)

        with pytest.raises(ValueError):
            calculate_mdes(n_samples=100, n_predictors=5, power=1.5)

        with pytest.raises(ValueError):
            calculate_mdes(n_samples=100, n_predictors=5, alpha=-0.1)

    def test_fixed_effect_size_constant(self):
        """Test that the fixed effect size constant is set correctly."""
        assert FIXED_EFFECT_SIZE == 0.15

    def test_run_power_analysis_creates_output(self, temp_dataset):
        """Test that power analysis creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis_result.txt"

            results = run_power_analysis(temp_dataset, str(output_path))

            # Check that output file was created
            assert output_path.exists()

            # Check results dictionary
            assert "n_samples" in results
            assert "n_predictors" in results
            assert "minimum_detectable_effect_size_f2" in results
            assert results["n_samples"] == 200
            assert results["n_predictors"] == 6  # 6 numeric predictors (excluding d50)

    def test_power_analysis_output_contains_limitation_note(self, temp_dataset):
        """Test that output file contains the limitation note about fixed effect size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis_result.txt"

            run_power_analysis(temp_dataset, str(output_path))

            # Read and check content
            with open(output_path, "r") as f:
                content = f.read()

            assert "LIMITATION NOTE" in content
            assert "fixed effect size assumption" in content
            assert "f²=0.15" in content
            assert "indicative, not definitive" in content

    def test_power_analysis_file_not_found(self):
        """Test power analysis with non-existent dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis_result.txt"

            with pytest.raises(FileNotFoundError):
                run_power_analysis("non_existent.parquet", str(output_path))

    def test_power_analysis_insufficient_predictors(self):
        """Test power analysis with no predictors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "empty_predictors.parquet"
            output_path = Path(tmpdir) / "power_analysis_result.txt"

            # Create dataset with only target variable
            df = pd.DataFrame({"d50": [1, 2, 3, 4, 5]})
            df.to_parquet(dataset_path)

            with pytest.raises(ValueError, match="No predictor variables"):
                run_power_analysis(str(dataset_path), str(output_path))