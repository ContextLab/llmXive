"""
Unit tests for Task T024: P-value calculation against Cramér null distribution.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.pvalue_calculation import (
    load_observed_ks_statistic,
    load_cramer_null_distribution,
    calculate_pvalue,
    run_pipeline,
    main
)


class TestLoadObservedKsStatistic:
    """Tests for load_observed_ks_statistic function."""

    def test_load_valid_ks_statistic(self, tmp_path):
        """Test loading a valid KS statistic from a JSON file."""
        results_file = tmp_path / "correlation_results.json"
        data = {"ks_statistic": 0.123456, "other_key": "value"}
        with open(results_file, 'w') as f:
            json.dump(data, f)

        result = load_observed_ks_statistic(results_file)
        assert result == 0.123456

    def test_missing_file_raises_error(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_observed_ks_statistic(tmp_path / "nonexistent.json")

    def test_missing_key_raises_error(self, tmp_path):
        """Test that KeyError is raised when expected key is missing."""
        results_file = tmp_path / "correlation_results.json"
        with open(results_file, 'w') as f:
            json.dump({"other_key": "value"}, f)

        with pytest.raises(KeyError):
            load_observed_ks_statistic(results_file)

    def test_invalid_value_raises_error(self, tmp_path):
        """Test that ValueError is raised when value is not a number."""
        results_file = tmp_path / "correlation_results.json"
        with open(results_file, 'w') as f:
            json.dump({"ks_statistic": "not_a_number"}, f)

        with pytest.raises(ValueError):
            load_observed_ks_statistic(results_file)


class TestLoadCramerNullDistribution:
    """Tests for load_cramer_null_distribution function."""

    def test_load_valid_null_distribution(self, tmp_path):
        """Test loading a valid null distribution from a JSON file."""
        null_file = tmp_path / "cramer_null.json"
        data = {"ks_statistics": [0.1, 0.2, 0.3, 0.4, 0.5]}
        with open(null_file, 'w') as f:
            json.dump(data, f)

        result = load_cramer_null_distribution(null_file)
        expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float64)
        np.testing.assert_array_equal(result, expected)

    def test_missing_file_raises_error(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_cramer_null_distribution(tmp_path / "nonexistent.json")

    def test_missing_key_raises_error(self, tmp_path):
        """Test that KeyError is raised when expected key is missing."""
        null_file = tmp_path / "cramer_null.json"
        with open(null_file, 'w') as f:
            json.dump({"other_key": "value"}, f)

        with pytest.raises(KeyError):
            load_cramer_null_distribution(null_file)


class TestCalculatePvalue:
    """Tests for calculate_pvalue function."""

    def test_pvalue_greater_alternative(self):
        """Test p-value calculation with 'greater' alternative."""
        observed = 0.5
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8])
        # 3 values >= 0.5 out of 7 -> p = 3/7
        p_val, stats = calculate_pvalue(observed, null_dist, 'greater')
        assert abs(p_val - 3/7) < 1e-10
        assert stats['extreme_count'] == 3

    def test_pvalue_less_alternative(self):
        """Test p-value calculation with 'less' alternative."""
        observed = 0.5
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8])
        # 4 values <= 0.5 out of 7 -> p = 4/7
        p_val, stats = calculate_pvalue(observed, null_dist, 'less')
        assert abs(p_val - 4/7) < 1e-10
        assert stats['extreme_count'] == 4

    def test_pvalue_two_sided_alternative(self):
        """Test p-value calculation with 'two-sided' alternative."""
        observed = 0.5
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8])
        # Mean = 0.42857, observed deviation = 0.07143
        # Deviations: [0.32857, 0.22857, 0.12857, 0.02857, 0.17143, 0.27143, 0.37143]
        # Values with deviation >= 0.07143: all except 0.4 (deviation 0.02857)
        # So 6 out of 7
        p_val, stats = calculate_pvalue(observed, null_dist, 'two-sided')
        assert abs(p_val - 6/7) < 1e-10

    def test_empty_null_distribution_raises_error(self):
        """Test that ValueError is raised when null distribution is empty."""
        with pytest.raises(ValueError):
            calculate_pvalue(0.5, np.array([]))

    def test_non_finite_values_raises_error(self):
        """Test that ValueError is raised when null distribution contains NaN or Inf."""
        null_dist = np.array([0.1, np.nan, 0.3])
        with pytest.raises(ValueError):
            calculate_pvalue(0.5, null_dist)

    def test_invalid_alternative_raises_error(self):
        """Test that ValueError is raised for invalid alternative hypothesis."""
        null_dist = np.array([0.1, 0.2, 0.3])
        with pytest.raises(ValueError):
            calculate_pvalue(0.5, null_dist, alternative='invalid')

    def test_pvalue_stats_dict_completeness(self):
        """Test that the stats_dict contains all expected keys."""
        observed = 0.5
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8])
        _, stats = calculate_pvalue(observed, null_dist, 'greater')

        expected_keys = [
            'observed_ks', 'mean_null_ks', 'std_null_ks',
            'min_null_ks', 'max_null_ks', 'n_simulations',
            'extreme_count', 'p_value', 'alternative'
        ]
        for key in expected_keys:
            assert key in stats, f"Missing key: {key}"

    def test_pvalue_bounds(self):
        """Test that p-value is always between 0 and 1."""
        null_dist = np.random.normal(0.5, 0.1, 1000)
        for observed in [0.1, 0.5, 0.9]:
            p_val, _ = calculate_pvalue(observed, null_dist, 'greater')
            assert 0 <= p_val <= 1


class TestRunPipeline:
    """Tests for run_pipeline function."""

    def test_run_pipeline_creates_output_file(self, tmp_path):
        """Test that run_pipeline creates the output JSON file."""
        # Create mock input files
        observed_file = tmp_path / "correlation_results.json"
        with open(observed_file, 'w') as f:
            json.dump({"ks_statistic": 0.5}, f)

        null_file = tmp_path / "cramer_null.json"
        with open(null_file, 'w') as f:
            json.dump({"ks_statistics": [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8]}, f)

        output_file = tmp_path / "pvalue_results.json"

        # Run pipeline
        results = run_pipeline(
            observed_results_path=str(observed_file),
            null_results_path=str(null_file),
            output_path=str(output_file)
        )

        # Check output file exists
        assert output_file.exists()

        # Check results dictionary
        assert 'p_value' in results
        assert 'observed_ks_statistic' in results
        assert 'null_distribution_stats' in results

    def test_run_pipeline_handles_missing_files(self, tmp_path):
        """Test that run_pipeline raises FileNotFoundError for missing inputs."""
        with pytest.raises(FileNotFoundError):
            run_pipeline(
                observed_results_path=str(tmp_path / "nonexistent.json"),
                null_results_path=str(tmp_path / "also_nonexistent.json")
            )

    def test_run_pipeline_uses_default_paths(self, tmp_path, monkeypatch):
        """Test that run_pipeline uses default paths from config when not provided."""
        # Mock get_project_paths to return our tmp_path
        def mock_get_project_paths():
            return {
                'results_dir': tmp_path
            }

        monkeypatch.setattr('src.analysis.pvalue_calculation.get_project_paths', mock_get_project_paths)

        # Create mock input files in tmp_path
        observed_file = tmp_path / "correlation_results.json"
        with open(observed_file, 'w') as f:
            json.dump({"ks_statistic": 0.5}, f)

        null_file = tmp_path / "cramer_null_distribution.json"
        with open(null_file, 'w') as f:
            json.dump({"ks_statistics": [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8]}, f)

        # Run pipeline with no path arguments
        results = run_pipeline()

        # Check output was created
        output_file = tmp_path / "pvalue_results.json"
        assert output_file.exists()
        assert 'p_value' in results


class TestMain:
    """Tests for main function."""

    def test_main_returns_zero_on_success(self, tmp_path, monkeypatch, capsys):
        """Test that main returns 0 on successful execution."""
        # Create mock input files
        observed_file = tmp_path / "correlation_results.json"
        with open(observed_file, 'w') as f:
            json.dump({"ks_statistic": 0.5}, f)

        null_file = tmp_path / "cramer_null.json"
        with open(null_file, 'w') as f:
            json.dump({"ks_statistics": [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8]}, f)

        output_file = tmp_path / "pvalue_results.json"

        # Mock get_project_paths
        def mock_get_project_paths():
            return {'results_dir': tmp_path}

        monkeypatch.setattr('src.analysis.pvalue_calculation.get_project_paths', mock_get_project_paths)

        # Run main
        result = main()

        # Check return code
        assert result == 0

        # Check output was printed
        captured = capsys.readouterr()
        assert "P-VALUE CALCULATION RESULTS" in captured.out

    def test_main_returns_one_on_file_not_found(self, capsys):
        """Test that main returns 1 when input files are missing."""
        result = main()
        assert result == 1

        captured = capsys.readouterr()
        assert "ERROR" in captured.out

    def test_main_returns_one_on_invalid_data(self, tmp_path, monkeypatch, capsys):
        """Test that main returns 1 when input data is invalid."""
        # Create mock input files with invalid data
        observed_file = tmp_path / "correlation_results.json"
        with open(observed_file, 'w') as f:
            json.dump({"other_key": "value"}, f)  # Missing ks_statistic

        null_file = tmp_path / "cramer_null.json"
        with open(null_file, 'w') as f:
            json.dump({"ks_statistics": [0.1, 0.2, 0.3]}, f)

        def mock_get_project_paths():
            return {'results_dir': tmp_path}

        monkeypatch.setattr('src.analysis.pvalue_calculation.get_project_paths', mock_get_project_paths)

        result = main()
        assert result == 1

        captured = capsys.readouterr()
        assert "ERROR" in captured.out