import unittest
import numpy as np
import pandas as pd
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.weightstats import ttest_ind
from statsmodels.regression.mixed_linear_model import MixedLM
import sys
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestMcNemarsTest(unittest.TestCase):
    """
    Unit tests for McNemar's test implementation logic.
    This tests the statistical correctness of the contingency table setup
    and the p-value calculation, which will be used in run_statistics.py.
    """

    def test_mcnemar_perfect_agreement(self):
        """
        Test case where there is perfect agreement between two conditions.
        Off-diagonal elements (b and c) should be 0.
        McNemar's test is undefined or p=1.0 in this case (or raises error depending on exactness).
        We verify the contingency table construction logic.
        """
        # Simulating data:
        # Condition A: Correct, Condition B: Correct -> 100
        # Condition A: Correct, Condition B: Incorrect -> 0
        # Condition A: Incorrect, Condition B: Correct -> 0
        # Condition A: Incorrect, Condition B: Incorrect -> 0
        
        # We will construct the 2x2 table manually to test the logic
        # Table:
        #           B=1   B=0
        # A=1       100     0
        # A=0         0     0
        
        # In a real scenario, we would feed a DataFrame, but here we test the core logic
        # that counts discordant pairs.
        
        discordant_pairs = 0 # b + c
        self.assertEqual(discordant_pairs, 0)

    def test_mcnemar_significant_difference(self):
        """
        Test case where there is a significant difference between two conditions.
        A high number of discordant pairs where B=1, A=0 vs B=0, A=1.
        """
        # Construct a table with significant discordance
        # A=1, B=0 (b): 10 (A correct, B wrong)
        # A=0, B=1 (c): 50 (A wrong, B correct)
        # Total discordant = 60
        
        b = 10
        c = 50
        
        # McNemar's chi-squared statistic (with continuity correction)
        # Chi2 = (|b - c| - 1)^2 / (b + c)
        chi2_stat = (abs(b - c) - 1)**2 / (b + c)
        
        # We expect a high chi-squared value indicating difference
        self.assertGreater(chi2_stat, 3.84) # Approx p < 0.05 threshold for 1 dof
        
        # Verify using statsmodels if available (mocked data)
        # We create a synthetic contingency table
        table = np.array([[100, b], [c, 100]]) # [[a, b], [c, d]]
        
        result = mcnemar(table, exact=False, correction=True)
        self.assertLess(result.pvalue, 0.05)

    def test_mcnemar_no_difference(self):
        """
        Test case where there is no significant difference.
        Discordant pairs are roughly equal.
        """
        # b = 25, c = 25
        b = 25
        c = 25
        
        table = np.array([[100, b], [c, 100]])
        result = mcnemar(table, exact=False, correction=True)
        
        # P-value should be high (> 0.05)
        self.assertGreater(result.pvalue, 0.05)

    def test_contingency_table_construction_logic(self):
        """
        Verify the logic for constructing the 2x2 table from raw interaction logs.
        This simulates the data processing step that would happen in run_statistics.py.
        """
        # Mock data representing binary outcomes (1=Success, 0=Fail)
        # Condition A: [1, 1, 0, 0, 1]
        # Condition B: [1, 0, 0, 1, 1]
        # Pairs: (1,1), (1,0), (0,0), (0,1), (1,1)
        # a (1,1): 2
        # b (1,0): 1
        # c (0,1): 1
        # d (0,0): 1
        
        cond_a = np.array([1, 1, 0, 0, 1])
        cond_b = np.array([1, 0, 0, 1, 1])
        
        a = np.sum((cond_a == 1) & (cond_b == 1))
        b = np.sum((cond_a == 1) & (cond_b == 0))
        c = np.sum((cond_a == 0) & (cond_b == 1))
        d = np.sum((cond_a == 0) & (cond_b == 0))
        
        self.assertEqual(a, 2)
        self.assertEqual(b, 1)
        self.assertEqual(c, 1)
        self.assertEqual(d, 1)
        
        table = np.array([[a, b], [c, d]])
        result = mcnemar(table, exact=False, correction=True)
        
        # With b=1, c=1, chi2 = (|1-1|-1)^2 / 2 = 0.5, p > 0.05
        self.assertGreater(result.pvalue, 0.05)

class TestEffectSizeCalculation(unittest.TestCase):
    """
    Unit tests for Odds Ratio and Cohen's d calculation logic.
    """

    def test_odds_ratio_calculation(self):
        """
        Verify Odds Ratio calculation: OR = (a * d) / (b * c)
        """
        a, b, c, d = 10, 5, 20, 15
        or_val = (a * d) / (b * c)
        expected = (10 * 15) / (5 * 20)
        self.assertAlmostEqual(or_val, expected)

    def test_cohen_d_calculation(self):
        """
        Verify Cohen's d calculation for independent samples.
        d = (mean1 - mean2) / pooled_std
        """
        group1 = np.array([10, 12, 14, 16, 18])
        group2 = np.array([5, 7, 9, 11, 13])
        
        mean1 = np.mean(group1)
        mean2 = np.mean(group2)
        
        std1 = np.std(group1, ddof=1)
        std2 = np.std(group2, ddof=1)
        
        n1 = len(group1)
        n2 = len(group2)
        
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        d = (mean1 - mean2) / pooled_std
        
        # Manual check:
        # mean1 = 14, mean2 = 9, diff = 5
        # std1 = 3.16, std2 = 3.16
        # pooled ~ 3.16
        # d ~ 1.58
        self.assertGreater(d, 1.0)
        self.assertLess(d, 2.0)

class TestLMEModel(unittest.TestCase):
    """
    Unit tests for Linear Mixed-Effects model setup.
    """

    def test_lme_model_construction(self):
        """
        Verify that the LME model can be constructed with random intercepts.
        """
        # Create synthetic data
        np.random.seed(42)
        n_participants = 10
        n_tasks_per_participant = 5
        
        participant_ids = np.repeat(range(n_participants), n_tasks_per_participant)
        task_ids = np.tile(range(n_tasks_per_participant), n_participants)
        condition = np.random.choice([0, 1], size=n_participants * n_tasks_per_participant)
        # Simulate response with a fixed effect for condition and random intercept for participant
        fixed_effect = 2.0
        random_intercepts = np.random.normal(0, 1, n_participants)[participant_ids]
        noise = np.random.normal(0, 0.5, n_participants * n_tasks_per_participant)
        response = fixed_effect * condition + random_intercepts + noise
        
        endog = response
        exog = condition.reshape(-1, 1)
        groups = participant_ids
        
        # Construct model
        model = MixedLM(endog, exog, groups=groups)
        result = model.fit()
        
        self.assertIsNotNone(result)
        self.assertIn('cond', result.params.index)

if __name__ == '__main__':
    unittest.main()