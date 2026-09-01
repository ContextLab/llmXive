"""
Unit tests for error propagation analysis (T054).
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Mock the config module to use temporary directories
import sys
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, 'code')

from analysis.error_propagation import (
    propagate_lifetime_uncertainty,
    propagate_correlation_uncertainty,
    run_error_propagation_analysis
)


class TestPropagateLifetimeUncertainty:
    def test_basic_calculation(self):
        """Test standard SEM and CI calculation."""
        mean_tau = 100.0
        std_tau = 10.0
        n_rep = 4

        result = propagate_lifetime_uncertainty(mean_tau, std_tau, n_rep)

        # SEM = 10 / sqrt(4) = 5.0
        assert abs(result['sem'] - 5.0) < 1e-6
        # t_val for 95% CI, df=3 is approx 3.182
        # CI_half = 3.182 * 5.0 = 15.91
        expected_ci_half = 3.182 * 5.0
        assert abs(result['ci_half_width'] - expected_ci_half) < 0.1
        assert result['ci_lower'] == mean_tau - result['ci_half_width']
        assert result['ci_upper'] == mean_tau + result['ci_half_width']
        assert result['n_replicates'] == 4

    def test_single_replicate(self):
        """Test behavior when n_replicates = 1."""
        mean_tau = 100.0
        std_tau = 10.0
        n_rep = 1

        result = propagate_lifetime_uncertainty(mean_tau, std_tau, n_rep)

        # For n=1, SEM is effectively std_dev (or undefined, but we handle it)
        # The implementation sets SEM = std_dev and CI_half = std_dev
        assert abs(result['sem'] - std_tau) < 1e-6
        assert abs(result['ci_half_width'] - std_tau) < 1e-6
        assert result['ci_lower'] == 90.0
        assert result['ci_upper'] == 110.0

    def test_high_precision(self):
        """Test with very small standard deviation."""
        mean_tau = 100.0
        std_tau = 0.001
        n_rep = 10

        result = propagate_lifetime_uncertainty(mean_tau, std_tau, n_rep)
        assert result['sem'] < 0.001
        assert result['relative_error_percent'] < 0.1


class TestPropagateCorrelationUncertainty:
    def test_basic_correlation(self):
        """Test slope and intercept CI calculation."""
        slope = 2.0
        slope_std = 0.1
        intercept = 5.0
        intercept_std = 0.5
        r_squared = 0.85
        n_points = 5

        result = propagate_correlation_uncertainty(
            slope, slope_std, intercept, intercept_std, r_squared, n_points
        )

        # df = 3, t_val approx 3.182
        # slope_ci_half = 3.182 * 0.1 = 0.3182
        expected_slope_half = 3.182 * 0.1
        assert abs(result['slope_ci_half_width'] - expected_slope_half) < 0.01
        assert result['slope_ci_lower'] == slope - expected_slope_half
        assert result['slope_ci_upper'] == slope + expected_slope_half

    def test_r_squared_bounds(self):
        """Test that R-squared CI stays within [0, 1]."""
        slope = 1.0
        slope_std = 0.1
        intercept = 0.0
        intercept_std = 0.1
        r_squared = 0.99
        n_points = 10

        result = propagate_correlation_uncertainty(
            slope, slope_std, intercept, intercept_std, r_squared, n_points
        )

        assert 0.0 <= result['r_squared_ci_lower'] <= 1.0
        assert 0.0 <= result['r_squared_ci_upper'] <= 1.0

    def test_small_n_points(self):
        """Test behavior with minimal data points."""
        slope = 1.0
        slope_std = 0.1
        intercept = 0.0
        intercept_std = 0.1
        r_squared = 0.5
        n_points = 2

        result = propagate_correlation_uncertainty(
            slope, slope_std, intercept, intercept_std, r_squared, n_points
        )
        # Should not crash, df should be 0
        assert result['degrees_of_freedom'] == 0


class TestRunErrorPropagationAnalysis:
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary directory structure for testing."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create mock kinetic_metrics.csv
        kinetic_data = {
            'solvent': ['cyclohexane', 'methanol', 'acetonitrile'],
            'lifetime': [100.0, 50.0, 200.0],
            'std_dev': [5.0, 2.5, 10.0],
            'n_replicates': [3, 3, 3]
        }
        df = pd.DataFrame(kinetic_data)
        df.to_csv(processed_dir / "kinetic_metrics.csv", index=False)

        # Create mock correlation_results.json
        corr_data = {
            'posterior_slope': {'mean': 0.5, 'std': 0.05},
            'posterior_intercept': {'mean': 10.0, 'std': 2.0},
            'bayesian_r2': 0.75,
            'credible_intervals': {
                'slope': [0.4, 0.6],
                'intercept': [8.0, 12.0]
            }
        }
        with open(processed_dir / "correlation_results.json", 'w') as f:
            json.dump(corr_data, f)

        return tmp_path

    def test_full_pipeline(self, temp_data_dir, caplog):
        """Test the full pipeline execution with mock data."""
        output_path = temp_data_dir / "data" / "processed" / "error_propagation_report.json"

        with patch('config.get_processed_data_path', return_value=temp_data_dir / "data" / "processed"):
            report = run_error_propagation_analysis(
                confidence_level=0.95,
                output_path=output_path
            )

        # Verify report structure
        assert 'metadata' in report
        assert 'kinetic_metrics_propagation' in report
        assert 'correlation_metrics_propagation' in report
        assert 'summary' in report

        # Verify kinetic metrics
        assert len(report['kinetic_metrics_propagation']) == 3
        assert report['kinetic_metrics_propagation'][0]['solvent'] == 'cyclohexane'
        assert 'sem' in report['kinetic_metrics_propagation'][0]

        # Verify correlation metrics
        corr = report['correlation_metrics_propagation']
        assert 'slope_ci_lower' in corr
        assert 'slope_ci_upper' in corr
        assert 'r_squared_ci_lower' in corr

        # Verify file was written
        assert output_path.exists()
        with open(output_path, 'r') as f:
            written_report = json.load(f)
        assert written_report['summary']['total_solvents_analyzed'] == 3