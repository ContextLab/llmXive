"""Unit tests for the bootstrapper module.

Tests for bootstrapped power estimation and KS distance calculation.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from code.analysis.bootstrapper import (
    load_real_data_pvalues,
    load_simulated_power_distribution,
    bootstrap_power_estimate,
    calculate_ks_distance,
    run_bootstrapped_validation,
    save_power_results
)


class TestLoadRealDataPvalues:
    """Tests for load_real_data_pvalues function."""

    def test_load_valid_pvalues(self, tmp_path):
        """Test loading a valid p-values CSV file."""
        # Create test data
        data = {
            'test_type': ['t-test', 't-test', 'anova'],
            'dataset': ['breast_cancer', 'wine', 'adult'],
            'p_value': [0.03, 0.15, 0.02],
            'sample_size': [50, 100, 200]
        }
        df = pd.DataFrame(data)

        filepath = tmp_path / "real_data_pvalues.csv"
        df.to_csv(filepath, index=False)

        # Load and verify
        loaded_df = load_real_data_pvalues(str(filepath))

        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['test_type', 'dataset', 'p_value', 'sample_size']
        assert loaded_df['p_value'].iloc[0] == 0.03

    def test_load_empty_file(self, tmp_path):
        """Test that loading an empty file raises ValueError."""
        filepath = tmp_path / "empty.csv"
        filepath.touch()

        with pytest.raises(ValueError, match="empty"):
            load_real_data_pvalues(str(filepath))

    def test_load_missing_columns(self, tmp_path):
        """Test that missing required columns raise ValueError."""
        data = {
            'test_type': ['t-test'],
            'p_value': [0.05]
        }
        df = pd.DataFrame(data)

        filepath = tmp_path / "incomplete.csv"
        df.to_csv(filepath, index=False)

        with pytest.raises(ValueError, match="Missing required columns"):
            load_real_data_pvalues(str(filepath))

    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_real_data_pvalues("nonexistent.csv")


class TestLoadSimulatedPowerDistribution:
    """Tests for load_simulated_power_distribution function."""

    def test_load_and_calculate_power(self, tmp_path):
        """Test loading error rates and calculating power."""
        # Create test data
        data = {
            'test_type': ['t-test', 'anova'],
            'sample_size': [50, 100],
            'effect_size': [0.5, 0.8],
            'type_ii_error_rate': [0.2, 0.1]
        }
        df = pd.DataFrame(data)

        filepath = tmp_path / "error_rates.csv"
        df.to_csv(filepath, index=False)

        # Load and verify
        loaded_df = load_simulated_power_distribution(str(filepath))

        assert len(loaded_df) == 2
        assert 'power' in loaded_df.columns
        assert loaded_df['power'].iloc[0] == pytest.approx(0.8, rel=0.01)
        assert loaded_df['power'].iloc[1] == pytest.approx(0.9, rel=0.01)

    def test_missing_columns(self, tmp_path):
        """Test that missing required columns raise ValueError."""
        data = {
            'test_type': ['t-test'],
            'sample_size': [50]
        }
        df = pd.DataFrame(data)

        filepath = tmp_path / "incomplete.csv"
        df.to_csv(filepath, index=False)

        with pytest.raises(ValueError, match="Missing required columns"):
            load_simulated_power_distribution(str(filepath))


class TestBootstrapPowerEstimate:
    """Tests for bootstrap_power_estimate function."""

    def test_bootstrap_basic(self):
        """Test basic bootstrap functionality."""
        # Create test data
        data = {
            'test_type': ['t-test', 't-test', 't-test', 't-test', 't-test'],
            'dataset': ['test', 'test', 'test', 'test', 'test'],
            'p_value': [0.01, 0.03, 0.04, 0.06, 0.07],
            'sample_size': [50, 50, 50, 50, 50]
        }
        df = pd.DataFrame(data)

        results = bootstrap_power_estimate(df, n_bootstrap=100, random_state=42)

        assert 't-test_test' in results
        assert 'mean_power' in results['t-test_test']
        assert 'std_power' in results['t-test_test']
        assert 'ci_lower' in results['t-test_test']
        assert 'ci_upper' in results['t-test_test']
        assert results['t-test_test']['bootstrap_samples'] == 100

    def test_bootstrap_empty_dataframe(self):
        """Test that empty DataFrame raises ValueError."""
        df = pd.DataFrame(columns=['test_type', 'dataset', 'p_value', 'sample_size'])

        with pytest.raises(ValueError, match="empty"):
            bootstrap_power_estimate(df)

    def test_bootstrap_small_sample(self, caplog):
        """Test bootstrap with small sample size."""
        data = {
            'test_type': ['t-test'],
            'dataset': ['test'],
            'p_value': [0.03],
            'sample_size': [50]
        }
        df = pd.DataFrame(data)

        # Should still work but log a warning
        results = bootstrap_power_estimate(df, n_bootstrap=10, random_state=42)
        assert 't-test_test' in results


class TestCalculateKsDistance:
    """Tests for calculate_ks_distance function."""

    def test_ks_distance_calculation(self, tmp_path):
        """Test KS distance calculation between real and simulated distributions."""
        # Create mock real power distribution
        real_power_dist = {
            't-test_test': {
                'power_estimates': [0.7, 0.75, 0.8, 0.85, 0.9]
            }
        }

        # Create simulated power dataframe
        data = {
            'test_type': ['t-test', 't-test', 't-test'],
            'sample_size': [50, 50, 50],
            'effect_size': [0.5, 0.5, 0.5],
            'type_ii_error_rate': [0.2, 0.25, 0.3]
        }
        sim_df = pd.DataFrame(data)

        ks_distances = calculate_ks_distance(real_power_dist, sim_df)

        assert 't-test_test' in ks_distances
        assert 0 <= ks_distances['t-test_test'] <= 1

    def test_ks_distance_no_simulated_data(self):
        """Test KS distance when no simulated data exists for test type."""
        real_power_dist = {
            'unknown_test_test': {
                'power_estimates': [0.7, 0.8]
            }
        }

        data = {
            'test_type': ['t-test'],
            'sample_size': [50],
            'effect_size': [0.5],
            'type_ii_error_rate': [0.2]
        }
        sim_df = pd.DataFrame(data)

        ks_distances = calculate_ks_distance(real_power_dist, sim_df)

        assert 'unknown_test_test' in ks_distances
        assert ks_distances['unknown_test_test'] == float('inf')


class TestSavePowerResults:
    """Tests for save_power_results function."""

    def test_save_results(self, tmp_path):
        """Test saving results to JSON file."""
        results = {
            'bootstrap_parameters': {'n_bootstrap': 100, 'random_state': 42},
            'power_estimates': {
                't-test_test': {
                    'mean_power': 0.75,
                    'std_power': 0.05,
                    'ci_lower': 0.65,
                    'ci_upper': 0.85
                }
            },
            'ks_distances': {'t-test_test': 0.08},
            'overall_assessment': {
                'all_tests_passed': True,
                'num_tests': 1,
                'num_passed': 1
            }
        }

        filepath = tmp_path / "power_results.json"
        save_power_results(results, str(filepath))

        assert filepath.exists()

        # Verify JSON is valid and contains expected data
        with open(filepath, 'r') as f:
            loaded = json.load(f)

        assert loaded['bootstrap_parameters']['n_bootstrap'] == 100
        assert loaded['ks_distances']['t-test_test'] == 0.08

    def test_save_creates_directory(self, tmp_path):
        """Test that save_power_results creates directory if it doesn't exist."""
        results = {'test': 'data'}
        nested_path = tmp_path / "nested" / "path" / "results.json"

        save_power_results(results, str(nested_path))

        assert nested_path.exists()

    def test_save_numpy_types(self, tmp_path):
        """Test that numpy types are properly serialized."""
        results = {
            'value': np.float64(0.75),
            'array': np.array([1, 2, 3]),
            'nan_value': np.nan
        }

        filepath = tmp_path / "numpy_test.json"
        save_power_results(results, str(filepath))

        # Should not raise and should be valid JSON
        with open(filepath, 'r') as f:
            loaded = json.load(f)

        assert loaded['value'] == 0.75
        assert loaded['array'] == [1, 2, 3]
        assert loaded['nan_value'] is None  # NaN becomes None


