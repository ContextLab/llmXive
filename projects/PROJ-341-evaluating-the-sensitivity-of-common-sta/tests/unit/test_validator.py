"""
Unit tests for the validator module (T031).
Tests data preparation and statistical test functions without requiring network access.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import json
import tempfile

# Import the module under test
from code.analysis.validator import (
    prepare_data_for_ttest,
    prepare_data_for_anova,
    prepare_data_for_chi_squared,
    run_t_test,
    run_anova,
    run_chi_squared,
    save_p_values_to_csv,
    load_p_values_to_csv_safe
)

class TestDataPreparation:
    """Tests for data preparation functions."""
    
    def test_prepare_data_for_ttest(self):
        """Test t-test data preparation with synthetic data."""
        # Create a simple dataset
        df = pd.DataFrame({
            'target': [0, 0, 0, 1, 1, 1],
            'feature': [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]
        })
        
        group1, group2 = prepare_data_for_ttest(df, target_col='target', feature_col='feature')
        
        assert len(group1) == 3
        assert len(group2) == 3
        assert np.allclose(group1, [1.0, 2.0, 3.0])
        assert np.allclose(group2, [10.0, 11.0, 12.0])
    
    def test_prepare_data_for_ttest_missing_target(self):
        """Test t-test data preparation with missing target column."""
        df = pd.DataFrame({
            'feature': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError, match="Target column"):
            prepare_data_for_ttest(df, target_col='target', feature_col='feature')
    
    def test_prepare_data_for_anova(self):
        """Test ANOVA data preparation with synthetic data."""
        df = pd.DataFrame({
            'target': [0, 0, 0, 1, 1, 1, 2, 2, 2],
            'feature': [1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 20.0, 21.0, 22.0]
        })
        
        groups = prepare_data_for_anova(df, target_col='target', feature_col='feature')
        
        assert len(groups) == 3
        assert len(groups[0]) == 3
        assert len(groups[1]) == 3
        assert len(groups[2]) == 3
    
    def test_prepare_data_for_chi_squared(self):
        """Test chi-squared data preparation with synthetic data."""
        df = pd.DataFrame({
            'col1': ['A', 'A', 'B', 'B'],
            'col2': ['X', 'Y', 'X', 'Y']
        })
        
        contingency = prepare_data_for_chi_squared(df, col1='col1', col2='col2')
        
        assert contingency.shape == (2, 2)
        assert contingency[0, 0] == 1  # A, X
        assert contingency[0, 1] == 1  # A, Y
        assert contingency[1, 0] == 1  # B, X
        assert contingency[1, 1] == 1  # B, Y

class TestStatisticalTests:
    """Tests for statistical test functions."""
    
    def test_run_t_test(self):
        """Test t-test execution."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        
        result = run_t_test(group1, group2)
        
        assert result['test'] == 't-test'
        assert result['p_value'] is not None
        assert result['statistic'] is not None
        assert result['group1_size'] == 5
        assert result['group2_size'] == 5
    
    def test_run_anova(self):
        """Test ANOVA execution."""
        groups = [
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 11.0, 12.0]),
            np.array([20.0, 21.0, 22.0])
        ]
        
        result = run_anova(groups)
        
        assert result['test'] == 'anova'
        assert result['p_value'] is not None
        assert result['statistic'] is not None
        assert result['n_groups'] == 3
    
    def test_run_chi_squared(self):
        """Test chi-squared execution."""
        contingency = np.array([
            [10, 20],
            [30, 40]
        ])
        
        result = run_chi_squared(contingency)
        
        assert result['test'] == 'chi-squared'
        assert result['p_value'] is not None
        assert result['statistic'] is not None
        assert result['degrees_of_freedom'] == 1

class TestOutputFunctions:
    """Tests for output functions."""
    
    def test_save_and_load_p_values_csv(self):
        """Test saving and loading p-values to/from CSV."""
        results = [
            {
                'dataset': 'test_dataset',
                'test': 't-test',
                'p_value': 0.05,
                'statistic': 1.96,
                'group1_size': 10,
                'group2_size': 10,
                'feature': 'feature1'
            },
            {
                'dataset': 'test_dataset',
                'test': 'anova',
                'p_value': 0.01,
                'statistic': 5.0,
                'n_groups': 3,
                'feature': 'feature1'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            save_p_values_to_csv(results, output_path=temp_path)
            
            # Verify file exists
            assert os.path.exists(temp_path)
            
            # Load and verify
            loaded_df = load_p_values_to_csv_safe(temp_path)
            assert len(loaded_df) == 2
            assert loaded_df.iloc[0]['dataset'] == 'test_dataset'
            assert loaded_df.iloc[0]['test'] == 't-test'
            assert loaded_df.iloc[0]['p_value'] == 0.05
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_load_nonexistent_csv(self):
        """Test loading from a non-existent file."""
        df = load_p_values_to_csv_safe("nonexistent_file.csv")
        assert df.empty

if __name__ == "__main__":
    pytest.main([__file__, "-v"])