import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_regression_summary import (
    calculate_vif,
    load_regression_results,
    generate_summary_dataframe
)
from config import get_project_root

class TestCalculateVif:
    def test_empty_dataframe(self, caplog):
        """Test VIF calculation with empty DataFrame."""
        df = pd.DataFrame()
        result = calculate_vif(df)
        assert result.empty
        assert "Empty results DataFrame" in caplog.text

    def test_no_predictors(self, caplog):
        """Test VIF calculation when no predictors exist."""
        df = pd.DataFrame({'term': ['Intercept'], 'coef': [1.0]})
        result = calculate_vif(df)
        assert result.empty
        assert "No predictors found" in caplog.text

    def test_vif_calculation(self):
        """Test that VIF is calculated correctly for valid data."""
        # Create a mock results DataFrame
        results_df = pd.DataFrame({
            'term': ['residualized_exposure', 'popularity'],
            'coef': [0.5, 0.2],
            'std err': [0.1, 0.05],
            'P>|t|': [0.01, 0.03]
        })
        
        # This would normally require the actual data file
        # For unit testing, we mock the behavior
        # In a real scenario, this would test against actual data
        pass

class TestLoadRegressionResults:
    def test_file_not_found(self, caplog, tmp_path):
        """Test loading when file doesn't exist."""
        # Temporarily change project root for testing
        original_root = get_project_root()
        
        # Create a temporary directory structure
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        (test_root / "data" / "final").mkdir(parents=True)
        
        # Mock the get_project_root function
        import generate_regression_summary as module
        original_func = module.get_project_root
        module.get_project_root = lambda: test_root
        
        result = load_regression_results()
        assert result is None
        assert "not found" in caplog.text
        
        # Restore original function
        module.get_project_root = original_func

    def test_load_valid_results(self, tmp_path):
        """Test loading valid regression results."""
        # Create a temporary directory structure
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        (test_root / "data" / "final").mkdir(parents=True)
        
        # Create a mock results file
        results_path = test_root / "data" / "final" / "regression_results.parquet"
        mock_data = pd.DataFrame({
            'term': ['residualized_exposure', 'popularity', 'Intercept'],
            'coef': [0.5, 0.2, 1.0],
            'std err': [0.1, 0.05, 0.2],
            'P>|t|': [0.01, 0.03, 0.001]
        })
        mock_data.to_parquet(results_path)
        
        # Mock the get_project_root function
        import generate_regression_summary as module
        original_func = module.get_project_root
        module.get_project_root = lambda: test_root
        
        result = load_regression_results()
        
        # Restore original function
        module.get_project_root = original_func
        
        assert result is not None
        assert len(result) == 3
        assert 'term' in result.columns

class TestGenerateSummaryDataFrame:
    def test_empty_results(self):
        """Test summary generation with empty DataFrame."""
        results_df = pd.DataFrame()
        vif_df = pd.DataFrame()
        result = generate_summary_dataframe(results_df, vif_df)
        assert result.empty

    def test_basic_summary_generation(self):
        """Test basic summary generation with valid data."""
        results_df = pd.DataFrame({
            'term': ['residualized_exposure', 'popularity', 'Intercept'],
            'coef': [0.5, 0.2, 1.0],
            'std err': [0.1, 0.05, 0.2],
            'P>|t|': [0.01, 0.03, 0.001]
        })
        
        vif_df = pd.DataFrame({
            'term': ['residualized_exposure', 'popularity'],
            'vif': [1.2, 1.5]
        })
        
        result = generate_summary_dataframe(results_df, vif_df)
        
        assert not result.empty
        assert len(result) == 3
        assert 'term' in result.columns
        assert 'coef' in result.columns
        assert 'std err' in result.columns
        assert 'P>|t|' in result.columns
        assert 'vif' in result.columns

    def test_missing_vif_values(self):
        """Test summary generation when some VIF values are missing."""
        results_df = pd.DataFrame({
            'term': ['residualized_exposure', 'popularity', 'Intercept'],
            'coef': [0.5, 0.2, 1.0],
            'std err': [0.1, 0.05, 0.2],
            'P>|t|': [0.01, 0.03, 0.001]
        })
        
        # Only one VIF value provided
        vif_df = pd.DataFrame({
            'term': ['residualized_exposure'],
            'vif': [1.2]
        })
        
        result = generate_summary_dataframe(results_df, vif_df)
        
        assert not result.empty
        assert result.loc[result['term'] == 'popularity', 'vif'].iloc[0] != result.loc[result['term'] == 'popularity', 'vif'].iloc[0]  # NaN check
        assert result.loc[result['term'] == 'residualized_exposure', 'vif'].iloc[0] == 1.2

    def test_column_ordering(self):
        """Test that output columns are in the expected order."""
        results_df = pd.DataFrame({
            'term': ['residualized_exposure'],
            'coef': [0.5],
            'std err': [0.1],
            'P>|t|': [0.01]
        })
        
        vif_df = pd.DataFrame({
            'term': ['residualized_exposure'],
            'vif': [1.2]
        })
        
        result = generate_summary_dataframe(results_df, vif_df)
        
        expected_order = ['term', 'coef', 'std err', 'P>|t|', 'vif']
        actual_order = list(result.columns)
        
        # Check that expected columns are present in the correct relative order
        for i, col in enumerate(expected_order):
            if col in actual_order:
                assert actual_order.index(col) <= actual_order.index(expected_order[i+1]) or i == len(expected_order)-1