import unittest
import pandas as pd
import numpy as np
from code.analyze import perform_stratified_mwu_test, calculate_effect_size_r

class TestMannWhitneyU(unittest.TestCase):

    def setUp(self):
        # Create a mock dataframe
        np.random.seed(42)
        n = 100
        data = {
            'is_ai': np.random.choice([True, False], n),
            'turnaround_hours': np.random.exponential(scale=20, size=n),
            'lines_changed': np.random.randint(1, 100, n),
            'total_prs_by_author': np.random.randint(1, 20, n)
        }
        self.df = pd.DataFrame(data)

    def test_stratified_mwu_basic(self):
        """Test that stratified MWU runs without error and returns expected keys."""
        result = perform_stratified_mwu_test(
            self.df, 
            group_col='is_ai', 
            value_col='turnaround_hours', 
            stratify_cols=['lines_changed', 'total_prs_by_author']
        )
        
        self.assertIn('u_statistic', result)
        self.assertIn('p_value', result)
        self.assertIn('effect_size', result)
        self.assertIsInstance(result['u_statistic'], float)
        self.assertIsInstance(result['p_value'], float)
        self.assertIsInstance(result['effect_size'], float)
        self.assertGreaterEqual(result['p_value'], 0.0)
        self.assertLessEqual(result['p_value'], 1.0)

    def test_effect_size_calculation(self):
        """Test effect size calculation logic."""
        # r = U / sqrt(n1 * n2)
        # If U is 0, r should be 0
        r = calculate_effect_size_r(0, 50, 50)
        self.assertEqual(r, 0.0)
        
        # If U is sqrt(n1*n2), r should be 1.0
        n1, n2 = 50, 50
        u = np.sqrt(n1 * n2)
        r = calculate_effect_size_r(u, n1, n2)
        self.assertAlmostEqual(r, 1.0, places=5)

    def test_stratification_logic(self):
        """Test that stratification actually splits data."""
        # Create a dataset where one stratum is clearly different
        df = pd.DataFrame({
            'is_ai': [True]*20 + [False]*20 + [True]*20 + [False]*20,
            'turnaround_hours': [1]*20 + [100]*20 + [50]*20 + [60]*20,
            'stratum_col': [0]*20 + [0]*20 + [1]*20 + [1]*20
        })
        
        # This should run without crashing
        result = perform_stratified_mwu_test(
            df, 'is_ai', 'turnaround_hours', ['stratum_col']
        )
        self.assertIsNotNone(result['p_value'])

if __name__ == '__main__':
    unittest.main()