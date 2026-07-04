import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm

# Import the function to be tested from the existing API surface
from robustness import run_alpha_sweep

class TestAlphaSweep:
    """
    Unit test for alpha sweep logic (0.01, 0.05, 0.10) in robustness.py.
    Verifies that the function correctly evaluates significance at multiple thresholds.
    """

    def setup_method(self):
        """Create mock data and model for testing."""
        # Create a small synthetic dataset for testing the logic
        # In real execution, this data would come from the imputed dataset
        np.random.seed(42)
        n = 100
        self.mock_data = pd.DataFrame({
            'IAT_D_score': np.random.normal(0, 1, n),
            'news_exposure_z': np.random.normal(0, 1, n),
            'political_ideology': np.random.normal(0, 1, n),
            'interaction': np.random.normal(0, 1, n)
        })
        
        # Create a mock OLS result object
        # We simulate the interaction term p-value being 0.045
        self.mock_model = MagicMock(spec=OLS)
        self.mock_results = MagicMock()
        
        # Simulate a results object where the interaction term has p=0.045
        # The p-values are typically accessed via pvalues dataframe
        p_values = pd.DataFrame({
            'IAT_D_score': [0.10],
            'news_exposure_z': [0.20],
            'political_ideology': [0.30],
            'interaction': [0.045]  # This is the key term
        }, index=['const', 'x1', 'x2', 'x3'])
        
        self.mock_results.pvalues = p_values
        self.mock_model.fit.return_value = self.mock_results

    @patch('statsmodels.api.OLS')
    def test_alpha_sweep_returns_correct_significance(self, mock_ols_class):
        """
        Test that run_alpha_sweep correctly identifies significance 
        at 0.01 (False), 0.05 (True), and 0.10 (True).
        """
        mock_ols_class.return_value = self.mock_model
        
        # Run the alpha sweep
        results = run_alpha_sweep(
            data=self.mock_data,
            outcome_var='IAT_D_score',
            predictor_vars=['news_exposure_z', 'political_ideology', 'interaction'],
            alpha_levels=[0.01, 0.05, 0.10]
        )
        
        # Verify the output structure
        assert isinstance(results, pd.DataFrame)
        assert 'alpha_level' in results.columns
        assert 'significant' in results.columns
        assert 'p_value' in results.columns
        
        # Check that all three alpha levels are present
        assert set(results['alpha_level'].tolist()) == {0.01, 0.05, 0.10}
        
        # Verify significance logic for the specific p-value (0.045)
        # For alpha=0.01: 0.045 > 0.01 -> False
        row_001 = results[results['alpha_level'] == 0.01].iloc[0]
        assert row_001['significant'] == False
        assert row_001['p_value'] == 0.045
        
        # For alpha=0.05: 0.045 <= 0.05 -> True
        row_005 = results[results['alpha_level'] == 0.05].iloc[0]
        assert row_005['significant'] == True
        assert row_005['p_value'] == 0.045
        
        # For alpha=0.10: 0.045 <= 0.10 -> True
        row_010 = results[results['alpha_level'] == 0.10].iloc[0]
        assert row_010['significant'] == True
        assert row_010['p_value'] == 0.045

    @patch('statsmodels.api.OLS')
    def test_alpha_sweep_handles_non_significant_p_value(self, mock_ols_class):
        """
        Test behavior when p-value is above all alpha levels (e.g., p=0.20).
        """
        # Modify mock to return p=0.20 for interaction
        p_values = pd.DataFrame({
            'IAT_D_score': [0.10],
            'news_exposure_z': [0.20],
            'political_ideology': [0.30],
            'interaction': [0.20]  # Non-significant
        }, index=['const', 'x1', 'x2', 'x3'])
        
        self.mock_results.pvalues = p_values
        mock_ols_class.return_value = self.mock_model
        
        results = run_alpha_sweep(
            data=self.mock_data,
            outcome_var='IAT_D_score',
            predictor_vars=['news_exposure_z', 'political_ideology', 'interaction'],
            alpha_levels=[0.01, 0.05, 0.10]
        )
        
        # All should be False
        assert all(results['significant'] == False)

    @patch('statsmodels.api.OLS')
    def test_alpha_sweep_handles_very_significant_p_value(self, mock_ols_class):
        """
        Test behavior when p-value is below all alpha levels (e.g., p=0.001).
        """
        # Modify mock to return p=0.001 for interaction
        p_values = pd.DataFrame({
            'IAT_D_score': [0.10],
            'news_exposure_z': [0.20],
            'political_ideology': [0.30],
            'interaction': [0.001]  # Very significant
        }, index=['const', 'x1', 'x2', 'x3'])
        
        self.mock_results.pvalues = p_values
        mock_ols_class.return_value = self.mock_model
        
        results = run_alpha_sweep(
            data=self.mock_data,
            outcome_var='IAT_D_score',
            predictor_vars=['news_exposure_z', 'political_ideology', 'interaction'],
            alpha_levels=[0.01, 0.05, 0.10]
        )
        
        # All should be True
        assert all(results['significant'] == True)

    def test_alpha_sweep_raises_on_missing_columns(self):
        """
        Test that the function raises ValueError if required columns are missing.
        """
        incomplete_data = pd.DataFrame({
            'IAT_D_score': [1, 2, 3],
            'news_exposure_z': [1, 2, 3]
            # Missing 'political_ideology' and 'interaction'
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            run_alpha_sweep(
                data=incomplete_data,
                outcome_var='IAT_D_score',
                predictor_vars=['news_exposure_z', 'political_ideology', 'interaction'],
                alpha_levels=[0.05]
            )

    def test_alpha_sweep_empty_alpha_levels(self):
        """
        Test that the function handles empty alpha_levels list gracefully 
        or raises a clear error.
        """
        with pytest.raises(ValueError, match="Alpha levels list cannot be empty"):
            run_alpha_sweep(
                data=self.mock_data,
                outcome_var='IAT_D_score',
                predictor_vars=['news_exposure_z', 'political_ideology', 'interaction'],
                alpha_levels=[]
            )