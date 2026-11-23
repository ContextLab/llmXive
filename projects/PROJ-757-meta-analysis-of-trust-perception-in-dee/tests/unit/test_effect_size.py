"""
Unit tests for effect size calculation module.

Tests:
- T019: Cohen's d calculation from means/SDs
- T020: Log-odds conversion from odds ratio
- T021: SD reconstruction logic and imputation logic
"""

import math
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from effect_size_calc import (
    parse_p_value,
    reconstruct_sd_from_t,
    reconstruct_sd_from_p,
    calculate_cohens_d,
    calculate_log_odds,
    calculate_variance_cohens_d,
    process_study,
    calculate_sensitivity_pool_sd,
    apply_sensitivity_imputation
)


class TestParsePValue:
    """Test p-value parsing logic."""

    def test_exact_p_value(self):
        assert parse_p_value("0.032") == 0.032
        assert parse_p_value("p = 0.05") == 0.05
        assert parse_p_value("p=0.01") == 0.01

    def test_inequality_p_value(self):
        assert parse_p_value("p < 0.05") == 0.05
        assert parse_p_value("p>0.1") == 0.1

    def test_invalid_p_value(self):
        assert parse_p_value("") is None
        assert parse_p_value(None) is None
        assert parse_p_value("invalid") is None
        assert parse_p_value("p = abc") is None


class TestReconstructSDFromT:
    """Test SD reconstruction from t-statistic."""

    def test_basic_reconstruction(self):
        # Example: mean1=10, mean2=8, t=2.5, n1=30, n2=30
        # sp = (10-8) / (2.5 * sqrt(1/30 + 1/30))
        mean1, mean2, t, n1, n2 = 10.0, 8.0, 2.5, 30, 30
        sd = reconstruct_sd_from_t(mean1, mean2, t, n1, n2)
        assert sd is not None
        assert sd > 0

    def test_zero_t_stat(self):
        assert reconstruct_sd_from_t(10, 8, 0, 30, 30) is None

    def test_invalid_sd_result(self):
        # Negative difference with positive t gives negative sd -> None
        assert reconstruct_sd_from_t(8, 10, 2.5, 30, 30) is None


class TestReconstructSDFromP:
    """Test SD reconstruction from p-value."""

    def test_valid_p_value(self):
        mean1, mean2, p_val, n1, n2 = 10.0, 8.0, 0.03, 30, 30
        sd = reconstruct_sd_from_p(mean1, mean2, p_val, n1, n2)
        # Should return a value (approximate)
        assert sd is not None

    def test_invalid_p_value(self):
        assert reconstruct_sd_from_p(10, 8, 0, 30, 30) is None
        assert reconstruct_sd_from_p(10, 8, 1.5, 30, 30) is None
        assert reconstruct_sd_from_p(10, 8, None, 30, 30) is None


class TestCohensD:
    """Test Cohen's d calculation."""

    def test_basic_cohens_d(self):
        mean1, mean2, sd1, sd2, n1, n2 = 10.0, 8.0, 2.0, 2.0, 30, 30
        d = calculate_cohens_d(mean1, mean2, sd1, sd2, n1, n2)
        # Expected: (10-8) / sqrt(((29*4 + 29*4)/58)) = 2 / 2 = 1.0
        assert abs(d - 1.0) < 0.001

    def test_negative_d(self):
        mean1, mean2, sd1, sd2, n1, n2 = 8.0, 10.0, 2.0, 2.0, 30, 30
        d = calculate_cohens_d(mean1, mean2, sd1, sd2, n1, n2)
        assert d < 0

    def test_invalid_sd(self):
        with pytest.raises(ValueError):
            calculate_cohens_d(10, 8, 0, 2, 30, 30)

        with pytest.raises(ValueError):
            calculate_cohens_d(10, 8, -1, 2, 30, 30)


class TestLogOdds:
    """Test log-odds conversion."""

    def test_basic_log_odds(self):
        or_val = 2.0
        log_odds = calculate_log_odds(or_val)
        assert abs(log_odds - math.log(2.0)) < 0.001

    def test_invalid_odds_ratio(self):
        with pytest.raises(ValueError):
            calculate_log_odds(0)

        with pytest.raises(ValueError):
            calculate_log_odds(-1)


class TestVarianceCohensD:
    """Test variance calculation for Cohen's d."""

    def test_basic_variance(self):
        n1, n2, d = 30, 30, 1.0
        var = calculate_variance_cohens_d(n1, n2, d)
        # Expected: (60/900) + (1/120) = 0.0667 + 0.0083 = 0.075
        expected = (n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2))
        assert abs(var - expected) < 0.0001


