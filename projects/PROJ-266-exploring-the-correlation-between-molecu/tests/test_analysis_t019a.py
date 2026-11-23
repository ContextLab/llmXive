import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports
# Assuming tests are run from the root or the project structure is set up
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.analysis import fit_multivariate_model, load_analysis_data

class TestT019aMultivariateModel:
    """
    Tests for T019a: Multivariate Linear Regression implementation.
    """

    def test_fit_multivariate_model_structure(self, tmp_path):
        """
        Verifies that the model fits correctly and returns the expected structure.
        Uses a small synthetic dataframe to ensure the logic works without full data.
        """
        # Create a mock dataframe that mimics the expected schema
        data = {
            'smiles': ['CCO', 'CCCO', 'CCCCO', 'CCCCCO', 'CCCCCCO'],
            'dihedral_variance': [0.1, 0.2, 0.3, 0.4, 0.5],
            'logP': [0.5, 1.0, 1.5, 2.0, 2.5],
            'mw': [46.0, 60.0, 74.0, 88.0, 102.0],
            'psa': [20.0, 20.0, 20.0, 20.0, 20.0],
            'logPapp': [5.0, 4.5, 4.0, 3.5, 3.0] # Synthetic target
        }
        df = pd.DataFrame(data)

        # Run the model
        results = fit_multivariate_model(df)

        # Verify structure
        assert isinstance(results, dict)
        assert results['model_type'] == "Multivariate Linear Regression"
        assert 'coefficients' in results
        assert 'metrics' in results
        assert 'r_squared' in results['metrics']
        assert 'rmse' in results['metrics']
        assert 'mae' in results['metrics']
        
        # Verify predictors
        expected_predictors = ['dihedral_variance', 'logP', 'mw', 'psa']
        assert results['predictors'] == expected_predictors

    def test_model_metrics_reasonableness(self, tmp_path):
        """
        Checks that the metrics are reasonable (R2 between 0 and 1 for a perfect synthetic line).
        """
        # Create a perfectly linear synthetic dataset
        # y = 10 - 2*x (where x is dihedral_variance)
        n = 20
        x = np.linspace(0.1, 1.0, n)
        df_data = {
            'smiles': ['CCO'] * n,
            'dihedral_variance': x,
            'logP': [0.5] * n,
            'mw': [46.0] * n,
            'psa': [20.0] * n,
            'logPapp': 10 - 2 * x # Perfect linear relationship
        }
        df = pd.DataFrame(df_data)

        results = fit_multivariate_model(df)
        
        # R2 should be very close to 1.0
        assert results['metrics']['r_squared'] > 0.99
        assert results['metrics']['rmse'] < 0.01
        assert results['metrics']['mae'] < 0.01

    def test_missing_feature_handling(self):
        """
        Verifies that the function raises an error if required features are missing.
        """
        df_missing = pd.DataFrame({
            'smiles': ['CCO'],
            'dihedral_variance': [0.1],
            # Missing 'logP', 'mw', 'psa'
            'logPapp': [5.0]
        })
        
        with pytest.raises(ValueError, match="Missing required feature columns"):
            fit_multivariate_model(df_missing)