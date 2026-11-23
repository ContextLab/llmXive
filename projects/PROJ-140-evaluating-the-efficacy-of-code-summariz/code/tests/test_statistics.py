import unittest
import numpy as np
import pandas as pd
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.weightstats import ttest_ind
from statsmodels.regression.mixed_linear_model import MixedLM
import sys
import os
from pathlib import Path
from io import StringIO

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.run_statistics import (
    run_mcnemar_tests,
    run_lme_analysis,
    compute_effect_sizes,
    detect_outliers,
    run_sensitivity_analysis
)
from analysis.bootstrap_utils import bootstrap_cohen_d, bootstrap_odds_ratio
from analysis.correction_utils import holm_bonferroni_correction

class TestMcNemarsTest(unittest.TestCase):
    """Unit tests for McNemar's test implementation and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a synthetic interaction log DataFrame for testing
        self.test_data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T1', 'T2', 'T2', 'T2'],
            'condition': ['baseline', 'llm', 'rule', 'baseline', 'llm', 'rule'],
            'correct': [1, 1, 0, 1, 0, 1],  # 1 = correct, 0 = incorrect
            'time_ms': [5000, 3000, 4000, 6000, 2500, 4500]
        })

    def test_mcnemar_perfect_agreement(self):
        """Test McNemar's test when both conditions have perfect agreement."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T2', 'T2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'correct': [1, 1, 0, 0]
        })
        # Both conditions agree perfectly -> no discordant pairs
        # Expected: b=0, c=0 -> result should handle this edge case
        results = run_mcnemar_tests(data, 'baseline', 'llm')
        self.assertIn('baseline_vs_llm', results)
        # When b=c=0, the test is undefined; implementation should handle gracefully
        self.assertIsNotNone(results['baseline_vs_llm'])

    def test_mcnemar_zero_discordant_pairs(self):
        """Test McNemar's test when there are zero discordant pairs in one direction."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3'],
            'task_id': ['T1', 'T1', 'T2', 'T2', 'T3', 'T3'],
            'condition': ['baseline', 'llm', 'baseline', 'llm', 'baseline', 'llm'],
            'correct': [1, 1, 0, 1, 1, 1]  # baseline: 1,0,1; llm: 1,1,1
        })
        results = run_mcnemar_tests(data, 'baseline', 'llm')
        self.assertIn('baseline_vs_llm', results)
        # Should not raise an exception
        self.assertIsNotNone(results['baseline_vs_llm']['p_value'])

    def test_mcnemar_single_participant(self):
        """Test McNemar's test with only one participant."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1'],
            'task_id': ['T1', 'T1'],
            'condition': ['baseline', 'llm'],
            'correct': [1, 0]
        })
        results = run_mcnemar_tests(data, 'baseline', 'llm')
        self.assertIn('baseline_vs_llm', results)
        # With only one discordant pair, p-value should be 1.0 (exact test)
        self.assertIsNotNone(results['baseline_vs_llm']['p_value'])

    def test_mcnemar_all_zeros(self):
        """Test McNemar's test when all outcomes are zero."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T2', 'T2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'correct': [0, 0, 0, 0]
        })
        results = run_mcnemar_tests(data, 'baseline', 'llm')
        self.assertIn('baseline_vs_llm', results)
        # Should handle without crashing
        self.assertIsNotNone(results['baseline_vs_llm'])

    def test_mcnemar_large_sample(self):
        """Test McNemar's test with a larger sample size."""
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'participant_id': [f'P{i}' for i in range(n)],
            'task_id': [f'T{i}' for i in range(n)],
            'condition': ['baseline'] * n + ['llm'] * n,
            'correct': np.concatenate([
                np.random.binomial(1, 0.7, n),
                np.random.binomial(1, 0.8, n)
            ])
        })
        results = run_mcnemar_tests(data, 'baseline', 'llm')
        self.assertIn('baseline_vs_llm', results)
        self.assertIn('p_value', results['baseline_vs_llm'])
        self.assertIsInstance(results['baseline_vs_llm']['p_value'], float)

    def test_mcnemar_missing_condition(self):
        """Test McNemar's test when one condition is missing from data."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T2', 'T2'],
            'condition': ['baseline', 'baseline', 'baseline', 'baseline'],
            'correct': [1, 0, 1, 1]
        })
        with self.assertRaises(ValueError):
            run_mcnemar_tests(data, 'baseline', 'llm')

    def test_mcnemar_empty_dataframe(self):
        """Test McNemar's test with an empty DataFrame."""
        data = pd.DataFrame(columns=['participant_id', 'task_id', 'condition', 'correct'])
        with self.assertRaises(ValueError):
            run_mcnemar_tests(data, 'baseline', 'llm')

    def test_mcnemar_invalid_correct_values(self):
        """Test McNemar's test with invalid values in 'correct' column."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T2', 'T2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'correct': [1, 2, 0, 1]  # 2 is invalid
        })
        # Should either raise or handle gracefully; checking it doesn't crash unexpectedly
        try:
            results = run_mcnemar_tests(data, 'baseline', 'llm')
            # If it doesn't raise, it should handle the invalid value
            self.assertIsNotNone(results)
        except (ValueError, TypeError):
            # Expected behavior if validation is strict
            pass


class TestEffectSizeCalculation(unittest.TestCase):
    """Unit tests for effect size calculation and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
            'task_id': ['T1', 'T1', 'T1', 'T2', 'T2', 'T2'],
            'condition': ['baseline', 'llm', 'rule', 'baseline', 'llm', 'rule'],
            'correct': [1, 1, 0, 1, 0, 1],
            'time_ms': [5000, 3000, 4000, 6000, 2500, 4500]
        })

    def test_cohen_d_perfect_separation(self):
        """Test Cohen's d when groups are perfectly separated."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([10.0, 11.0, 12.0])
        # Should compute a large effect size
        result = ttest_ind(group1, group2)
        self.assertGreater(result.effectsize, 5.0)

    def test_cohen_d_identical_groups(self):
        """Test Cohen's d when groups are identical."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([1.0, 2.0, 3.0])
        result = ttest_ind(group1, group2)
        self.assertAlmostEqual(result.effectsize, 0.0, places=5)

    def test_cohen_d_single_value(self):
        """Test Cohen's d with a single value in one group."""
        group1 = np.array([1.0])
        group2 = np.array([2.0, 3.0, 4.0])
        # Should handle without crashing
        try:
            result = ttest_ind(group1, group2)
            # effectsize might be NaN or Inf depending on implementation
            self.assertTrue(np.isfinite(result.effectsize) or np.isnan(result.effectsize))
        except Exception:
            # Expected if standard deviation is zero
            pass

    def test_cohen_d_very_small_variance(self):
        """Test Cohen's d with very small variance."""
        group1 = np.array([1.0, 1.0000001, 1.0000002])
        group2 = np.array([2.0, 2.0000001, 2.0000002])
        result = ttest_ind(group1, group2)
        # Should compute without crashing
        self.assertIsNotNone(result.effectsize)

    def test_odds_ratio_zero_cell(self):
        """Test Odds Ratio calculation when one cell is zero."""
        # contingency table: [[a, b], [c, d]]
        table = np.array([[10, 0], [5, 8]])
        # Odds ratio should handle zero cell (possibly with continuity correction)
        result = bootstrap_odds_ratio(table, n_resamples=100, seed=42)
        self.assertIsNotNone(result)
        self.assertIn('odds_ratio', result)
        self.assertIn('ci_lower', result)
        self.assertIn('ci_upper', result)

    def test_odds_ratio_all_zeros(self):
        """Test Odds Ratio when all cells are zero."""
        table = np.array([[0, 0], [0, 0]])
        # Should handle gracefully
        result = bootstrap_odds_ratio(table, n_resamples=100, seed=42)
        self.assertIsNotNone(result)

    def test_bootstrap_with_small_sample(self):
        """Test bootstrap functions with very small sample size."""
        table = np.array([[5, 3], [2, 4]])
        result = bootstrap_odds_ratio(table, n_resamples=10, seed=42)
        self.assertIsNotNone(result)
        self.assertIn('odds_ratio', result)

    def test_effect_sizes_computation(self):
        """Test the compute_effect_sizes function with real data."""
        results = compute_effect_sizes(self.test_data)
        self.assertIsInstance(results, dict)
        self.assertIn('accuracy', results)
        self.assertIn('speed', results)
        # Check that effect sizes are computed for comparisons
        for comparison in ['baseline_vs_llm', 'baseline_vs_rule']:
            if comparison in results['accuracy']:
                self.assertIn('odds_ratio', results['accuracy'][comparison])
                self.assertIn('ci_lower', results['accuracy'][comparison])
                self.assertIn('ci_upper', results['accuracy'][comparison])


