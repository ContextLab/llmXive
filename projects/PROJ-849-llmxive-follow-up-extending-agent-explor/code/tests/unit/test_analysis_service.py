"""
Unit tests for src/services/analysis_service.py
"""

import pytest
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.analysis_service import (
    AnalysisServiceError,
    validate_sample_size,
    calculate_pearson_correlation,
    load_and_merge_analysis_data,
    run_correlation_analysis,
    CorrelationResult
)


class TestValidation:
    def test_validate_sample_size_success(self):
        # Should not raise
        validate_sample_size(30)
        validate_sample_size(100)

    def test_validate_sample_size_failure(self):
        with pytest.raises(AnalysisServiceError, match="Insufficient Sample Size"):
            validate_sample_size(29)
        with pytest.raises(AnalysisServiceError, match="Insufficient Sample Size"):
            validate_sample_size(0)


class TestCorrelationCalculation:
    def test_perfect_negative_correlation(self):
        # y = -x
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        result = calculate_pearson_correlation(x, y)
        assert np.isclose(result.correlation_coefficient, -1.0, atol=1e-5)
        assert result.p_value < 0.05
        assert result.significance_flag is True
        assert result.n_samples == 5

    def test_perfect_positive_correlation(self):
        # y = x
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_pearson_correlation(x, y)
        assert np.isclose(result.correlation_coefficient, 1.0, atol=1e-5)
        assert result.p_value < 0.05
        assert result.significance_flag is True

    def test_no_correlation(self):
        # Random noise with large N to ensure p > 0.05 usually, or just check calculation works
        np.random.seed(42)
        x = np.random.rand(100).tolist()
        y = np.random.rand(100).tolist()
        result = calculate_pearson_correlation(x, y)
        # Just check it runs and returns valid float
        assert isinstance(result.correlation_coefficient, float)
        assert isinstance(result.p_value, float)
        assert -1.0 <= result.correlation_coefficient <= 1.0

    def test_empty_inputs(self):
        with pytest.raises(AnalysisServiceError, match="cannot be empty"):
            calculate_pearson_correlation([], [])

    def test_mismatched_lengths(self):
        with pytest.raises(AnalysisServiceError, match="Mismatched input lengths"):
            calculate_pearson_correlation([1, 2], [1])

    def test_zero_variance(self):
        with pytest.raises(AnalysisServiceError, match="zero variance"):
            calculate_pearson_correlation([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])


class TestLoadAndMerge:
    def test_load_and_merge_success(self):
        # Create temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            div_path = os.path.join(tmpdir, "div.json")
            axpo_path = os.path.join(tmpdir, "axpo.json")

            div_data = [
                {"problem_id": "p1", "semantic_divergence_score": 0.5, "problem_type": "math"},
                {"problem_id": "p2", "semantic_divergence_score": 0.8, "problem_type": "science"}
            ]
            axpo_data = [
                {"problem_id": "p1", "failure_rate": 0.2},
                {"problem_id": "p2", "success_rate": 0.9} # Should convert to 0.1 failure
            ]

            with open(div_path, 'w') as f:
                json.dump(div_data, f)
            with open(axpo_path, 'w') as f:
                json.dump(axpo_data, f)

            records, scores, failures = load_and_merge_analysis_data(div_path, axpo_path)

            assert len(records) == 2
            assert len(scores) == 2
            assert len(failures) == 2

            # Check specific values
            # p1: div=0.5, fail=0.2
            # p2: div=0.8, fail=0.1 (1 - 0.9)
            assert abs(scores[0] - 0.5) < 1e-6
            assert abs(failures[0] - 0.2) < 1e-6
            assert abs(scores[1] - 0.8) < 1e-6
            assert abs(failures[1] - 0.1) < 1e-6

    def test_missing_file(self):
        with pytest.raises(AnalysisServiceError, match="not found"):
            load_and_merge_analysis_data("/nonexistent/path.json")

    def test_no_matching_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            div_path = os.path.join(tmpdir, "div.json")
            axpo_path = os.path.join(tmpdir, "axpo.json")

            div_data = [{"problem_id": "p1", "semantic_divergence_score": 0.5}]
            axpo_data = [{"problem_id": "p2", "failure_rate": 0.2}]

            with open(div_path, 'w') as f:
                json.dump(div_data, f)
            with open(axpo_path, 'w') as f:
                json.dump(axpo_data, f)

            with pytest.raises(AnalysisServiceError, match="No matching records"):
                load_and_merge_analysis_data(div_path, axpo_path)


class TestRunCorrelationAnalysis:
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            div_path = os.path.join(tmpdir, "div.json")
            axpo_path = os.path.join(tmpdir, "axpo.json")
            out_path = os.path.join(tmpdir, "report.json")

            # Create data with known negative correlation
            # x: 1, 2, 3, 4, 5
            # y: 5, 4, 3, 2, 1
            div_data = [
                {"problem_id": f"p{i}", "semantic_divergence_score": float(i+1), "problem_type": "test"}
                for i in range(5)
            ]
            axpo_data = [
                {"problem_id": f"p{i}", "failure_rate": float(5-i)/5.0}
                for i in range(5)
            ]

            with open(div_path, 'w') as f:
                json.dump(div_data, f)
            with open(axpo_path, 'w') as f:
                json.dump(axpo_data, f)

            # Note: N=5 is < 30, so this should fail validation in the function
            # We need N >= 30 for the function to pass.
            # Let's generate 30 points.
            div_data_large = [
                {"problem_id": f"p{i}", "semantic_divergence_score": float(i+1), "problem_type": "test"}
                for i in range(30)
            ]
            axpo_data_large = [
                {"problem_id": f"p{i}", "failure_rate": float(30-i)/30.0}
                for i in range(30)
            ]

            with open(div_path, 'w') as f:
                json.dump(div_data_large, f)
            with open(axpo_path, 'w') as f:
                json.dump(axpo_data_large, f)

            report = run_correlation_analysis(div_path, axpo_path, out_path)

            assert report.correlation.correlation_coefficient < 0 # Negative correlation
            assert report.correlation.significance_flag is True
            assert report.correlation.n_samples == 30

            # Check file was written
            assert os.path.exists(out_path)
            with open(out_path, 'r') as f:
                written = json.load(f)
            assert "correlation" in written
            assert "dataset_info" in written