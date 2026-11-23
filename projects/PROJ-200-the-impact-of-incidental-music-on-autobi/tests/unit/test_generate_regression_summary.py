import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generate_regression_summary import (
    calculate_vif,
    generate_summary_dataframe
)

class TestCalculateVIF:
    def test_vif_calculation_no_collinearity(self):
        """Test VIF calculation when predictors are uncorrelated."""
        # Create a mock model with uncorrelated predictors
        mock_model = Mock()
        
        # Create uncorrelated design matrix
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = np.random.normal(0, 1, n)
        x3 = np.random.normal(0, 1, n)
        
        exog = np.column_stack([np.ones(n), x1, x2, x3])
        col_names = ['Intercept', 'x1', 'x2', 'x3']
        
        mock_model.model.exog = exog
        mock_model.model.exog_names = col_names
        
        vif_dict = calculate_vif(mock_model)
        
        # VIF should be close to 1 for uncorrelated variables
        assert 'x1' in vif_dict
        assert 'x2' in vif_dict
        assert 'x3' in vif_dict
        assert 0.9 <= vif_dict['x1'] <= 1.1
        assert 0.9 <= vif_dict['x2'] <= 1.1
        assert 0.9 <= vif_dict['x3'] <= 1.1

    def test_vif_calculation_high_collinearity(self):
        """Test VIF calculation when predictors are highly correlated."""
        mock_model = Mock()
        
        # Create highly correlated design matrix
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 + np.random.normal(0, 0.01, n)  # Highly correlated
        x3 = np.random.normal(0, 1, n)
        
        exog = np.column_stack([np.ones(n), x1, x2, x3])
        col_names = ['Intercept', 'x1', 'x2', 'x3']
        
        mock_model.model.exog = exog
        mock_model.model.exog_names = col_names
        
        vif_dict = calculate_vif(mock_model)
        
        # VIF should be high for correlated variables
        assert vif_dict['x1'] > 5
        assert vif_dict['x2'] > 5
        # x3 should still be low
        assert 0.9 <= vif_dict['x3'] <= 1.1

class TestGenerateSummaryDataFrame:
    def test_summary_dataframe_structure(self):
        """Test that summary dataframe has correct columns."""
        # Create a mock model
        mock_model = Mock()
        
        # Mock params, bse, tvalues
        mock_model.params = pd.Series([0.5, 0.3], index=['x1', 'x2'])
        mock_model.bse = pd.Series([0.1, 0.15], index=['x1', 'x2'])
        mock_model.tvalues = pd.Series([5.0, 2.0], index=['x1', 'x2'])
        mock_model.df_resid = 98
        
        vif_dict = {'x1': 1.2, 'x2': 1.5}
        
        summary_df = generate_summary_dataframe(mock_model, vif_dict)
        
        # Check columns
        expected_columns = ['variable', 'coefficient', 'std_error', 't_statistic', 'p_value', 'vif']
        assert list(summary_df.columns) == expected_columns
        
        # Check values
        assert len(summary_df) == 2
        assert summary_df.loc[summary_df['variable'] == 'x1', 'coefficient'].iloc[0] == 0.5
        assert summary_df.loc[summary_df['variable'] == 'x1', 'std_error'].iloc[0] == 0.1
        assert summary_df.loc[summary_df['variable'] == 'x1', 'vif'].iloc[0] == 1.2

    def test_summary_dataframe_pvalue_calculation(self):
        """Test that p-values are correctly calculated."""
        mock_model = Mock()
        
        # t-value of 0 should give p-value of 1.0
        mock_model.params = pd.Series([0.0], index=['x1'])
        mock_model.bse = pd.Series([1.0], index=['x1'])
        mock_model.tvalues = pd.Series([0.0], index=['x1'])
        mock_model.df_resid = 100
        
        vif_dict = {'x1': 1.0}
        
        summary_df = generate_summary_dataframe(mock_model, vif_dict)
        
        # p-value should be close to 1.0 for t=0
        assert 0.99 < summary_df['p_value'].iloc[0] < 1.01

    def test_summary_dataframe_with_nan_vif(self):
        """Test summary dataframe generation when VIF is missing."""
        mock_model = Mock()
        
        mock_model.params = pd.Series([0.5], index=['x1'])
        mock_model.bse = pd.Series([0.1], index=['x1'])
        mock_model.tvalues = pd.Series([5.0], index=['x1'])
        mock_model.df_resid = 98
        
        # Empty VIF dict
        vif_dict = {}
        
        summary_df = generate_summary_dataframe(mock_model, vif_dict)
        
        assert summary_df['vif'].iloc[0] != summary_df['vif'].iloc[0]  # NaN check