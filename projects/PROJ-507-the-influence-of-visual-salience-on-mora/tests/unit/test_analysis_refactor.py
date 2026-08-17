"""
Unit tests for the refactored analysis module (T039b).

Tests verify that model fitting and reporting are separated.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import functions to test
from analysis_models import fit_clmm, check_convergence
from analysis_posthoc import perform_ordinal_posthoc, calculate_effect_sizes
from analysis_power import run_power_analysis

class TestAnalysisRefactor(unittest.TestCase):

    def setUp(self):
        """Set up mock data."""
        self.mock_df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'scenario_id': ['S1', 'S1', 'S2', 'S2', 'S3'],
            'salience_level': ['low', 'high', 'low', 'high', 'medium'],
            'rating': [3, 5, 2, 4, 3]
        })

    @patch('analysis_models.mixedlm')
    def test_fit_clmm_returns_model(self, mock_mixedlm):
        """Test that fit_clmm returns a model object."""
        mock_model = MagicMock()
        mock_model.converged = True
        mock_model.params = {'salience_level[T.high]': 0.5}
        mock_mixedlm.return_value.fit.return_value = mock_model

        result = fit_clmm(self.mock_df)
        self.assertIsNotNone(result)
        self.assertTrue(result.converged)

    def test_check_convergence_true(self):
        """Test convergence check with a converged model."""
        mock_model = MagicMock()
        mock_model.converged = True
        self.assertTrue(check_convergence(mock_model))

    def test_check_convergence_false(self):
        """Test convergence check with a non-converged model."""
        mock_model = MagicMock()
        mock_model.converged = False
        self.assertFalse(check_convergence(mock_model))

    def test_posthoc_returns_list(self):
        """Test post-hoc returns a list of comparisons."""
        result = perform_ordinal_posthoc(self.mock_df, correction='bonferroni')
        self.assertIsInstance(result, list)

    def test_effect_sizes_calculation(self):
        """Test effect size calculation."""
        mock_results = {
            'coefficients': {'salience_level': 0.5},
            'std_errors': {'salience_level': 0.1}
        }
        result = calculate_effect_sizes(self.mock_df, mock_results)
        self.assertIn('salience_level', result)
        self.assertIn('odds_ratio', result['salience_level'])

    def test_power_analysis_returns_dict(self):
        """Test power analysis returns correct structure."""
        mock_results = {'coefficients': {}}
        result = run_power_analysis(self.mock_df, mock_results)
        self.assertIn('power', result)
        self.assertIn('power_adequate', result)

if __name__ == '__main__':
    unittest.main()