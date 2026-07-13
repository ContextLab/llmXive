"""
Integration tests for T029: Scaling Confidence Interval Analysis.
"""
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.scaling_ci import (
    bootstrap_power_law_ci,
    load_scaling_results_for_bootstrap,
    run_scaling_ci_analysis,
)


class TestScalingCIIntegration:
    """Integration tests for scaling confidence interval computation."""

    @pytest.fixture
    def sample_scaling_data(self, tmp_path):
        """Create sample scaling data for testing."""
        data = {
            "num_agents": [3, 5, 7],
            "specialization_index": [1.5, 2.1, 2.6],
            "retrieval_efficiency": [0.85, 0.78, 0.72],
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "scaling_data.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def sample_scaling_data_insufficient(self, tmp_path):
        """Create insufficient scaling data (only 2 points)."""
        data = {
            "num_agents": [3, 5],
            "specialization_index": [1.5, 2.1],
            "retrieval_efficiency": [0.85, 0.78],
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "scaling_data_insufficient.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def sample_scaling_data_with_zeros(self, tmp_path):
        """Create scaling data with zero values."""
        data = {
            "num_agents": [0, 3, 5, 7],
            "specialization_index": [0.0, 1.5, 2.1, 2.6],
            "retrieval_efficiency": [0.0, 0.85, 0.78, 0.72],
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "scaling_data_zeros.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    def test_load_scaling_data_valid(self, sample_scaling_data):
        """Test loading valid scaling data."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data)
        assert len(df) == 3
        assert "num_agents" in df.columns
        assert "specialization_index" in df.columns
        assert "retrieval_efficiency" in df.columns

    def test_load_scaling_data_missing_file(self):
        """Test loading missing scaling data raises error."""
        with pytest.raises(FileNotFoundError):
            load_scaling_results_for_bootstrap(Path("/nonexistent/path.csv"))

    def test_load_scaling_data_missing_columns(self, tmp_path):
        """Test loading data with missing columns raises error."""
        data = {"num_agents": [3, 5, 7], "other_col": [1, 2, 3]}
        df = pd.DataFrame(data)
        csv_path = tmp_path / "bad_data.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_scaling_results_for_bootstrap(csv_path)

    def test_bootstrap_power_law_ci_valid_data(self, sample_scaling_data):
        """Test bootstrap CI computation with valid data."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data)

        result = bootstrap_power_law_ci(
            df, "specialization_index", n_bootstrap=100
        )

        assert "exponent" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert result["n_bootstrap"] == 100
        assert result["metric"] == "specialization_index"
        assert math.isfinite(result["exponent"])

    def test_bootstrap_power_law_ci_insufficient_data(
        self, sample_scaling_data_insufficient
    ):
        """Test bootstrap CI with insufficient data points."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data_insufficient)

        result = bootstrap_power_law_ci(
            df, "specialization_index", n_bootstrap=100
        )

        # Should warn and return NaN or handle gracefully
        assert result["metric"] == "specialization_index"
        # May return NaN or a warning
        assert "warning" in result or math.isnan(result["exponent"])

    def test_bootstrap_power_law_ci_with_zeros(self, sample_scaling_data_with_zeros):
        """Test bootstrap CI with zero values (should filter them out)."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data_with_zeros)

        result = bootstrap_power_law_ci(
            df, "specialization_index", n_bootstrap=100
        )

        # Should handle zeros by filtering
        assert result["metric"] == "specialization_index"
        # Should have fewer samples used if zeros were filtered
        assert "n_samples_used" in result

    def test_run_scaling_ci_analysis_full_pipeline(self, sample_scaling_data, tmp_path):
        """Test full analysis pipeline with output file."""
        output_path = tmp_path / "test_scaling_ci.json"

        results = run_scaling_ci_analysis(
            data_path=sample_scaling_data,
            output_path=output_path,
            n_bootstrap=100,
        )

        # Check file was written
        assert output_path.exists()

        # Check JSON structure
        with open(output_path) as f:
            saved_results = json.load(f)

        assert "specialization_index" in saved_results
        assert "retrieval_efficiency" in saved_results
        assert "metadata" in saved_results

        # Check metadata
        assert saved_results["metadata"]["n_bootstrap"] == 100
        assert saved_results["metadata"]["confidence_level"] == 0.95

    def test_run_scaling_ci_analysis_default_paths(self, sample_scaling_data, tmp_path, monkeypatch):
        """Test analysis with default output path."""
        # Mock the default output path
        expected_output = tmp_path / "results" / "scaling_confidence_intervals.json"
        expected_output.parent.mkdir(parents=True, exist_ok=True)

        # Run with default output
        results = run_scaling_ci_analysis(
            data_path=sample_scaling_data,
            output_path=expected_output,
            n_bootstrap=50,
        )

        assert expected_output.exists()
        with open(expected_output) as f:
            saved = json.load(f)
        assert "specialization_index" in saved

    def test_bootstrap_ci_reproducibility(self, sample_scaling_data):
        """Test that bootstrap results are reproducible with fixed seed."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data)

        # Set seed
        np.random.seed(42)
        result1 = bootstrap_power_law_ci(df, "specialization_index", n_bootstrap=50)

        # Reset seed
        np.random.seed(42)
        result2 = bootstrap_power_law_ci(df, "specialization_index", n_bootstrap=50)

        # Results should be identical
        assert result1["exponent"] == result2["exponent"]
        assert result1["ci_lower"] == result2["ci_lower"]
        assert result1["ci_upper"] == result2["ci_upper"]

    def test_bootstrap_ci_different_metrics(self, sample_scaling_data):
        """Test bootstrap CI for both metrics."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data)

        spec_result = bootstrap_power_law_ci(
            df, "specialization_index", n_bootstrap=50
        )
        ret_result = bootstrap_power_law_ci(
            df, "retrieval_efficiency", n_bootstrap=50
        )

        assert spec_result["metric"] == "specialization_index"
        assert ret_result["metric"] == "retrieval_efficiency"
        assert spec_result["exponent"] != ret_result["exponent"]  # Different metrics

    def test_invalid_metric_name(self, sample_scaling_data):
        """Test bootstrap CI with invalid metric name."""
        df = load_scaling_results_for_bootstrap(sample_scaling_data)

        with pytest.raises(ValueError, match="not found in data columns"):
            bootstrap_power_law_ci(df, "invalid_metric", n_bootstrap=50)
