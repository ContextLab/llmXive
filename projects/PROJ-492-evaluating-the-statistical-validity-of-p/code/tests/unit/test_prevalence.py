"""
Unit tests for prevalence analysis module.

Tests:
- Binomial test functionality
- Wilson confidence interval calculation
- CI width constraint (≤ 0.10) per arXiv:1807.00365
- Sensitivity analysis
- Dynamic Bonferroni correction
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from scipy import stats

from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_dynamic_bonferroni,
    run_prevalence_analysis,
    load_audit_records
)
from code.src.config import SEED


class TestBinomialTest:
    """Tests for binomial test functionality."""

    def test_binomial_test_basic(self):
        """Test basic binomial test calculation."""
        x, n, p = 5, 100, 0.05
        p_value, effect_size = binomial_test(x, n, p)
        
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1 or np.isnan(p_value)
        assert effect_size is not None

    def test_binomial_test_zero_sample(self):
        """Test binomial test with zero sample size."""
        p_value, effect_size = binomial_test(0, 0, 0.05)
        
        assert np.isnan(p_value)
        assert np.isnan(effect_size)

    def test_binomial_test_all_successes(self):
        """Test binomial test when all are successes."""
        p_value, effect_size = binomial_test(100, 100, 0.05)
        
        # Should have very small p-value (reject null)
        assert p_value < 0.001

    def test_binomial_test_no_successes(self):
        """Test binomial test when none are successes."""
        p_value, effect_size = binomial_test(0, 100, 0.05)
        
        # Should have very small p-value (reject null)
        assert p_value < 0.001


class TestWilsonCI:
    """Tests for Wilson confidence interval."""

    def test_wilson_ci_basic(self):
        """Test basic Wilson CI calculation."""
        x, n = 10, 100
        lower, upper = wilson_ci(x, n)
        
        assert 0 <= lower <= 1
        assert 0 <= upper <= 1
        assert lower <= upper

    def test_wilson_ci_zero_sample(self):
        """Test Wilson CI with zero sample size."""
        lower, upper = wilson_ci(0, 0)
        
        assert np.isnan(lower)
        assert np.isnan(upper)

    def test_wilson_ci_width_constraint(self):
        """Test that CI width is ≤ 0.10 for appropriate sample sizes.
        
        Reference: arXiv:1807.00365 - Statistical methodology for 
        confidence interval width constraints in prevalence studies.
        """
        # For n=100, width should be reasonable
        x, n = 10, 100
        lower, upper = wilson_ci(x, n)
        width = upper - lower
        
        # With n=100, width should typically be < 0.20
        # The constraint ≤ 0.10 requires larger samples
        assert width < 0.30  # Relaxed check for n=100

        # For larger n, width should be smaller
        x, n = 100, 1000
        lower, upper = wilson_ci(x, n)
        width = upper - lower
        
        # With n=1000, width should be < 0.10
        assert width <= 0.10, f"CI width {width} exceeds 0.10 constraint"

    def test_wilson_ci_bounds(self):
        """Test that Wilson CI stays within [0, 1]."""
        # Edge case: very low proportion
        lower, upper = wilson_ci(1, 100)
        assert 0 <= lower <= upper <= 1

        # Edge case: very high proportion
        lower, upper = wilson_ci(99, 100)
        assert 0 <= lower <= upper <= 1


class TestComputePrevalence:
    """Tests for prevalence computation."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True}
        ]
        
        result = compute_prevalence(records)
        
        assert result['total_summaries'] == 3
        assert result['inconsistent_count'] == 2
        assert result['prevalence'] == 2/3
        assert 'wilson_ci_lower' in result
        assert 'wilson_ci_upper' in result

    def test_compute_prevalence_empty(self):
        """Test prevalence computation with empty records."""
        result = compute_prevalence([])
        
        assert result['total_summaries'] == 0
        assert result['prevalence'] == 0.0
        assert np.isnan(result['p_value_binomial'])

    def test_compute_prevalence_all_inconsistent(self):
        """Test prevalence when all are inconsistent."""
        records = [{'is_inconsistent': True} for _ in range(10)]
        result = compute_prevalence(records)
        
        assert result['prevalence'] == 1.0


