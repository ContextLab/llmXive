import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.effect_sizes import (
    calculate_cohens_d,
    calculate_paired_cohens_d,
    bonferroni_correction,
    holm_bonferroni_correction,
    perform_pairwise_comparisons_by_stratum,
    verify_paired_output,
    run_effect_size_pipeline,
    PairwiseComparison,
    EffectSizeResult
)


class TestCohensD:
    """Tests for Cohen's d calculation."""

    def test_calculate_cohens_d_basic(self):
        """Test basic Cohen's d calculation."""
        group1 = np.array([10, 12, 11, 13, 12])
        group2 = np.array([8, 9, 7, 10, 8])

        d, mean_diff, pooled_std = calculate_cohens_d(group1, group2)

        assert d > 0, "Effect size should be positive (group1 > group2)"
        assert mean_diff > 0, "Mean difference should be positive"
        assert pooled_std > 0, "Pooled std should be positive"
        assert isinstance(d, float), "Cohen's d should be a float"

    def test_calculate_cohens_d_negative(self):
        """Test Cohen's d with group1 < group2."""
        group1 = np.array([5, 6, 5, 7])
        group2 = np.array([10, 12, 11, 13])

        d, mean_diff, _ = calculate_cohens_d(group1, group2)

        assert d < 0, "Effect size should be negative (group1 < group2)"
        assert mean_diff < 0, "Mean difference should be negative"

    def test_calculate_cohens_d_identical(self):
        """Test Cohen's d with identical groups."""
        group1 = np.array([5, 5, 5, 5])
        group2 = np.array([5, 5, 5, 5])

        d, mean_diff, pooled_std = calculate_cohens_d(group1, group2)

        assert d == 0.0, "Cohen's d should be 0 for identical groups"
        assert mean_diff == 0.0, "Mean difference should be 0"
        assert pooled_std == 0.0, "Pooled std should be 0"

    def test_calculate_paired_cohens_d(self):
        """Test paired Cohen's d calculation."""
        pre = np.array([10, 12, 11, 13, 12])
        post = np.array([8, 9, 7, 10, 8])

        d, mean_diff, std_diff = calculate_paired_cohens_d(pre, post)

        assert d > 0, "Paired Cohen's d should be positive"
        assert mean_diff > 0, "Mean difference should be positive"
        assert std_diff > 0, "Std of differences should be positive"

    def test_calculate_paired_cohens_d_length_mismatch(self):
        """Test that paired calculation raises error on length mismatch."""
        pre = np.array([1, 2, 3])
        post = np.array([1, 2])

        with pytest.raises(ValueError):
            calculate_paired_cohens_d(pre, post)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni with single test."""
        p_values = [0.03]
        results = bonferroni_correction(p_values, alpha=0.05)

        assert len(results) == 1
        raw, adj, sig = results[0]
        assert raw == 0.03
        assert adj == 0.03  # 0.03 * 1 = 0.03
        assert sig is True

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni with multiple tests."""
        p_values = [0.01, 0.03, 0.06, 0.10]
        results = bonferroni_correction(p_values, alpha=0.05)

        assert len(results) == 4

        # Check that adjusted p-values are correctly calculated
        # adj_p = min(p * m, 1.0)
        m = 4
        expected_adj = [min(0.01 * m, 1.0), min(0.03 * m, 1.0), min(0.06 * m, 1.0), min(0.10 * m, 1.0)]

        for i, (_, adj, _) in enumerate(results):
            assert np.isclose(adj, expected_adj[i])

        # Check significance
        # adj_p < 0.05
        expected_sig = [True, True, False, False]
        for i, (_, _, sig) in enumerate(results):
            assert sig == expected_sig[i]

    def test_bonferroni_empty_list(self):
        """Test Bonferroni with empty list."""
        results = bonferroni_correction([], alpha=0.05)
        assert results == []

    def test_bonferroni_caps_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        results = bonferroni_correction(p_values, alpha=0.05)

        for _, adj, _ in results:
            assert adj <= 1.0


