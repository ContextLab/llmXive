import os
import sys
import unittest
import tempfile
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from metrics.tost_equivalence import perform_tost_test, run_tost_equivalence_tests, TOST_DELTA

class TestTOSTEquivalence(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock data for TOST
        # Scenario 1: Equivalent groups (means very close)
        self.equivalent_baseline = np.random.normal(loc=10.0, scale=0.5, size=100)
        self.equivalent_hybrid = np.random.normal(loc=10.1, scale=0.5, size=100)
        
        # Scenario 2: Non-equivalent groups (means far apart)
        self.non_equivalent_baseline = np.random.normal(loc=10.0, scale=0.5, size=100)
        self.non_equivalent_hybrid = np.random.normal(loc=15.0, scale=0.5, size=100)

    def test_perform_tost_equivalent_groups(self):
        """Test that TOST returns True for statistically equivalent groups."""
        results = perform_tost_test(
            self.equivalent_baseline.tolist(),
            self.equivalent_hybrid.tolist(),
            delta=TOST_DELTA,
            alpha=0.05
        )
        self.assertTrue(results['is_equivalent'])
        self.assertLess(results['p_value_lower'], 0.05)
        self.assertLess(results['p_value_upper'], 0.05)

    def test_perform_tost_non_equivalent_groups(self):
        """Test that TOST returns False for statistically different groups."""
        results = perform_tost_test(
            self.non_equivalent_baseline.tolist(),
            self.non_equivalent_hybrid.tolist(),
            delta=TOST_DELTA,
            alpha=0.05
        )
        self.assertFalse(results['is_equivalent'])
        # At least one p-value should be >= 0.05

    def test_run_tost_on_dataframe(self):
        """Test running TOST on a DataFrame with skip flags."""
        df = pd.DataFrame({
            'fid_score': list(self.equivalent_baseline) + list(self.equivalent_hybrid),
            'skip_flag': [False] * len(self.equivalent_baseline) + [True] * len(self.equivalent_hybrid)
        })
        
        results = run_tost_equivalence_tests(df)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['is_equivalent'])
        self.assertEqual(results[0]['metric'], 'fid_score')

    def test_insufficient_samples(self):
        """Test that TOST raises error with insufficient samples."""
        with self.assertRaises(ValueError):
            perform_tost_test([1.0], [1.0], delta=0.05)

    def test_empty_group(self):
        """Test that TOST raises error with empty group."""
        with self.assertRaises(ValueError):
            perform_tost_test([], [1.0, 2.0], delta=0.05)

if __name__ == '__main__':
    unittest.main()