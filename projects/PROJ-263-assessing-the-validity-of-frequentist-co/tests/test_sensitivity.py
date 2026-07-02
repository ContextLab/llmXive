"""
Unit tests for sensitivity analysis module.

Tests cover:
- Confidence level sweep functionality
- Sample size sweep functionality
- Deviation analysis
- Edge cases and error handling
"""

import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.sensitivity import (
    load_population_means,
    sweep_confidence_levels,
    sweep_sample_sizes,
    analyze_sensitivity_deviations,
    run_sensitivity_analysis
)
from code.coverage import check_coverage


class TestLoadPopulationMeans:
    """Tests for loading population means from JSON file."""

    def test_load_existing_file(self):
        """Test loading from an existing valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"dataset1": {"var1": 5.5}}, f)
            temp_path = f.name

        try:
            result = load_population_means(temp_path)
            assert result == {"dataset1": {"var1": 5.5}}
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test that loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_population_means("nonexistent_file.json")


class TestSweepConfidenceLevels:
    """Tests for confidence level sweep functionality."""

    def test_basic_sweep(self):
        """Test basic confidence level sweep with synthetic data."""
        np.random.seed(42)
        dataset = np.random.normal(loc=10.0, scale=2.0, size=500)
        pop_mean = 10.0
        sample_size = 20
        confidence_levels = [0.90, 0.95]
        n_replications = 100  # Small number for testing

        result = sweep_confidence_levels(
            dataset_name="test_dataset",
            dataset_array=dataset,
            sample_size=sample_size,
            confidence_levels=confidence_levels,
            n_replications=n_replications,
            population_mean=pop_mean,
            seed=42
        )

        assert result["dataset"] == "test_dataset"
        assert result["sample_size"] == sample_size
        assert result["sweep_type"] == "confidence_level"
        assert len(result["results"]) == len(confidence_levels)

        # Check that results contain expected fields
        for r in result["results"]:
            assert "confidence_level" in r
            assert "empirical_coverage" in r
            assert "deviation" in r
            if r["empirical_coverage"] is not None:
                assert 0 <= r["empirical_coverage"] <= 1

    def test_single_level(self):
        """Test sweep with a single confidence level."""
        np.random.seed(42)
        dataset = np.random.normal(loc=0.0, scale=1.0, size=200)

        result = sweep_confidence_levels(
            dataset_name="test",
            dataset_array=dataset,
            sample_size=15,
            confidence_levels=[0.95],
            n_replications=50,
            population_mean=0.0,
            seed=42
        )

        assert len(result["results"]) == 1
        assert result["results"][0]["confidence_level"] == 0.95

    def test_small_sample_size(self):
        """Test with very small sample size (n=2)."""
        np.random.seed(42)
        dataset = np.random.normal(loc=5.0, scale=1.0, size=100)

        result = sweep_confidence_levels(
            dataset_name="test",
            dataset_array=dataset,
            sample_size=2,
            confidence_levels=[0.95],
            n_replications=20,
            population_mean=5.0,
            seed=42
        )

        # Should handle gracefully even with small sample
        assert len(result["results"]) == 1


class TestSweepSampleSizes:
    """Tests for sample size sweep functionality."""

    def test_basic_size_sweep(self):
        """Test basic sample size sweep."""
        np.random.seed(42)
        dataset = np.random.normal(loc=10.0, scale=2.0, size=500)

        result = sweep_sample_sizes(
            dataset_name="test_dataset",
            dataset_array=dataset,
            confidence_level=0.95,
            sample_sizes=[10, 20, 30],
            n_replications=50,
            population_mean=10.0,
            seed=42
        )

        assert result["dataset"] == "test_dataset"
        assert result["confidence_level"] == 0.95
        assert result["sweep_type"] == "sample_size"
        assert len(result["results"]) == 3

        sample_sizes_found = [r["sample_size"] for r in result["results"]]
        assert sample_sizes_found == [10, 20, 30]

    def test_single_size(self):
        """Test sweep with a single sample size."""
        np.random.seed(42)
        dataset = np.random.normal(loc=0.0, scale=1.0, size=200)

        result = sweep_sample_sizes(
            dataset_name="test",
            dataset_array=dataset,
            confidence_level=0.90,
            sample_sizes=[15],
            n_replications=30,
            population_mean=0.0,
            seed=42
        )

        assert len(result["results"]) == 1
        assert result["results"][0]["sample_size"] == 15


class TestAnalyzeSensitivityDeviations:
    """Tests for sensitivity deviation analysis."""

    def test_identify_significant_deviations(self):
        """Test detection of practically significant deviations."""
        results = {
            "dataset": "test",
            "sweep_type": "confidence_level",
            "results": [
                {
                    "confidence_level": 0.95,
                    "empirical_coverage": 0.92,
                    "deviation": 0.03,
                    "is_practically_significant": True
                },
                {
                    "confidence_level": 0.90,
                    "empirical_coverage": 0.895,
                    "deviation": 0.005,
                    "is_practically_significant": False
                }
            ]
        }

        analysis = analyze_sensitivity_deviations(results)

        assert analysis["dataset"] == "test"
        assert analysis["max_deviation"] == 0.03
        assert analysis["practically_significant_count"] == 1
        assert analysis["instability_detected"] is True

    def test_no_deviations(self):
        """Test when all deviations are within threshold."""
        results = {
            "dataset": "test",
            "sweep_type": "sample_size",
            "results": [
                {
                    "sample_size": 10,
                    "empirical_coverage": 0.949,
                    "deviation": 0.001,
                    "is_practically_significant": False
                },
                {
                    "sample_size": 20,
                    "empirical_coverage": 0.951,
                    "deviation": 0.001,
                    "is_practically_significant": False
                }
            ]
        }

        analysis = analyze_sensitivity_deviations(results)

        assert analysis["instability_detected"] is False
        assert analysis["practically_significant_count"] == 0

    def test_empty_results(self):
        """Test analysis with empty results list."""
        results = {
            "dataset": "test",
            "sweep_type": "confidence_level",
            "results": []
        }

        analysis = analyze_sensitivity_deviations(results)

        assert analysis["max_deviation"] == 0.0
        assert analysis["practically_significant_count"] == 0
        assert analysis["instability_detected"] is False


class TestCoverageCheckIntegration:
    """Integration tests for coverage checking within sensitivity analysis."""

    def test_coverage_detection_accuracy(self):
        """Test that coverage is correctly detected for known intervals."""
        # Test cases: (lower, upper, mean, expected_contains)
        test_cases = [
            (9.0, 11.0, 10.0, True),
            (9.0, 11.0, 11.5, False),
            (9.0, 11.0, 8.5, False),
            (10.0, 10.0, 10.0, True),  # Point interval
        ]

        for lower, upper, mean, expected in test_cases:
            result = check_coverage(lower, upper, mean)
            assert result == expected, f"Failed for interval [{lower}, {upper}] with mean {mean}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])