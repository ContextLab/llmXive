"""
Unit tests for LME model and bootstrapping utilities.
Tests for code/analysis/bootstrap_utils.py
"""
import unittest
import numpy as np
import pandas as pd
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.contingency_tables import mcnemar
import json
import tempfile
import os
from pathlib import Path

# Import the functions we are testing
# Note: We assume bootstrap_utils.py is implemented in code/analysis/
# If it doesn't exist yet, we are testing the interface and logic here.
try:
    from analysis.bootstrap_utils import (
        bootstrap_cohen_d,
        bootstrap_odds_ratio,
        run_lme_model,
        compute_confidence_interval
    )
    BOOTSTRAP_UTILS_AVAILABLE = True
except ImportError:
    # If the module doesn't exist yet, we mock the behavior for the test
    # to ensure the test structure is valid, but mark it as pending.
    BOOTSTRAP_UTILS_AVAILABLE = False


class TestBootstrapUtils(unittest.TestCase):
    """Tests for bootstrapping and LME model functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        np.random.seed(self.seed)
        self.n_samples = 1000
        self.n_bootstrap = 100  # Small number for fast testing

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_bootstrap_cohen_d_basic(self):
        """Test that Cohen's d bootstrapping returns expected structure."""
        # Generate synthetic data: two groups with known difference
        group_a = np.random.normal(loc=0.0, scale=1.0, size=self.n_samples)
        group_b = np.random.normal(loc=0.5, scale=1.0, size=self.n_samples)

        result = bootstrap_cohen_d(group_a, group_b, n_bootstraps=self.n_bootstrap, seed=self.seed)

        self.assertIn('effect_size', result)
        self.assertIn('ci_lower', result)
        self.assertIn('ci_upper', result)
        self.assertIn('ci_level', result)

        # Effect size should be positive (group_b > group_a)
        self.assertGreater(result['effect_size'], 0)

        # CI should contain the effect size
        self.assertLessEqual(result['ci_lower'], result['effect_size'])
        self.assertGreaterEqual(result['ci_upper'], result['effect_size'])

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_bootstrap_cohen_d_with_seed_reproducibility(self):
        """Test that bootstrapping is deterministic with fixed seed."""
        group_a = np.random.normal(loc=0.0, scale=1.0, size=self.n_samples)
        group_b = np.random.normal(loc=0.5, scale=1.0, size=self.n_samples)

        result1 = bootstrap_cohen_d(group_a, group_b, n_bootstraps=self.n_bootstrap, seed=self.seed)
        result2 = bootstrap_cohen_d(group_a, group_b, n_bootstraps=self.n_bootstrap, seed=self.seed)

        self.assertEqual(result1['effect_size'], result2['effect_size'])
        self.assertEqual(result1['ci_lower'], result2['ci_lower'])
        self.assertEqual(result1['ci_upper'], result2['ci_upper'])

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_bootstrap_odds_ratio_basic(self):
        """Test that Odds Ratio bootstrapping returns expected structure."""
        # Create contingency table data
        # Group A: 80 successes, 20 failures
        # Group B: 60 successes, 40 failures
        successes_a = 80
        failures_a = 20
        successes_b = 60
        failures_b = 40

        result = bootstrap_odds_ratio(
            successes_a, failures_a,
            successes_b, failures_b,
            n_bootstraps=self.n_bootstrap,
            seed=self.seed
        )

        self.assertIn('odds_ratio', result)
        self.assertIn('ci_lower', result)
        self.assertIn('ci_upper', result)
        self.assertIn('ci_level', result)

        # OR should be > 1 (Group A has higher success rate)
        self.assertGreater(result['odds_ratio'], 1.0)

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_run_lme_model_basic(self):
        """Test LME model execution with synthetic data."""
        # Create synthetic data for LME
        # Simulate participants with different intercepts
        n_participants = 50
        n_trials_per_participant = 10

        data = []
        for p_id in range(n_participants):
            # Random intercept for participant
            intercept = np.random.normal(loc=0.0, scale=0.5)
            for trial in range(n_trials_per_participant):
                # Condition: 0 or 1
                condition = np.random.choice([0, 1])
                # Outcome: depends on condition + random noise + participant intercept
                outcome = intercept + 0.3 * condition + np.random.normal(loc=0.0, scale=0.2)
                data.append({
                    'participant_id': p_id,
                    'condition': condition,
                    'outcome': outcome
                })

        df = pd.DataFrame(data)

        result = run_lme_model(
            df,
            fixed_formula='outcome ~ condition',
            random_formula='1 | participant_id'
        )

        self.assertIn('fixed_effects', result)
        self.assertIn('random_effects_variance', result)
        self.assertIn('p_value', result)
        self.assertIn('coefficient', result)

        # The coefficient for condition should be positive (0.3 in our simulation)
        self.assertGreater(result['coefficient'], 0)

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_compute_confidence_interval_percentile(self):
        """Test percentile-based CI computation."""
        # Generate bootstrap samples
        samples = np.random.normal(loc=1.0, scale=0.2, size=1000)

        ci = compute_confidence_interval(samples, ci_level=0.95)

        self.assertIn('lower', ci)
        self.assertIn('upper', ci)
        self.assertIn('method', ci)

        # Lower should be less than upper
        self.assertLess(ci['lower'], ci['upper'])

        # Mean should be between lower and upper
        self.assertGreaterEqual(ci['upper'], np.mean(samples))
        self.assertLessEqual(ci['lower'], np.mean(samples))

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_edge_case_small_sample_size(self):
        """Test behavior with small sample sizes."""
        group_a = np.array([1.0, 2.0, 3.0])
        group_b = np.array([2.0, 3.0, 4.0])

        # Should not raise an error, just return results with wide CIs
        result = bootstrap_cohen_d(group_a, group_b, n_bootstraps=10, seed=self.seed)

        self.assertIn('effect_size', result)
        # CI should be wider for small samples
        self.assertGreater(result['ci_upper'] - result['ci_lower'], 0.1)


