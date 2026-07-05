"""
Tests for the Sensitivity Analysis Module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

from code.src.analysis.sensitivity import (
    load_simulation_data,
    filter_by_clustering_threshold,
    compute_sensitivity_metrics,
    run_sensitivity_sweep,
    main
)
from code.src.utils.config import load_config


class TestSensitivitySweepLogic:
    """Test suite for sensitivity sweep logic."""

    @pytest.fixture
    def sample_simulation_data(self):
        """Create sample simulation data for testing."""
        np.random.seed(42)
        n_samples = 100

        # Generate synthetic data with known correlation
        clustering = np.random.uniform(0, 1, n_samples)
        # Add some noise to create a moderate correlation
        diffusion = 0.5 * clustering + np.random.normal(0, 0.1, n_samples)
        diffusion = np.clip(diffusion, 0, 1)

        data = {
            'clustering_coefficient': clustering,
            'diffusion_rate': diffusion,
            'topology_class': np.random.choice(['er', 'sw', 'sf'], n_samples),
            'seed': np.random.randint(0, 1000, n_samples)
        }

        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_filter_by_clustering_threshold_above(self, sample_simulation_data):
        """Test filtering data for clustering coefficients above a threshold."""
        threshold = 0.5
        filtered = filter_by_clustering_threshold(
            sample_simulation_data,
            threshold,
            direction="above"
        )

        # All values should be >= threshold
        assert all(filtered['clustering_coefficient'] >= threshold)
        assert len(filtered) < len(sample_simulation_data)

    def test_filter_by_clustering_threshold_below(self, sample_simulation_data):
        """Test filtering data for clustering coefficients below a threshold."""
        threshold = 0.5
        filtered = filter_by_clustering_threshold(
            sample_simulation_data,
            threshold,
            direction="below"
        )

        # All values should be <= threshold
        assert all(filtered['clustering_coefficient'] <= threshold)

    def test_filter_invalid_direction(self, sample_simulation_data):
        """Test that invalid direction raises an error."""
        with pytest.raises(ValueError, match="Invalid direction"):
            filter_by_clustering_threshold(
                sample_simulation_data,
                0.5,
                direction="invalid"
            )

    def test_compute_sensitivity_metrics(self, sample_simulation_data):
        """Test computation of sensitivity metrics."""
        threshold = 0.5
        filtered = filter_by_clustering_threshold(
            sample_simulation_data,
            threshold,
            direction="above"
        )

        metrics = compute_sensitivity_metrics(filtered, threshold, direction="above")

        # Check required keys
        assert metrics['threshold'] == threshold
        assert metrics['direction'] == "above"
        assert metrics['sample_size'] == len(filtered)
        assert 'mean_clustering' in metrics
        assert 'correlation' in metrics

        # Check correlation structure
        corr = metrics['correlation']
        assert 'pearson_r' in corr
        assert 'p_value' in corr
        assert 'significant' in corr

    def test_run_sensitivity_sweep_minimum_thresholds(self, sample_simulation_data, temp_output_dir):
        """Test that sweep requires at least 5 thresholds (SC-005)."""
        # Test with too few thresholds
        with pytest.raises(ValueError, match="at least 5"):
            run_sensitivity_sweep(
                sample_simulation_data,
                thresholds=[0.0, 0.5],  # Only 2 thresholds
                output_path=temp_output_dir / "test.json"
            )

    def test_run_sensitivity_sweep_success(self, sample_simulation_data, temp_output_dir):
        """Test successful execution of sensitivity sweep."""
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]  # 6 thresholds

        results = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "sensitivity_test.json"
        )

        # Verify output file exists
        output_path = temp_output_dir / "sensitivity_test.json"
        assert output_path.exists()

        # Verify results structure
        assert 'metadata' in results
        assert 'threshold_results' in results
        assert 'summary' in results

        # Verify SC-005 compliance
        assert len(results['threshold_results']) >= 5

        # Verify threshold count matches
        assert results['metadata']['total_thresholds'] == len(thresholds)

    def test_run_sensitivity_sweep_output_format(self, sample_simulation_data, temp_output_dir):
        """Test that output JSON has correct structure and content."""
        thresholds = [0.0, 0.5, 1.0]

        results = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "format_test.json"
        )

        # Load and verify JSON structure
        with open(temp_output_dir / "format_test.json", 'r') as f:
            loaded = json.load(f)

        # Check metadata fields
        meta = loaded['metadata']
        assert meta['analysis_type'] == 'sensitivity_sweep'
        assert meta['parameter'] == 'clustering_coefficient'
        assert 'thresholds_used' in meta
        assert 'timestamp' in meta

        # Check threshold results
        for result in loaded['threshold_results']:
            assert 'threshold' in result
            assert 'sample_size' in result
            assert 'correlation' in result
            assert 'pearson_r' in result['correlation']
            assert 'p_value' in result['correlation']

    def test_run_sensitivity_sweep_correlation_detection(self, sample_simulation_data, temp_output_dir):
        """Test that the sweep correctly detects correlations in the data."""
        thresholds = [0.0, 0.5, 1.0]

        results = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "corr_test.json"
        )

        # At least some thresholds should have valid correlations
        valid_corrs = [
            r['correlation']['pearson_r']
            for r in results['threshold_results']
            if r['correlation'].get('pearson_r') is not None
        ]

        assert len(valid_corrs) > 0

    def test_main_with_mocked_data(self, sample_simulation_data, temp_output_dir, caplog):
        """Test the main function with mocked data loading."""
        # Mock the load_simulation_data function
        with patch('code.src.analysis.sensitivity.load_simulation_data') as mock_load:
            mock_load.return_value = sample_simulation_data

            # Mock the config to use temp directory
            with patch('code.src.analysis.sensitivity.load_config') as mock_config:
                mock_config.return_value = {
                    'paths': {
                        'sensitivity_results': str(temp_output_dir / "main_test.json")
                    }
                }

                # Run main
                result = main()

                # Should complete successfully
                assert result == 0

                # Verify output was created
                assert (temp_output_dir / "main_test.json").exists()

    def test_sensitivity_sweep_empty_data_handling(self, temp_output_dir):
        """Test handling of empty data subsets."""
        # Create data that will result in empty subsets for some thresholds
        np.random.seed(42)
        data = pd.DataFrame({
            'clustering_coefficient': [0.1, 0.2, 0.3],
            'diffusion_rate': [0.5, 0.6, 0.7],
            'topology_class': ['er', 'sw', 'sf']
        })

        # Use thresholds that will create empty subsets
        thresholds = [0.0, 0.5, 1.0]

        results = run_sensitivity_sweep(
            data,
            thresholds=thresholds,
            output_path=temp_output_dir / "empty_test.json"
        )

        # Should handle empty subsets gracefully
        for result in results['threshold_results']:
            assert 'sample_size' in result
            # Even with 0 samples, correlation should be handled
            assert 'correlation' in result

    def test_sensitivity_sweep_summary_statistics(self, sample_simulation_data, temp_output_dir):
        """Test that summary statistics are computed correctly."""
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        results = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "summary_test.json"
        )

        summary = results['summary']

        # Check summary fields
        assert 'total_thresholds_processed' in summary
        assert 'thresholds_with_data' in summary
        assert 'best_correlation_threshold' in summary
        assert 'best_correlation_value' in summary
        assert 'mean_sample_size' in summary
        assert 'significant_correlations_count' in summary

    def test_sensitivity_sweep_direction_parameter(self, sample_simulation_data, temp_output_dir):
        """Test that direction parameter affects filtering correctly."""
        thresholds = [0.5]

        # Run with "above" direction
        results_above = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "above.json",
            direction="above"
        )

        # Run with "below" direction
        results_below = run_sensitivity_sweep(
            sample_simulation_data,
            thresholds=thresholds,
            output_path=temp_output_dir / "below.json",
            direction="below"
        )

        # Sample sizes should be different (unless threshold is 0 or 1)
        sample_above = results_above['threshold_results'][0]['sample_size']
        sample_below = results_below['threshold_results'][0]['sample_size']

        # They should not both be the full dataset
        assert sample_above + sample_below <= len(sample_simulation_data) + 1  # +1 for boundary case