class TestHolmBonferroniCorrection:
    """Tests for Holm-Bonferroni correction."""

    def test_holm_basic(self):
        """Test Holm-Bonferroni with basic p-values."""
        p_values = [0.01, 0.03, 0.06, 0.10]
        results = holm_bonferroni_correction(p_values, alpha=0.05)

        assert len(results) == 4

        # Holm is less conservative than Bonferroni
        # Check that at least some results are different from Bonferroni
        bonf_results = bonferroni_correction(p_values, alpha=0.05)

        for i, ((raw_h, adj_h, sig_h), (raw_b, adj_b, sig_b)) in enumerate(zip(results, bonf_results)):
            assert raw_h == raw_b
            # Holm adjusted p-values should be <= Bonferroni (more powerful)
            assert adj_h <= adj_b

    def test_holm_significance(self):
        """Test Holm-Bonferroni significance determination."""
        p_values = [0.01, 0.02, 0.06, 0.10]
        results = holm_bonferroni_correction(p_values, alpha=0.05)

        # With Holm:
        # m=4: 0.01 < 0.05/4=0.0125 -> sig
        # m=3: 0.02 < 0.05/3=0.0167 -> sig
        # m=2: 0.06 < 0.05/2=0.025 -> not sig
        # m=1: 0.10 < 0.05/1=0.05 -> not sig
        expected_sig = [True, True, False, False]

        for i, (_, _, sig) in enumerate(results):
            assert sig == expected_sig[i]

    def test_holm_empty_list(self):
        """Test Holm-Bonferroni with empty list."""
        results = holm_bonferroni_correction([], alpha=0.05)
        assert results == []

    def test_holm_monotonicity(self):
        """Test that adjusted p-values are monotonic."""
        p_values = [0.05, 0.03, 0.01, 0.02]  # Unsorted
        results = holm_bonferroni_correction(p_values, alpha=0.05)

        # Extract adjusted p-values in original order
        adj_p = [r[1] for r in results]

        # When sorted by original p-value, adjusted p-values should be non-decreasing
        sorted_pairs = sorted(zip(p_values, adj_p), key=lambda x: x[0])
        sorted_adj = [p[1] for p in sorted_pairs]

        for i in range(len(sorted_adj) - 1):
            assert sorted_adj[i] <= sorted_adj[i + 1]


class TestPairwiseComparisons:
    """Tests for pairwise comparisons by stratum."""

    def create_test_data(self):
        """Create test DataFrame."""
        data = {
            'task_time': [10, 12, 11, 8, 9, 7, 15, 14, 16, 12, 13, 11],
            'tool_usage': ['AI', 'AI', 'AI', 'AI', 'AI', 'AI', 'Manual', 'Manual', 'Manual', 'Manual', 'Manual', 'Manual'],
            'experience_level': ['Novice', 'Novice', 'Novice', 'Expert', 'Expert', 'Expert',
                                 'Novice', 'Novice', 'Novice', 'Expert', 'Expert', 'Expert']
        }
        return pd.DataFrame(data)

    def test_perform_pairwise_comparisons_basic(self):
        """Test basic pairwise comparison."""
        df = self.create_test_data()

        result = perform_pairwise_comparisons_by_stratum(
            df, 'task_time', 'tool_usage', 'experience_level', alpha=0.05, correction_method='holm'
        )

        assert isinstance(result, EffectSizeResult)
        assert result.n_tests > 0
        assert len(result.comparisons) == result.n_tests
        assert result.correction_method == 'holm'

    def test_pairwise_comparisons_has_effect_sizes(self):
        """Test that all comparisons include effect sizes."""
        df = self.create_test_data()

        result = perform_pairwise_comparisons_by_stratum(
            df, 'task_time', 'tool_usage', 'experience_level', alpha=0.05, correction_method='bonferroni'
        )

        for comp in result.comparisons:
            assert 'cohens_d' in comp
            assert 'mean_diff' in comp
            assert 'p_value' in comp
            assert 'p_value_adjusted' in comp

    def test_pairwise_comparisons_stratification(self):
        """Test that comparisons are stratified correctly."""
        df = self.create_test_data()

        result = perform_pairwise_comparisons_by_stratum(
            df, 'task_time', 'tool_usage', 'experience_level', alpha=0.05, correction_method='holm'
        )

        # Should have comparisons for both Novice and Expert
        strata = set(c['stratum'] for c in result.comparisons)
        assert 'Novice' in strata
        assert 'Expert' in strata

    def test_pairwise_comparisons_empty_data(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=['task_time', 'tool_usage', 'experience_level'])

        result = perform_pairwise_comparisons_by_stratum(
            df, 'task_time', 'tool_usage', 'experience_level', alpha=0.05, correction_method='holm'
        )

        assert result.n_tests == 0
        assert len(result.comparisons) == 0


