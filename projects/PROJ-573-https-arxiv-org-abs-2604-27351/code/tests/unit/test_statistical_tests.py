"""
Unit tests for statistical_tests module.
Tests paired t-test, Wilcoxon test, and bootstrap CI functions.
"""

import pytest
import numpy as np
from src.evaluation.statistical_tests import (
    paired_ttest,
    wilcoxon_effect_size,
    bootstrap_ci,
    get_effect_size_interpretation,
    run_full_statistical_analysis,
    generate_analysis_summary
)


class TestPairedTTest:
    """Tests for paired_ttest function."""

    def test_basic_paired_ttest(self):
        """Test basic paired t-test functionality."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.5, 2.5, 3.5, 4.5, 5.5]

        result = paired_ttest(a, b)

        assert result['t_statistic'] > 0  # b > a
        assert result['p_value'] < 0.05  # Should be significant
        assert result['mean_diff'] == 0.5
        assert result['n_pairs'] == 5
        assert result['significant'] is True
        assert 'ci_95' in result
        assert result['effect_size_cohen_d'] > 0

    def test_equal_conditions(self):
        """Test when conditions are equal (no difference)."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = paired_ttest(a, b)

        assert result['t_statistic'] == 0.0
        assert result['p_value'] == 1.0
        assert result['mean_diff'] == 0.0
        assert result['significant'] is False

    def test_unequal_lengths_raises_error(self):
        """Test that unequal lengths raise ValueError."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0]

        with pytest.raises(ValueError):
            paired_ttest(a, b)

    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises ValueError."""
        a = [1.0]
        b = [1.5]

        with pytest.raises(ValueError):
            paired_ttest(a, b)


class TestWilcoxonEffectSize:
    """Tests for wilcoxon_effect_size function."""

    def test_basic_wilcoxon(self):
        """Test basic Wilcoxon signed-rank test."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.5, 2.5, 3.5, 4.5, 5.5]

        result = wilcoxon_effect_size(a, b)

        assert result['statistic'] >= 0
        assert 0 <= result['p_value'] <= 1
        assert result['n_pairs'] == 5
        assert result['n_nonzero'] > 0
        assert 'effect_size_r' in result

    def test_equal_conditions_wilcoxon(self):
        """Test when conditions are equal."""
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = wilcoxon_effect_size(a, b)

        assert result['p_value'] == 1.0
        assert result['significant'] is False

    def test_unequal_lengths_raises_error(self):
        """Test that unequal lengths raise ValueError."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0]

        with pytest.raises(ValueError):
            wilcoxon_effect_size(a, b)


class TestBootstrapCI:
    """Tests for bootstrap_ci function."""

    def test_basic_bootstrap_ci(self):
        """Test basic bootstrap confidence interval."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result = bootstrap_ci(values, n_bootstrap=1000, seed=42)

        assert result['mean'] == 5.5
        assert result['n'] == 10
        assert result['ci_lower'] < result['mean']
        assert result['ci_upper'] > result['mean']
        assert result['ci_width'] > 0
        assert result['n_bootstrap'] == 1000

    def test_narrow_ci_with_large_sample(self):
        """Test that larger samples give narrower CIs."""
        np.random.seed(42)
        small_sample = np.random.normal(5.0, 1.0, 10)
        large_sample = np.random.normal(5.0, 1.0, 1000)

        ci_small = bootstrap_ci(small_sample, n_bootstrap=1000, seed=42)
        ci_large = bootstrap_ci(large_sample, n_bootstrap=1000, seed=42)

        # Larger sample should have narrower CI
        assert ci_large['ci_width'] < ci_small['ci_width']

    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises ValueError."""
        with pytest.raises(ValueError):
            bootstrap_ci([1.0], n_bootstrap=100)


class TestEffectSizeInterpretation:
    """Tests for get_effect_size_interpretation function."""

    def test_cohen_d_small(self):
        """Test Cohen's d small effect interpretation."""
        assert 'small' in get_effect_size_interpretation(0.15, 'cohen_d')
        assert 'small' in get_effect_size_interpretation(-0.15, 'cohen_d')

    def test_cohen_d_medium(self):
        """Test Cohen's d medium effect interpretation."""
        assert 'medium' in get_effect_size_interpretation(0.4, 'cohen_d')
        assert 'medium' in get_effect_size_interpretation(-0.4, 'cohen_d')

    def test_cohen_d_large(self):
        """Test Cohen's d large effect interpretation."""
        assert 'large' in get_effect_size_interpretation(1.0, 'cohen_d')
        assert 'large' in get_effect_size_interpretation(-1.0, 'cohen_d')

    def test_cohen_r_small(self):
        """Test Cohen's r small effect interpretation."""
        assert 'small' in get_effect_size_interpretation(0.05, 'cohen_r')

    def test_cohen_r_medium(self):
        """Test Cohen's r medium effect interpretation."""
        assert 'medium' in get_effect_size_interpretation(0.3, 'cohen_r')


class TestFullStatisticalAnalysis:
    """Tests for run_full_statistical_analysis function."""

    def test_full_pipeline(self):
        """Test complete statistical analysis pipeline."""
        a = [0.72, 0.75, 0.68, 0.71, 0.74]
        b = [0.78, 0.80, 0.75, 0.77, 0.79]

        result = run_full_statistical_analysis(a, b, alpha=0.05, n_bootstrap=500, seed=42)

        # Check all components present
        assert 't_test' in result
        assert 'wilcoxon' in result
        assert 'bootstrap_ci_difference' in result
        assert 'primary_outcome' in result
        assert 'effect_sizes' in result
        assert 'significance_summary' in result

        # Check primary outcome structure
        po = result['primary_outcome']
        assert 'lower' in po
        assert 'upper' in po
        assert 'mean_diff' in po
        assert 'formula' in po

        # Check effect sizes
        assert 'cohen_d' in result['effect_sizes']
        assert 'wilcoxon_r' in result['effect_sizes']
        assert 'interpretation_d' in result['effect_sizes']
        assert 'interpretation_r' in result['effect_sizes']

    def test_n_comparisons_count(self):
        """Test that n_comparisons is tracked ({{claim:c_55db4237}})."""
        a = [1.0, 2.0, 3.0]
        b = [1.5, 2.5, 3.5]

        result = run_full_statistical_analysis(a, b)

        assert 'n_comparisons' in result
        assert result['n_comparisons'] >= 1


class TestGenerateAnalysisSummary:
    """Tests for generate_analysis_summary function."""

    def test_summary_generation(self):
        """Test that summary is generated correctly."""
        a = [0.72, 0.75, 0.68]
        b = [0.78, 0.80, 0.75]

        analysis = run_full_statistical_analysis(a, b, n_bootstrap=100)
        summary = generate_analysis_summary(analysis)

        assert isinstance(summary, str)
        assert len(summary) > 100
        assert "STATISTICAL ANALYSIS SUMMARY" in summary
        assert "PAIRED T-TEST" in summary
        assert "WILCOXON" in summary
        assert "BOOTSTRAP 95% CI" in summary