class TestLMEModel(unittest.TestCase):
    """Unit tests for Linear Mixed-Effects model and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2', 'P3', 'P3', 'P3'],
            'task_id': ['T1', 'T1', 'T1', 'T2', 'T2', 'T2', 'T3', 'T3', 'T3'],
            'condition': ['baseline', 'llm', 'rule', 'baseline', 'llm', 'rule', 'baseline', 'llm', 'rule'],
            'time_ms': [5000, 3000, 4000, 6000, 2500, 4500, 5500, 2800, 4200]
        })

    def test_lme_single_group(self):
        """Test LME model when all data belongs to one group."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'condition': ['baseline', 'baseline', 'baseline', 'baseline'],
            'time_ms': [5000, 5100, 5200, 5300]
        })
        # LME requires variation in the fixed effect; should handle gracefully
        try:
            result = run_lme_analysis(data, 'time_ms', 'condition', 'participant_id')
            self.assertIsNotNone(result)
        except Exception:
            # Expected if model cannot converge with no fixed effect variation
            pass

    def test_lme_single_participant(self):
        """Test LME model with only one participant."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1'],
            'condition': ['baseline', 'llm', 'rule'],
            'time_ms': [5000, 3000, 4000]
        })
        # LME requires multiple participants for random effects
        try:
            result = run_lme_analysis(data, 'time_ms', 'condition', 'participant_id')
            # Should handle or warn
            self.assertIsNotNone(result)
        except Exception:
            # Expected if model cannot estimate random effects
            pass

    def test_lme_very_small_variance(self):
        """Test LME model with very small variance in outcome."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'time_ms': [5000.0, 5000.0001, 5000.0002, 5000.0003]
        })
        try:
            result = run_lme_analysis(data, 'time_ms', 'condition', 'participant_id')
            self.assertIsNotNone(result)
        except Exception:
            # Expected if model cannot converge
            pass

    def test_lme_missing_random_effect_levels(self):
        """Test LME when some participants have only one observation."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P2'],
            'condition': ['baseline', 'llm', 'rule'],
            'time_ms': [5000, 3000, 4000]
        })
        try:
            result = run_lme_analysis(data, 'time_ms', 'condition', 'participant_id')
            self.assertIsNotNone(result)
        except Exception:
            # Expected if model cannot estimate random effects
            pass

    def test_lme_normal_case(self):
        """Test LME model with normal, well-formed data."""
        np.random.seed(42)
        n_participants = 20
        n_tasks = 3
        data = pd.DataFrame({
            'participant_id': [f'P{i}' for i in range(n_participants) for _ in range(n_tasks)],
            'condition': ['baseline', 'llm', 'rule'] * n_participants,
            'time_ms': np.random.normal(4000, 500, n_participants * n_tasks)
        })
        result = run_lme_analysis(data, 'time_ms', 'condition', 'participant_id')
        self.assertIsNotNone(result)
        self.assertIn('fixed_effects', result)
        self.assertIn('random_effects_variance', result)


class TestOutlierDetection(unittest.TestCase):
    """Unit tests for outlier detection edge cases."""

    def test_detect_outliers_empty_data(self):
        """Test outlier detection with empty DataFrame."""
        data = pd.DataFrame(columns=['participant_id', 'time_ms'])
        result = detect_outliers(data, 'time_ms')
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_detect_outliers_single_value(self):
        """Test outlier detection with a single value."""
        data = pd.DataFrame({'time_ms': [5000.0]})
        result = detect_outliers(data, 'time_ms')
        self.assertIsInstance(result, list)
        # No outliers possible with single value
        self.assertEqual(len(result), 0)

    def test_detect_outliers_all_identical(self):
        """Test outlier detection when all values are identical."""
        data = pd.DataFrame({'time_ms': [5000.0, 5000.0, 5000.0]})
        result = detect_outliers(data, 'time_ms')
        self.assertIsInstance(result, list)
        # No outliers if all values are the same
        self.assertEqual(len(result), 0)

    def test_detect_outliers_normal_case(self):
        """Test outlier detection with normal data including one outlier."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'time_ms': [4000, 4100, 3900, 4050, 15000]  # 15000 is an outlier
        })
        result = detect_outliers(data, 'time_ms')
        self.assertIsInstance(result, list)
        # Should identify the outlier
        self.assertGreater(len(result), 0)
        self.assertIn('P5', result)

    def test_detect_outliers_with_nan(self):
        """Test outlier detection with NaN values."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'time_ms': [4000.0, np.nan, 4100.0]
        })
        # Should handle NaN without crashing
        result = detect_outliers(data, 'time_ms')
        self.assertIsInstance(result, list)


class TestSensitivityAnalysis(unittest.TestCase):
    """Unit tests for sensitivity analysis edge cases."""

    def test_sensitivity_empty_config(self):
        """Test sensitivity analysis with empty config."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1'],
            'condition': ['baseline', 'llm'],
            'correct': [1, 0]
        })
        # Should handle empty config gracefully
        result = run_sensitivity_analysis(data, 'baseline', 'llm', 'correct', [])
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    def test_sensitivity_single_cutoff(self):
        """Test sensitivity analysis with a single cutoff value."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'correct': [1, 1, 0, 1]
        })
        result = run_sensitivity_analysis(data, 'baseline', 'llm', 'correct', [0.05])
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    def test_sensitivity_duplicate_cutoffs(self):
        """Test sensitivity analysis with duplicate cutoff values."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'condition': ['baseline', 'llm', 'baseline', 'llm'],
            'correct': [1, 1, 0, 1]
        })
        result = run_sensitivity_analysis(data, 'baseline', 'llm', 'correct', [0.05, 0.05, 0.10])
        self.assertIsInstance(result, pd.DataFrame)
        # Should handle duplicates (either deduplicate or process multiple times)
        self.assertGreater(len(result), 0)

    def test_sensitivity_invalid_cutoffs(self):
        """Test sensitivity analysis with invalid cutoff values."""
        data = pd.DataFrame({
            'participant_id': ['P1', 'P1'],
            'condition': ['baseline', 'llm'],
            'correct': [1, 0]
        })
        # Negative or >1 cutoffs should be handled
        result = run_sensitivity_analysis(data, 'baseline', 'llm', 'correct', [-0.1, 0.05, 1.5])
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()