class TestProcessStudy:
    """Test study processing logic (FR-003 compliance)."""

    def test_case_a_sd_present(self):
        study = {
            'doi': 'test-001',
            'title': 'Test Study',
            'year': '2023',
            'source': 'arXiv',
            'p_value': '0.03',
            'n1': '30',
            'n2': '30',
            'mean1': '10.0',
            'mean2': '8.0',
            'sd1': '2.0',
            'sd2': '2.0',
            't_stat': '',
            'odds_ratio': ''
        }
        result = process_study(study)
        assert result['included_in_primary'] is True
        assert result['sd_reconstructed'] is False
        assert result['sd_imputed'] is False
        assert result['effect_size'] is not None
        assert result['effect_size_type'] == 'cohen_d'
        assert result['exclusion_reason'] is None

    def test_case_b_sd_missing_t_present(self):
        study = {
            'doi': 'test-002',
            'title': 'Test Study 2',
            'year': '2023',
            'source': 'arXiv',
            'p_value': '0.03',
            'n1': '30',
            'n2': '30',
            'mean1': '10.0',
            'mean2': '8.0',
            'sd1': '',
            'sd2': '',
            't_stat': '2.5',
            'odds_ratio': ''
        }
        result = process_study(study)
        assert result['included_in_primary'] is False  # Excluded from primary
        assert result['sd_reconstructed'] is True
        assert result['sensitivity_effect_size'] is not None
        assert result['exclusion_reason'] is None

    def test_case_c_sd_missing_p_exact(self):
        study = {
            'doi': 'test-003',
            'title': 'Test Study 3',
            'year': '2023',
            'source': 'arXiv',
            'p_value': '0.03',
            'n1': '30',
            'n2': '30',
            'mean1': '10.0',
            'mean2': '8.0',
            'sd1': '',
            'sd2': '',
            't_stat': '',
            'odds_ratio': ''
        }
        result = process_study(study)
        assert result['included_in_primary'] is False  # Excluded from primary
        assert result['sensitivity_effect_size'] is not None
        assert result['exclusion_reason'] is None

    def test_case_d_sd_missing_unrecoverable(self):
        study = {
            'doi': 'test-004',
            'title': 'Test Study 4',
            'year': '2023',
            'source': 'arXiv',
            'p_value': '',
            'n1': '30',
            'n2': '30',
            'mean1': '10.0',
            'mean2': '8.0',
            'sd1': '',
            'sd2': '',
            't_stat': '',
            'odds_ratio': ''
        }
        result = process_study(study)
        assert result['included_in_primary'] is False
        assert result['exclusion_reason'] == 'SD_UNRECOVERABLE'

    def test_odds_ratio_case(self):
        study = {
            'doi': 'test-005',
            'title': 'Test Study 5',
            'year': '2023',
            'source': 'arXiv',
            'p_value': '',
            'n1': '30',
            'n2': '30',
            'mean1': '',
            'mean2': '',
            'sd1': '',
            'sd2': '',
            't_stat': '',
            'odds_ratio': '2.5'
        }
        result = process_study(study)
        assert result['included_in_primary'] is True
        assert result['effect_size_type'] == 'log_odds'
        assert result['effect_size'] is not None


class TestSensitivityImputation:
    """Test sensitivity analysis imputation logic."""

    def test_apply_imputation(self):
        studies = [
            {
                'doi': 'test-001',
                'included_in_primary': True,
                'sd1': 2.0,
                'sd2': 2.0,
                'n1': 30,
                'n2': 30,
                'mean1': 10.0,
                'mean2': 8.0,
                'sd_reconstructed': False,
                'sd_imputed': False,
                'sensitivity_effect_size': None
            },
            {
                'doi': 'test-002',
                'included_in_primary': False,
                'sd1': None,
                'sd2': None,
                'n1': 30,
                'n2': 30,
                'mean1': 10.0,
                'mean2': 8.0,
                'sd_reconstructed': True,
                'sd_imputed': False,
                'sensitivity_effect_size': None
            }
        ]

        result = apply_sensitivity_imputation(studies)

        # First study should remain unchanged
        assert result[0]['sensitivity_effect_size'] is None

        # Second study should get imputed sensitivity effect size
        assert result[1]['sensitivity_effect_size'] is not None
        assert result[1]['sd_imputed'] is True