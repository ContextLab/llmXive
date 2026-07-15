import pytest
import pandas as pd
import numpy as np
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
import os
import tempfile

class TestAggregator:
    
    def test_calculate_error_rates_type_i(self):
        """Test Type I error rate calculation (H0 true)"""
        # Create synthetic data: H0 true, 100 iterations, 5 rejections (alpha=0.05)
        data = {
            'sample_size': [5] * 100,
            'effect_size': [0.0] * 100,
            'test_type': ['t-test'] * 100,
            'p_value': [0.01] * 5 + [0.1] * 95,  # 5 rejections
            'hypothesis': ['H0'] * 100
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]['error_type'] == 'Type_I'
        assert result.iloc[0]['error_rate'] == 0.05  # 5/100
        assert result.iloc[0]['error_count'] == 5
        
    def test_calculate_error_rates_type_ii(self):
        """Test Type II error rate calculation (H1 true)"""
        # Create synthetic data: H1 true, 100 iterations, 80 rejections (power=0.80)
        # Type II = 1 - power = 0.20
        data = {
            'sample_size': [50] * 100,
            'effect_size': [0.5] * 100,
            'test_type': ['t-test'] * 100,
            'p_value': [0.01] * 80 + [0.1] * 20,  # 80 rejections
            'hypothesis': ['H1'] * 100
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]['error_type'] == 'Type_II'
        assert result.iloc[0]['error_rate'] == 0.20  # 20/100 (fail to reject when H1 true)
        assert result.iloc[0]['error_count'] == 20
        
    def test_calculate_error_rates_multiple_conditions(self):
        """Test aggregation across multiple sample sizes and test types"""
        data = {
            'sample_size': [5] * 50 + [10] * 50,
            'effect_size': [0.0] * 50 + [0.0] * 50,
            'test_type': ['t-test'] * 50 + ['anova'] * 50,
            'p_value': [0.01] * 2 + [0.1] * 48 + [0.01] * 3 + [0.1] * 47,
            'hypothesis': ['H0'] * 100
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        assert len(result) == 2
        
        # Check t-test row
        ttest_row = result[result['test_type'] == 't-test'].iloc[0]
        assert ttest_row['sample_size'] == 5
        assert ttest_row['error_rate'] == 0.04  # 2/50
        
        # Check anova row
        anova_row = result[result['test_type'] == 'anova'].iloc[0]
        assert anova_row['sample_size'] == 10
        assert anova_row['error_rate'] == 0.06  # 3/50
        
    def test_save_aggregated_results(self):
        """Test saving results to CSV"""
        data = {
            'sample_size': [5],
            'effect_size': [0.0],
            'test_type': ['t-test'],
            'hypothesis': ['H0'],
            'error_type': ['Type_I'],
            'total_iterations': [100],
            'error_count': [5],
            'error_rate': [0.05],
            'alpha_threshold': [0.05]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_error_rates.csv')
            save_aggregated_results(df, output_path)
            
            assert os.path.exists(output_path)
            
            # Verify contents
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 1
            assert loaded_df.iloc[0]['error_rate'] == 0.05
            
    def test_empty_dataframe(self):
        """Test handling of empty input"""
        df = pd.DataFrame()
        result = calculate_error_rates(df)
        assert result.empty
        
    def test_mixed_hypotheses(self):
        """Test calculation with both H0 and H1 in same dataset"""
        data = {
            'sample_size': [5] * 100 + [5] * 100,
            'effect_size': [0.0] * 200,
            'test_type': ['t-test'] * 200,
            'p_value': [0.01] * 5 + [0.1] * 95 + [0.01] * 80 + [0.1] * 20,
            'hypothesis': ['H0'] * 100 + ['H1'] * 100
        }
        df = pd.DataFrame(data)
        
        result = calculate_error_rates(df, alpha=0.05)
        
        assert len(result) == 2
        
        type_i = result[result['error_type'] == 'Type_I'].iloc[0]
        type_ii = result[result['error_type'] == 'Type_II'].iloc[0]
        
        assert type_i['error_rate'] == 0.05
        assert type_ii['error_rate'] == 0.20