class TestRunBootstrappedValidation:
    """Tests for run_bootstrapped_validation function."""

    def test_full_validation_pipeline(self, tmp_path):
        """Test the complete validation pipeline."""
        # Create mock real data
        real_data = {
            'test_type': ['t-test', 't-test', 't-test'],
            'dataset': ['test', 'test', 'test'],
            'p_value': [0.01, 0.03, 0.04],
            'sample_size': [50, 50, 50]
        }
        real_df = pd.DataFrame(real_data)
        real_path = tmp_path / "real_data_pvalues.csv"
        real_df.to_csv(real_path, index=False)

        # Create mock simulated data
        sim_data = {
            'test_type': ['t-test', 't-test'],
            'sample_size': [50, 100],
            'effect_size': [0.5, 0.5],
            'type_ii_error_rate': [0.2, 0.1]
        }
        sim_df = pd.DataFrame(sim_data)
        sim_path = tmp_path / "error_rates.csv"
        sim_df.to_csv(sim_path, index=False)

        # Run validation
        results = run_bootstrapped_validation(
            real_data_path=str(real_path),
            simulated_data_path=str(sim_path),
            n_bootstrap=50,
            random_state=42
        )

        assert 'bootstrap_parameters' in results
        assert 'power_estimates' in results
        assert 'ks_distances' in results
        assert 'overall_assessment' in results
        assert results['overall_assessment']['num_tests'] >= 1

    def test_missing_real_data_file(self, tmp_path):
        """Test that missing real data file raises FileNotFoundError."""
        sim_data = {
            'test_type': ['t-test'],
            'sample_size': [50],
            'effect_size': [0.5],
            'type_ii_error_rate': [0.2]
        }
        sim_df = pd.DataFrame(sim_data)
        sim_path = tmp_path / "error_rates.csv"
        sim_df.to_csv(sim_path, index=False)

        with pytest.raises(FileNotFoundError, match="real_data_pvalues.csv"):
            run_bootstrapped_validation(
                real_data_path=str(tmp_path / "nonexistent.csv"),
                simulated_data_path=str(sim_path)
            )

    def test_missing_simulated_data_file(self, tmp_path):
        """Test that missing simulated data file raises FileNotFoundError."""
        real_data = {
            'test_type': ['t-test'],
            'dataset': ['test'],
            'p_value': [0.03],
            'sample_size': [50]
        }
        real_df = pd.DataFrame(real_data)
        real_path = tmp_path / "real_data_pvalues.csv"
        real_df.to_csv(real_path, index=False)

        with pytest.raises(FileNotFoundError, match="error_rates_summary.csv"):
            run_bootstrapped_validation(
                real_data_path=str(real_path),
                simulated_data_path=str(tmp_path / "nonexistent.csv")
            )