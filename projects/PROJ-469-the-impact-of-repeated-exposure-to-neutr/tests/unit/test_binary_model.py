"""
Unit tests for the Binary Model Fit (T024b).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from binary_model import fit_binary_model, save_binary_model_results
from preprocessing import derive_variables

class TestFitBinaryModel:
    def test_fit_binary_model_basic(self):
        """Test that the function runs and returns expected keys."""
        # Create synthetic data for testing (only for unit test validation of logic)
        np.random.seed(42)
        n = 100
        data = {
            'IAT_D_score': np.random.normal(0, 1, n),
            'news_exposure_z': np.random.normal(0, 1, n),
            'ideology_binary': np.random.choice([0, 1], n)
        }
        df = pd.DataFrame(data)
        
        results = fit_binary_model(df)
        
        assert isinstance(results, dict)
        assert 'interaction_coef' in results
        assert 'interaction_pvalue' in results
        assert 'model_type' in results
        assert results['model_type'] == 'binary_ideology_ols'
        assert 'n_obs' in results
        assert results['n_obs'] == n

    def test_fit_binary_model_missing_columns(self):
        """Test that ValueError is raised if required columns are missing."""
        df = pd.DataFrame({'IAT_D_score': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            fit_binary_model(df)

    def test_fit_binary_model_insufficient_data(self):
        """Test that ValueError is raised if too few data points remain."""
        df = pd.DataFrame({
            'IAT_D_score': [1.0],
            'news_exposure_z': [1.0],
            'ideology_binary': [1.0]
        })
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            fit_binary_model(df)

    def test_fit_binary_model_nan_handling(self):
        """Test that rows with NaNs are dropped correctly."""
        np.random.seed(42)
        n = 50
        data = {
            'IAT_D_score': np.random.normal(0, 1, n),
            'news_exposure_z': np.random.normal(0, 1, n),
            'ideology_binary': np.random.choice([0, 1], n)
        }
        df = pd.DataFrame(data)
        
        # Introduce NaNs
        df.loc[0, 'news_exposure_z'] = np.nan
        df.loc[1, 'ideology_binary'] = np.nan
        
        results = fit_binary_model(df)
        
        # Should have dropped 2 rows
        assert results['n_obs'] == n - 2

class TestSaveBinaryModelResults:
    def test_save_binary_model_results(self, tmp_path):
        """Test that results are saved correctly to CSV."""
        results = {
            'model_type': 'test',
            'interaction_coef': 0.5,
            'interaction_pvalue': 0.03,
            'n_obs': 100
        }
        output_path = tmp_path / "test_binary_model.csv"
        
        save_binary_model_results(results, output_path)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert 'interaction_coef' in df.columns
        assert df['interaction_coef'].iloc[0] == 0.5
        assert len(df) == 1

class TestDeriveVariablesIntegration:
    def test_derive_variables_creates_binary(self):
        """Test that derive_variables creates the ideology_binary column."""
        # Create minimal raw-like data
        np.random.seed(42)
        data = {
            'political_ideology': np.random.uniform(-10, 10, 50)
        }
        df = pd.DataFrame(data)
        
        result_df = derive_variables(df)
        
        assert 'ideology_binary' in result_df.columns
        assert result_df['ideology_binary'].dtype in [np.int64, np.int32, int]
        # Check that it's a binary split (0 and 1)
        unique_vals = result_df['ideology_binary'].unique()
        assert set(unique_vals).issubset({0, 1})
