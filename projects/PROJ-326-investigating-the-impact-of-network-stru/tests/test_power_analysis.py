"""
Tests for the power analysis module.
"""

import json
import math
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from code.src.analysis.power import (
    PowerAnalysisError,
    calculate_effect_size_r_to_cohen_d,
    calculate_power_t_test_two_tailed,
    compute_effect_size_from_regression,
    compute_effect_size_from_anova,
    compute_power_analysis,
    generate_power_report,
    main
)


class TestEffectSizeCalculations:
    """Tests for effect size conversion functions."""

    def test_r_to_cohen_d_positive_correlation(self):
        """Test conversion of positive correlation to Cohen's d."""
        r = 0.5
        n1, n2 = 50, 50
        d = calculate_effect_size_r_to_cohen_d(r, n1, n2)
        expected = (2 * r) / math.sqrt(1 - r * r)
        assert abs(d - expected) < 1e-6

    def test_r_to_cohen_d_negative_correlation(self):
        """Test conversion of negative correlation to Cohen's d."""
        r = -0.5
        n1, n2 = 50, 50
        d = calculate_effect_size_r_to_cohen_d(r, n1, n2)
        expected = (2 * r) / math.sqrt(1 - r * r)
        assert abs(d - expected) < 1e-6

    def test_r_to_cohen_d_zero_correlation(self):
        """Test conversion of zero correlation."""
        r = 0.0
        n1, n2 = 50, 50
        d = calculate_effect_size_r_to_cohen_d(r, n1, n2)
        assert abs(d) < 1e-6

    def test_r_to_cohen_d_edge_case_r_near_one(self):
        """Test conversion when r is near 1 (should be clipped)."""
        r = 0.99999
        n1, n2 = 50, 50
        # Should not raise an exception
        d = calculate_effect_size_r_to_cohen_d(r, n1, n2)
        assert math.isfinite(d)


class TestPowerCalculations:
    """Tests for power calculation functions."""

    def test_calculate_power_t_test_valid_inputs(self):
        """Test power calculation with valid inputs."""
        effect_size = 0.5  # Medium effect size
        n1, n2 = 50, 50
        alpha = 0.05
        power = calculate_power_t_test_two_tailed(effect_size, n1, n2, alpha)
        assert 0 <= power <= 1

    def test_calculate_power_t_test_large_sample(self):
        """Test that power increases with sample size."""
        effect_size = 0.5
        alpha = 0.05
        power_small = calculate_power_t_test_two_tailed(effect_size, 20, 20, alpha)
        power_large = calculate_power_t_test_two_tailed(effect_size, 100, 100, alpha)
        assert power_large > power_small

    def test_calculate_power_t_test_zero_effect_size(self):
        """Test power calculation with zero effect size."""
        effect_size = 0.0
        n1, n2 = 50, 50
        alpha = 0.05
        power = calculate_power_t_test_two_tailed(effect_size, n1, n2, alpha)
        # Power should equal alpha when effect size is 0
        assert abs(power - alpha) < 0.01

    def test_calculate_power_invalid_sample_size(self):
        """Test power calculation with invalid sample sizes."""
        with pytest.raises(PowerAnalysisError):
            calculate_power_t_test_two_tailed(0.5, 0, 50)

        with pytest.raises(PowerAnalysisError):
            calculate_power_t_test_two_tailed(0.5, 50, -10)


class TestEffectSizeExtraction:
    """Tests for effect size extraction from results."""

    def test_compute_effect_size_from_regression(self):
        """Test effect size extraction from regression results."""
        regression_results = {
            'sample_data': {'total_samples': 100},
            'results': [
                {'r_squared': 0.25, 'coefficient': 0.5}
            ]
        }
        effect_size, n1, n2 = compute_effect_size_from_regression(regression_results)
        assert math.isfinite(effect_size)
        assert n1 + n2 == 100

    def test_compute_effect_size_from_regression_no_sample_data(self):
        """Test effect size extraction when sample data is missing."""
        regression_results = {
            'results': [
                {'r_squared': 0.25, 'coefficient': 0.5}
            ]
        }
        effect_size, n1, n2 = compute_effect_size_from_regression(regression_results)
        assert math.isfinite(effect_size)
        assert n1 + n2 > 0  # Should use fallback

    def test_compute_effect_size_from_anova(self):
        """Test effect size extraction from ANOVA results."""
        anova_results = {
            'results': [
                {
                    'f_statistic': 5.0,
                    'df_between': 2,
                    'df_within': 97
                }
            ]
        }
        effect_size, n1, n2 = compute_effect_size_from_anova(anova_results)
        assert math.isfinite(effect_size)

    def test_compute_effect_size_from_anova_no_results(self):
        """Test effect size extraction when ANOVA results are missing."""
        anova_results = {}
        effect_size, n1, n2 = compute_effect_size_from_anova(anova_results)
        # Should return default values
        assert effect_size == 0.3
        assert n1 == 50
        assert n2 == 50


class TestPowerAnalysisIntegration:
    """Integration tests for the power analysis module."""

    @pytest.fixture
    def temp_results_file(self, tmp_path):
        """Create a temporary final_results.json file."""
        results = {
            'regression_results': {
                'sample_data': {'total_samples': 100},
                'results': [
                    {'r_squared': 0.25, 'coefficient': 0.5}
                ]
            },
            'anova_results': {
                'results': [
                    {
                        'f_statistic': 5.0,
                        'df_between': 2,
                        'df_within': 97
                    }
                ]
            }
        }
        file_path = tmp_path / 'final_results.json'
        with open(file_path, 'w') as f:
            json.dump(results, f)
        return file_path

    def test_compute_power_analysis(self, temp_results_file):
        """Test full power analysis computation."""
        config = {'target_power': 0.80, 'alpha': 0.05}
        result = compute_power_analysis(temp_results_file, config)

        assert 'timestamp' in result
        assert 'parameters' in result
        assert 'results' in result
        assert 'conclusion' in result
        assert 'regression' in result['results']
        assert 'anova' in result['results']
        assert 'calculated_power' in result['results']['regression']
        assert 'calculated_power' in result['results']['anova']

    def test_generate_power_report(self, temp_results_file, tmp_path):
        """Test power report generation."""
        config = {'target_power': 0.80, 'alpha': 0.05}
        result = compute_power_analysis(temp_results_file, config)

        output_path = tmp_path / 'power_analysis_report.json'
        generate_power_report(result, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        assert saved_result == result

    def test_main_function(self, temp_results_file, tmp_path):
        """Test the main function entry point."""
        output_path = tmp_path / 'power_analysis_report.json'
        result = main(str(temp_results_file), str(output_path))

        assert output_path.exists()
        assert 'conclusion' in result
        assert 'overall_target_met' in result['conclusion']

    def test_main_missing_input_file(self, tmp_path):
        """Test main function with missing input file."""
        output_path = tmp_path / 'power_analysis_report.json'
        with pytest.raises(PowerAnalysisError):
            main(str(tmp_path / 'nonexistent.json'), str(output_path))