class TestVerifyPairedOutput:
    """Tests for paired output verification."""

    def test_verify_paired_output_success(self):
        """Test verification passes with complete data."""
        result = EffectSizeResult(
            comparisons=[
                {
                    'group1': 'A', 'group2': 'B',
                    'cohens_d': 0.5, 'p_value': 0.03, 'p_value_adjusted': 0.06,
                    'mean_diff': 2.0, 'significant': False, 'stratum': 'Novice', 'n1': 10, 'n2': 10
                }
            ],
            correction_method='holm',
            alpha=0.05,
            n_tests=1,
            significant_count=0,
            family_wise_error_rate=0.05,
            raw_p_values=[0.03],
            adjusted_p_values=[0.06]
        )

        assert verify_paired_output(result) is True

    def test_verify_paired_output_missing_cohens_d(self):
        """Test verification fails with missing Cohen's d."""
        result = EffectSizeResult(
            comparisons=[
                {
                    'group1': 'A', 'group2': 'B',
                    'p_value': 0.03, 'p_value_adjusted': 0.06,
                    'mean_diff': 2.0, 'significant': False, 'stratum': 'Novice', 'n1': 10, 'n2': 10
                }
            ],
            correction_method='holm',
            alpha=0.05,
            n_tests=1,
            significant_count=0,
            family_wise_error_rate=0.05,
            raw_p_values=[0.03],
            adjusted_p_values=[0.06]
        )

        assert verify_paired_output(result) is False

    def test_verify_paired_output_missing_p_value(self):
        """Test verification fails with missing p-value."""
        result = EffectSizeResult(
            comparisons=[
                {
                    'group1': 'A', 'group2': 'B',
                    'cohens_d': 0.5, 'p_value_adjusted': 0.06,
                    'mean_diff': 2.0, 'significant': False, 'stratum': 'Novice', 'n1': 10, 'n2': 10
                }
            ],
            correction_method='holm',
            alpha=0.05,
            n_tests=1,
            significant_count=0,
            family_wise_error_rate=0.05,
            raw_p_values=[0.03],
            adjusted_p_values=[0.06]
        )

        assert verify_paired_output(result) is False


class TestEffectSizePipeline:
    """Integration tests for the effect size pipeline."""

    def test_run_effect_size_pipeline(self, tmp_path):
        """Test running the full pipeline."""
        # Create test data
        data = {
            'task_time': [10, 12, 11, 8, 9, 7, 15, 14, 16, 12, 13, 11],
            'tool_usage': ['AI', 'AI', 'AI', 'AI', 'AI', 'AI', 'Manual', 'Manual', 'Manual', 'Manual', 'Manual', 'Manual'],
            'experience_level': ['Novice', 'Novice', 'Novice', 'Expert', 'Expert', 'Expert',
                                 'Novice', 'Novice', 'Novice', 'Expert', 'Expert', 'Expert']
        }
        df = pd.DataFrame(data)

        input_path = tmp_path / 'test_data.csv'
        output_path = tmp_path / 'test_output.json'

        df.to_csv(input_path, index=False)

        result = run_effect_size_pipeline(
            data_path=str(input_path),
            outcome_var='task_time',
            group_var='tool_usage',
            stratum_var='experience_level',
            alpha=0.05,
            correction_method='holm',
            output_path=str(output_path)
        )

        assert result.n_tests > 0
        assert output_path.exists()

        # Verify output file contains expected keys
        import json
        with open(output_path, 'r') as f:
            output_data = json.load(f)

        assert 'comparisons' in output_data
        assert 'correction_method' in output_data
        assert 'significant_count' in output_data