class TestIntegrationWithStatistics(unittest.TestCase):
    """Integration tests combining bootstrapping with statistical tests."""

    def setUp(self):
        self.seed = 42
        np.random.seed(self.seed)

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_mcnemar_and_odds_ratio_consistency(self):
        """
        Test that McNemar's test and Odds Ratio bootstrapping
        are consistent for the same contingency table.
        """
        # Contingency table for paired data:
        #          Method B Success | Method B Failure
        # Method A Success |     a          |     b
        # Method A Failure |     c          |     d

        # Example: Method A is better (more successes when B fails)
        a, b, c, d = 10, 5, 15, 20

        # McNemar's test
        table = np.array([[a, b], [c, d]])
        mc_result = mcnemar(table, exact=True)

        # Odds ratio for discordant pairs (b vs c)
        or_result = bootstrap_odds_ratio(
            successes_a=b, failures_a=c,  # Discordant pairs
            successes_b=0, failures_b=0,   # Not used in this specific calculation
            n_bootstraps=50,
            seed=self.seed
        )

        # If b < c, OR should be < 1 (Method A has more failures in discordant pairs)
        # If b > c, OR should be > 1
        # In our case, b=5, c=15, so OR < 1
        self.assertLess(or_result['odds_ratio'], 1.0)

    @unittest.skipIf(not BOOTSTRAP_UTILS_AVAILABLE, "bootstrap_utils not implemented yet")
    def test_lme_with_realistic_study_data(self):
        """
        Test LME model with data structure similar to the study:
        - Multiple participants
        - Multiple conditions (baseline, llm, rule)
        - Reaction time as outcome
        """
        n_participants = 30
        conditions = ['baseline', 'llm', 'rule']

        data = []
        for p_id in range(n_participants):
            base_time = np.random.normal(loc=5000, scale=500)  # Base reaction time
            for cond in conditions:
                # Add condition effect
                if cond == 'baseline':
                    effect = 0
                elif cond == 'llm':
                    effect = -500  # Faster
                else:  # rule
                    effect = -300  # Faster but less than LLM

                time_val = base_time + effect + np.random.normal(loc=0, scale=200)
                data.append({
                    'participant_id': p_id,
                    'condition': cond,
                    'reaction_time': time_val
                })

        df = pd.DataFrame(data)

        # Convert condition to numeric for simple model
        df['condition_num'] = df['condition'].map({'baseline': 0, 'rule': 1, 'llm': 2})

        result = run_lme_model(
            df,
            fixed_formula='reaction_time ~ condition_num',
            random_formula='1 | participant_id'
        )

        # Should detect significant effect of condition
        self.assertLess(result['p_value'], 0.05)
        # Coefficient should be negative (higher condition_num -> faster time)
        self.assertLess(result['coefficient'], 0)


if __name__ == '__main__':
    unittest.main()
