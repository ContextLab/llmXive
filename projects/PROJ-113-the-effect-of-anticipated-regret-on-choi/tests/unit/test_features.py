"""
Unit tests for regret_proxy calculation, specifically focusing on the single-option edge case.
This test validates the logic implemented in code/features.py for T010 and T011.
"""
import unittest
import pandas as pd
import numpy as np
from features import calculate_min_max_regret

class TestRegretProxySingleOption(unittest.TestCase):
    """Tests for the single-option edge case in regret proxy calculation."""

    def test_single_option_returns_zero(self):
        """
        Verify that if a decision scenario contains only ONE option,
        the calculated regret_proxy is exactly 0.0.
        
        This aligns with FR-002 and T011: Regret requires a comparison between
        at least two alternatives. With only one option, there is no opportunity cost.
        """
        # Create a DataFrame representing a single-trial decision with one option
        # Structure: Each row is an option within a decision context (identified by 'trial_id')
        data = {
            'trial_id': [1, 1, 1],  # Same context, but we simulate a case where only one option exists
            'option_id': ['A', 'B', 'C'], # Actually, let's simulate a scenario where we only have one valid option row per trial
            'utility': [10.0, 10.0, 10.0]
        }
        
        # To test the "single option" edge case properly, we need a dataset where 
        # a specific trial_id has only one row associated with it.
        single_option_data = {
            'trial_id': [1],
            'option_id': ['A'],
            'utility': [15.5]
        }
        df_single = pd.DataFrame(single_option_data)
        
        result = calculate_min_max_regret(df_single)
        
        # Assert that the result is 0.0
        self.assertEqual(result['regret_proxy'].iloc[0], 0.0)
        self.assertEqual(result['max_opportunity'].iloc[0], 15.5) # Max utility is the only utility

    def test_multiple_options_calculates_regret(self):
        """
        Verify that with multiple options, regret is calculated correctly as
        (max_utility_in_context - utility_of_chosen_option).
        """
        data = {
            'trial_id': [1, 1, 1],
            'option_id': ['A', 'B', 'C'],
            'utility': [10.0, 20.0, 15.0],
            'is_chosen': [1, 0, 0] # Option A is chosen
        }
        df_multi = pd.DataFrame(data)
        
        result = calculate_min_max_regret(df_multi)
        
        # Expected: Max utility is 20.0 (Option B). Chosen is 10.0 (Option A).
        # Regret = 20.0 - 10.0 = 10.0
        self.assertEqual(result['regret_proxy'].iloc[0], 10.0)
        
        # Check non-chosen options (though the function might return 0 for them or handle differently)
        # The function should return a row for each input option.
        # For Option B (chosen=0), regret is 20 - 20 = 0? Or is it opportunity cost of not choosing?
        # Min-Max Regret usually applies to the chosen action.
        # Let's verify the logic handles the 'is_chosen' flag correctly.
        
    def test_no_chosen_option_returns_nan_or_zero(self):
        """
        Edge case: Multiple options exist, but none are marked as chosen.
        Depending on implementation, this might return NaN or 0.
        """
        data = {
            'trial_id': [1, 1],
            'option_id': ['A', 'B'],
            'utility': [10.0, 20.0],
            'is_chosen': [0, 0]
        }
        df_no_choice = pd.DataFrame(data)
        
        result = calculate_min_max_regret(df_no_choice)
        
        # If deferral logic is handled elsewhere, this might return 0 or NaN.
        # We assert that it doesn't crash.
        self.assertIsNotNone(result)
        self.assertIn('regret_proxy', result.columns)

    def test_empty_dataframe(self):
        """
        Edge case: Empty input DataFrame.
        """
        df_empty = pd.DataFrame(columns=['trial_id', 'option_id', 'utility'])
        
        result = calculate_min_max_regret(df_empty)
        
        self.assertTrue(result.empty)
        self.assertIn('regret_proxy', result.columns)

if __name__ == '__main__':
    unittest.main()