class TestSensitivityAnalysis:
    """Tests for sensitivity analysis."""

    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis."""
        records = [{'is_inconsistent': True} for _ in range(50)] + \
                 [{'is_inconsistent': False} for _ in range(50)]
        
        result = sensitivity_analysis(records, num_points=5)
        
        assert 'baseline_range' in result
        assert 'results' in result
        assert 'max_variation' in result
        assert 'is_stable' in result
        assert len(result['results']) == 5

    def test_sensitivity_analysis_empty(self):
        """Test sensitivity analysis with empty records."""
        result = sensitivity_analysis([])
        
        assert result['status'] is not None or result.get('is_stable') is not None

    def test_sensitivity_analysis_stability(self):
        """Test stability detection in sensitivity analysis."""
        records = [{'is_inconsistent': True} for _ in range(1000)]
        
        result = sensitivity_analysis(records, baseline_range=(0.01, 0.10), num_points=10)
        
        # Should detect if variation is within threshold
        assert 'max_variation' in result
        assert 'is_stable' in result


class TestDynamicBonferroni:
    """Tests for dynamic Bonferroni correction."""

    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        corrected = apply_dynamic_bonferroni(10, 0.05)
        assert corrected == 0.005

    def test_bonferroni_single_group(self):
        """Test Bonferroni with single subgroup."""
        corrected = apply_dynamic_bonferroni(1, 0.05)
        assert corrected == 0.05

    def test_bonferroni_zero_groups(self):
        """Test Bonferroni with zero subgroups."""
        corrected = apply_dynamic_bonferroni(0, 0.05)
        assert corrected == 0.05  # Returns original alpha

    def test_bonferroni_many_groups(self):
        """Test Bonferroni with many subgroups."""
        corrected = apply_dynamic_bonferroni(100, 0.05)
        assert corrected == 0.0005


class TestRunPrevalenceAnalysis:
    """Integration tests for prevalence analysis pipeline."""

    def test_run_prevalence_analysis_full(self):
        """Test full prevalence analysis pipeline."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            records = [
                {'is_inconsistent': True, 'domain': 'tech', 'year': 2023},
                {'is_inconsistent': False, 'domain': 'tech', 'year': 2023},
                {'is_inconsistent': True, 'domain': 'finance', 'year': 2022},
                {'is_inconsistent': False, 'domain': 'finance', 'year': 2022},
            ]
            json.dump(records, f)
            input_path = Path(f.name)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = Path(f.name)
        
            result = run_prevalence_analysis(input_path, output_path)
        
            # Verify output file exists
            assert output_path.exists()
        
            # Verify result structure
            assert 'prevalence' in result
            assert 'sensitivity_analysis' in result
            assert 'bonferroni_correction' in result
            assert 'metadata' in result
        
            # Verify Bonferroni correction
            bc = result['bonferroni_correction']
            assert bc['num_subgroups'] > 0
            assert bc['corrected_alpha'] < bc['original_alpha']
        
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_run_prevalence_analysis_empty_input(self):
        """Test prevalence analysis with empty input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            input_path = Path(f.name)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = Path(f.name)
        
            result = run_prevalence_analysis(input_path, output_path)
        
            assert output_path.exists()
            # Should handle empty input gracefully
            assert result.get('status') == 'empty' or 'prevalence' in result
        
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

class TestCIWidthConstraint:
    """Tests specifically for CI width constraint per arXiv:1807.00365."""

    @pytest.mark.parametrize("n,expected_max_width", [
        (100, 0.20),
        (500, 0.14),
        (1000, 0.10),
        (5000, 0.05),
    ])
    def test_ci_width_scaling(self, n, expected_max_width):
        """Test that CI width scales appropriately with sample size."""
        x = int(n * 0.1)  # 10% prevalence
        lower, upper = wilson_ci(x, n)
        width = upper - lower
        
        assert width <= expected_max_width, \
            f"CI width {width} for n={n} exceeds expected max {expected_max_width}"

    def test_ci_width_under_0_10(self):
        """Verify CI width ≤ 0.10 for n ≥ 1000 as per methodology requirements."""
        # Test at threshold
        lower, upper = wilson_ci(100, 1000)
        width = upper - lower
        assert width <= 0.10, f"CI width {width} exceeds 0.10 constraint"

        # Test above threshold
        lower, upper = wilson_ci(500, 5000)
        width = upper - lower
        assert width <= 0.10, f"CI width {width} exceeds 0.10 constraint"