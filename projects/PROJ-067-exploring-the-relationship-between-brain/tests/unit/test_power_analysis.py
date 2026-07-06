"""
Unit tests for the post-hoc power analysis module.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.power_analysis import (
    calculate_detectable_effect_size,
    calculate_post_hoc_power,
    run_power_analysis
)

class TestCalculateDetectableEffectSize:
    """Tests for detectable effect size calculation."""

    def test_detectable_effect_size_n50(self):
        """Test detectable effect size for N=50."""
        d = calculate_detectable_effect_size(n=50, alpha=0.05, power=0.80)
        assert isinstance(d, float)
        assert d > 0
        # For N=50, detectable d should be around 0.5-0.6 (medium effect)
        assert 0.4 < d < 0.8

    def test_detectable_effect_size_larger_n(self):
        """Detectable effect size should decrease with larger N."""
        d_50 = calculate_detectable_effect_size(n=50)
        d_100 = calculate_detectable_effect_size(n=100)
        assert d_100 < d_50

    def test_detectable_effect_size_smaller_n(self):
        """Detectable effect size should increase with smaller N."""
        d_50 = calculate_detectable_effect_size(n=50)
        d_20 = calculate_detectable_effect_size(n=20)
        assert d_20 > d_50

    def test_detectable_effect_size_strict_alpha(self):
        """Stricter alpha should increase detectable effect size."""
        d_05 = calculate_detectable_effect_size(n=50, alpha=0.05)
        d_01 = calculate_detectable_effect_size(n=50, alpha=0.01)
        assert d_01 > d_05

    def test_detectable_effect_size_high_power(self):
        """Higher target power should increase detectable effect size."""
        d_80 = calculate_detectable_effect_size(n=50, power=0.80)
        d_90 = calculate_detectable_effect_size(n=50, power=0.90)
        assert d_90 > d_80

class TestCalculatePostHocPower:
    """Tests for achieved power calculation."""

    def test_power_with_r_zero(self):
        """Power should be near alpha when r=0."""
        power = calculate_post_hoc_power(r_observed=0.0, n=50)
        # When r=0, power should be close to alpha (type I error rate)
        assert 0.04 < power < 0.06  # Approximately 0.05

    def test_power_with_large_r(self):
        """Power should approach 1.0 with large r."""
        power = calculate_post_hoc_power(r_observed=0.5, n=50)
        assert power > 0.8

    def test_power_with_medium_r(self):
        """Power should be moderate with medium r."""
        power = calculate_post_hoc_power(r_observed=0.3, n=50)
        assert 0.3 < power < 0.9

    def test_power_with_r_one(self):
        """Power should be 1.0 when r=1."""
        power = calculate_post_hoc_power(r_observed=1.0, n=50)
        assert power == 1.0

    def test_power_with_r_negative(self):
        """Power calculation should handle negative r."""
        power_pos = calculate_post_hoc_power(r_observed=0.4, n=50)
        power_neg = calculate_post_hoc_power(r_observed=-0.4, n=50)
        # Power should be similar for equal magnitude positive/negative r
        assert abs(power_pos - power_neg) < 0.01

    def test_power_bounds(self):
        """Power should always be between 0 and 1."""
        for r in [-0.9, -0.5, 0.0, 0.5, 0.9]:
            power = calculate_post_hoc_power(r_observed=r, n=50)
            assert 0.0 <= power <= 1.0

class TestRunPowerAnalysis:
    """Tests for the main power analysis runner."""

    @patch('analysis.power_analysis.get_config')
    def test_run_power_analysis_creates_file(self, mock_get_config, tmp_path):
        """Test that run_power_analysis creates the output file."""
        mock_get_config.return_value = {
            'paths': {
                'results': str(tmp_path)
            }
        }

        results_path = tmp_path / 'stats.json'
        # Create a mock stats file
        mock_stats = {
            'network_correlations': [
                {'network': 'DMN', 'rho': 0.3, 'fdr_corrected_p': 0.04},
                {'network': 'Salience', 'rho': 0.1, 'fdr_corrected_p': 0.3}
            ]
        }
        with open(results_path, 'w') as f:
            json.dump(mock_stats, f)

        output_path = tmp_path / 'power_analysis.json'
        results = run_power_analysis(
            n_subjects=50,
            results_path=results_path,
            output_path=output_path
        )

        assert output_path.exists()
        assert 'study_parameters' in results
        assert results['study_parameters']['n_subjects'] == 50
        assert 'detectable_effect' in results
        assert 'observed_power_analysis' in results

    @patch('analysis.power_analysis.get_config')
    def test_run_power_analysis_no_stats_file(self, mock_get_config, tmp_path):
        """Test behavior when stats file doesn't exist."""
        mock_get_config.return_value = {
            'paths': {
                'results': str(tmp_path)
            }
        }

        output_path = tmp_path / 'power_analysis.json'
        results = run_power_analysis(
            n_subjects=50,
            results_path=tmp_path / 'nonexistent.json',
            output_path=output_path
        )

        assert output_path.exists()
        assert results['observed_power_analysis']['status'] == 'skipped'

    @patch('analysis.power_analysis.get_config')
    def test_run_power_analysis_default_paths(self, mock_get_config, tmp_path):
        """Test that default paths are used when not specified."""
        mock_get_config.return_value = {
            'paths': {
                'results': str(tmp_path)
            }
        }

        results = run_power_analysis(n_subjects=50)

        assert results['study_parameters']['n_subjects'] == 50
        assert results['study_parameters']['alpha'] == 0.05
        assert results['study_parameters']['target_power'] == 0.80

    def test_run_power_analysis_with_different_n(self):
        """Test power analysis with different sample sizes."""
        # Create temp directory for output
        with patch('analysis.power_analysis.get_config') as mock_config:
            mock_config.return_value = {
                'paths': {
                    'results': str(Path.cwd())
                }
            }
            # Just test that it runs without error for different N
            results_n30 = run_power_analysis(n_subjects=30)
            results_n100 = run_power_analysis(n_subjects=100)

            # Detectable effect should be larger for smaller N
            assert results_n30['detectable_effect']['cohen_d'] > results_n100['detectable_effect']['cohen_d']