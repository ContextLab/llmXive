"""
Unit tests for Holm-Bonferroni correction in hypothesis testing (T021).

Verifies that:
1. Holm-Bonferroni correction is correctly applied
2. Corrected p-values are monotonic
3. Significance decisions match expected behavior
"""

import pytest
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.hypothesis_testing import (
    perform_pairwise_comparisons,
    analyze_hypotheses,
    perform_kruskal_wallis
)


class TestHolmBonferroniCorrection:
    """Tests for Holm-Bonferroni correction implementation."""

    def test_holm_correction_monotonicity(self):
        """Test that Holm-corrected p-values are monotonic with raw p-values."""
        # Create synthetic groups with known differences
        np.random.seed(42)
        groups = {
            'lang_a': np.random.normal(10, 2, 100),
            'lang_b': np.random.normal(12, 2, 100),
            'lang_c': np.random.normal(10, 2, 100),
            'lang_d': np.random.normal(15, 2, 100),
        }

        results = perform_pairwise_comparisons(groups)

        # Extract corrected p-values
        corrected_pvalues = [r['holm_corrected_pvalue'] for r in results]

        # Extract raw p-values
        raw_pvalues = [r['raw_pvalue'] for r in results]

        # Sort by raw p-value
        sorted_indices = np.argsort(raw_pvalues)
        sorted_corrected = [corrected_pvalues[i] for i in sorted_indices]

        # Holm-corrected p-values should be non-decreasing when sorted by raw p-value
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i + 1], \
                "Holm-corrected p-values should be non-decreasing"

    def test_holm_correction_less_conservative_than_bonferroni(self):
        """Test that Holm is less conservative than standard Bonferroni."""
        np.random.seed(42)
        groups = {
            'lang_a': np.random.normal(10, 2, 50),
            'lang_b': np.random.normal(12, 2, 50),
            'lang_c': np.random.normal(10, 2, 50),
            'lang_d': np.random.normal(15, 2, 50),
            'lang_e': np.random.normal(10, 2, 50),
        }

        results = perform_pairwise_comparisons(groups)

        raw_pvalues = [r['raw_pvalue'] for r in results]
        holm_corrected = [r['holm_corrected_pvalue'] for r in results]

        # Compute Bonferroni manually
        n_tests = len(raw_pvalues)
        bonf_corrected = [p * n_tests for p in raw_pvalues]
        bonf_corrected = [min(p, 1.0) for p in bonf_corrected]

        # Holm should be <= Bonferroni for all tests
        for holm_p, bonf_p in zip(holm_corrected, bonf_corrected):
            assert holm_p <= bonf_p, \
                "Holm-corrected p-values should be <= Bonferroni-corrected p-values"

    def test_holm_significance_threshold(self):
        """Test that significance decisions are correct at α=0.05."""
        np.random.seed(42)
        # Create groups with clear differences
        groups = {
            'lang_a': np.random.normal(5, 1, 100),
            'lang_b': np.random.normal(20, 1, 100),
            'lang_c': np.random.normal(5, 1, 100),
        }

        results = perform_pairwise_comparisons(groups)

        # At least one comparison should be significant
        significant_count = sum(1 for r in results if r['is_significant_holm'])
        assert significant_count >= 1, \
            "With clearly different groups, at least one comparison should be significant"

    def test_holm_with_identical_groups(self):
        """Test that identical groups produce non-significant results."""
        np.random.seed(42)
        data = np.random.normal(10, 2, 100)
        groups = {
            'lang_a': data.copy(),
            'lang_b': data.copy(),
            'lang_c': data.copy(),
        }

        results = perform_pairwise_comparisons(groups)

        # All corrected p-values should be high (non-significant)
        for r in results:
            assert r['holm_corrected_pvalue'] > 0.05, \
                "Identical groups should not be significant after correction"
            assert not r['is_significant_holm'], \
                "Identical groups should not be marked significant"

    def test_pairwise_comparison_structure(self):
        """Test that pairwise comparison results have correct structure."""
        np.random.seed(42)
        groups = {
            'lang_a': np.random.normal(10, 2, 50),
            'lang_b': np.random.normal(12, 2, 50),
        }

        results = perform_pairwise_comparisons(groups)

        assert len(results) == 1, "Should have 1 pairwise comparison for 2 groups"

        comp = results[0]
        required_fields = [
            'group1', 'group2', 'sample1_size', 'sample2_size',
            'u_statistic', 'raw_pvalue', 'holm_corrected_pvalue',
            'is_significant_holm'
        ]

        for field in required_fields:
            assert field in comp, f"Missing field: {field}"

    def test_kruskal_wallis_consistency(self):
        """Test that Kruskal-Wallis results are consistent with scipy."""
        np.random.seed(42)
        groups = {
            'lang_a': np.random.normal(10, 2, 100),
            'lang_b': np.random.normal(15, 2, 100),
            'lang_c': np.random.normal(10, 2, 100),
        }

        # Our implementation
        h_stat, p_val = perform_kruskal_wallis(groups)

        # Scipy implementation
        scipy_h, scipy_p = stats.kruskal(
            groups['lang_a'], groups['lang_b'], groups['lang_c']
        )

        assert np.isclose(h_stat, scipy_h, rtol=1e-5), \
            "H-statistic should match scipy"
        assert np.isclose(p_val, scipy_p, rtol=1e-5), \
            "p-value should match scipy"


class TestHypothesisPipeline:
    """Integration tests for the full hypothesis testing pipeline."""

    def test_analyze_hypotheses_output_structure(self, tmp_path):
        """Test that analyze_hypotheses produces correct output structure."""
        np.random.seed(42)
        # Create a minimal valid dataframe
        from analysis.hypothesis_testing import load_cleaned_data
        import pandas as pd

        # We'll test with synthetic data by mocking
        test_df = pd.DataFrame({
            'language': ['a'] * 50 + ['b'] * 50 + ['c'] * 50,
            'resolution_time_hours': np.concatenate([
                np.random.normal(10, 2, 50),
                np.random.normal(15, 2, 50),
                np.random.normal(10, 2, 50),
            ])
        })

        # Mock the load function
        import analysis.hypothesis_testing as ht_module
        original_load = ht_module.load_cleaned_data
        ht_module.load_cleaned_data = lambda: test_df

        try:
            results = analyze_hypotheses(test_df)

            # Check structure
            assert 'omnibus_test' in results
            assert 'pairwise_comparisons' in results
            assert 'westfall_young_permutation' in results
            assert 'metadata' in results

            # Check omnibus test fields
            assert 'h_statistic' in results['omnibus_test']
            assert 'p_value' in results['omnibus_test']
            assert 'is_significant' in results['omnibus_test']

            # Check pairwise fields
            assert 'comparisons' in results['pairwise_comparisons']
            assert 'n_comparisons' in results['pairwise_comparisons']

            # Check Westfall-Young fields
            assert 'westfall_young_pvalue' in results['westfall_young_permutation']
            assert 'n_permutations' in results['westfall_young_permutation']

        finally:
            ht_module.load_cleaned_data = original_load

    def test_minimum_groups_requirement(self):
        """Test that analysis fails with < 2 groups."""
        import pandas as pd
        import analysis.hypothesis_testing as ht_module

        test_df = pd.DataFrame({
            'language': ['a'] * 100,
            'resolution_time_hours': np.random.normal(10, 2, 100)
        })

        with pytest.raises(ValueError, match="Insufficient groups"):
            analyze_hypotheses(test_df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])