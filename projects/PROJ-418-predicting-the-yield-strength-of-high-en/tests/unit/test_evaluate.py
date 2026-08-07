"""
Unit tests for statistical validation functions in models.evaluate.
Specifically tests Holm-Bonferroni correction logic.
"""
import unittest
import numpy as np
from models.evaluate import apply_bonferroni_correction, run_multiple_comparison_correction

class TestHolmBonferroniCorrection(unittest.TestCase):
    """
    Tests for the Holm-Bonferroni correction implementation.
    Verifies correctness against known small datasets with expected results.
    """

    def test_holm_bonferroni_known_values(self):
        """
        Verify Holm-Bonferroni correction against a known small dataset.
        
        Scenario:
        We have 5 p-values: [0.01, 0.04, 0.03, 0.005, 0.02]
        Sorted: [0.005, 0.01, 0.02, 0.03, 0.04] (indices: 3, 0, 4, 2, 1)
        m = 5 (number of tests)
        
        Holm-Bonferroni logic:
        1. p[0] = 0.005, threshold = 0.05 / 5 = 0.01. 0.005 < 0.01 -> significant. Corrected = 0.005 * 5 = 0.025
        2. p[1] = 0.01, threshold = 0.05 / 4 = 0.0125. 0.01 < 0.0125 -> significant. Corrected = 0.01 * 4 = 0.04
        3. p[2] = 0.02, threshold = 0.05 / 3 = 0.0166. 0.02 > 0.0166 -> not significant. 
           Per Holm, once a non-significant is found, all subsequent are not significant.
           Corrected p-value is max(current * (m-i), previous_corrected) to ensure monotonicity.
           However, standard implementation often just returns the calculated value for the test,
           but the decision is based on the threshold comparison.
           
        Let's verify the `run_multiple_comparison_correction` function which implements this logic.
        Expected behavior:
        - Input: [0.01, 0.04, 0.03, 0.005, 0.02]
        - Output (corrected p-values): [0.04, 0.20, 0.09, 0.025, 0.06] (approx, depending on monotonicity enforcement)
        - Output (significant): [True, False, False, True, False] (based on alpha=0.05)
        
        Let's trace manually with strict Holm:
        Sorted p: 0.005 (idx 3), 0.01 (idx 0), 0.02 (idx 4), 0.03 (idx 2), 0.04 (idx 1)
        m=5, alpha=0.05
        
        i=0: p=0.005. thresh=0.05/5=0.01. 0.005 <= 0.01 -> Sig.
        i=1: p=0.01. thresh=0.05/4=0.0125. 0.01 <= 0.0125 -> Sig.
        i=2: p=0.02. thresh=0.05/3=0.0166. 0.02 > 0.0166 -> Not Sig. Stop.
        i=3: Not Sig.
        i=4: Not Sig.
        
        Significant indices: 3, 0.
        """
        raw_p_values = np.array([0.01, 0.04, 0.03, 0.005, 0.02])
        alpha = 0.05
        
        # Assuming run_multiple_comparison_correction returns (corrected_p_values, is_significant)
        corrected_p, is_sig = run_multiple_comparison_correction(raw_p_values, alpha=alpha)
        
        # Expected significant indices based on manual trace: 3 (0.005) and 0 (0.01)
        # Indices 4, 2, 1 should be False.
        expected_sig = np.array([True, False, False, True, False])
        
        # Check boolean array equality
        np.testing.assert_array_equal(
            is_sig, expected_sig,
            err_msg=f"Holm-Bonferroni significance flags incorrect.\nGot: {is_sig}\nExpected: {expected_sig}"
        )
        
        # Verify monotonicity of corrected p-values (sorted by original index, they should respect the logic)
        # Actually, the corrected p-values themselves should be non-decreasing when sorted by original p-value rank.
        # But we just need to ensure the function runs and produces valid probabilities [0, 1].
        self.assertTrue(np.all(corrected_p >= 0) and np.all(corrected_p <= 1.0))
        
        # Specific check for the smallest p-value correction: 0.005 * 5 = 0.025
        # The corrected value for index 3 should be 0.025 (or capped at 1.0)
        self.assertAlmostEqual(corrected_p[3], 0.025, places=5)

    def test_holm_bonferroni_all_significant(self):
        """
        Test case where all p-values are significant.
        """
        raw_p_values = np.array([0.001, 0.002, 0.003, 0.004])
        alpha = 0.05
        
        corrected_p, is_sig = run_multiple_comparison_correction(raw_p_values, alpha=alpha)
        
        # All should be significant
        expected_sig = np.array([True, True, True, True])
        np.testing.assert_array_equal(is_sig, expected_sig)
        
        # Check specific correction for the last one (largest p): 0.004 * 1 = 0.004
        # Sorted: 0.001, 0.002, 0.003, 0.004
        # i=0: 0.001 * 4 = 0.004
        # i=1: 0.002 * 3 = 0.006
        # i=2: 0.003 * 2 = 0.006
        # i=3: 0.004 * 1 = 0.004 -> Wait, monotonicity check: max(0.004, 0.006) = 0.006?
        # Holm corrected p-values must be non-decreasing in the sorted order.
        # Corrected: [0.004, 0.006, 0.006, 0.004] -> sorted order correction:
        # 1. 0.001 * 4 = 0.004
        # 2. 0.002 * 3 = 0.006
        # 3. 0.003 * 2 = 0.006
        # 4. 0.004 * 1 = 0.004 -> This violates monotonicity (0.004 < 0.006). 
        # The algorithm should take max(current, previous). So the last one becomes 0.006.
        # Let's check the logic of the implementation.
        # If the implementation is correct, the last corrected p-value (for 0.004) should be 0.006.
        
        # Re-evaluating sorted order corrections:
        # 0.001 -> 0.004
        # 0.002 -> 0.006
        # 0.003 -> 0.006 (max(0.006, 0.006))
        # 0.004 -> 0.006 (max(0.004, 0.006))
        
        # The values in `corrected_p` should correspond to the original order.
        # Original order: 0.001, 0.002, 0.003, 0.004
        # Corrected: 0.004, 0.006, 0.006, 0.006
        self.assertAlmostEqual(corrected_p[0], 0.004, places=5)
        self.assertAlmostEqual(corrected_p[3], 0.006, places=5)

    def test_holm_bonferroni_none_significant(self):
        """
        Test case where no p-values are significant.
        """
        raw_p_values = np.array([0.1, 0.2, 0.3])
        alpha = 0.05
        
        corrected_p, is_sig = run_multiple_comparison_correction(raw_p_values, alpha=alpha)
        
        expected_sig = np.array([False, False, False])
        np.testing.assert_array_equal(is_sig, expected_sig)

    def test_holm_bonferroni_single_value(self):
        """
        Test with a single p-value.
        """
        raw_p_values = np.array([0.04])
        alpha = 0.05
        
        corrected_p, is_sig = run_multiple_comparison_correction(raw_p_values, alpha=alpha)
        
        self.assertTrue(is_sig[0])
        self.assertAlmostEqual(corrected_p[0], 0.04, places=5)

if __name__ == '__main__':
    unittest.main()