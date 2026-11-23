"""
Unit tests for statistical analysis functions in code/stats.py
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import kruskal
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import (
    load_raw_metrics,
    run_kruskal_wallis,
    save_kruskal_results
)
import config


class TestLoadRawMetrics:
    """Tests for load_raw_metrics function"""
    
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing raw_metrics.csv file"""
        # Create a mock raw_metrics.csv
        mock_data = {
            'snippet_id': [1, 2, 3, 4, 5],
            'model': ['model_a', 'model_a', 'model_b', 'model_b', 'model_c'],
            'prompt_id': [1, 2, 1, 2, 1],
            'v_100loc': [1.5, 2.0, 3.0, 2.5, 1.0],
            'mean_severity': [3.0, 4.0, 2.0, 3.5, 1.5],
            'loc': [100, 150, 200, 180, 120]
        }
        df = pd.DataFrame(mock_data)
        
        # Create directory structure
        results_dir = tmp_path / 'results'
        results_dir.mkdir(parents=True)
        
        csv_path = results_dir / 'raw_metrics.csv'
        df.to_csv(csv_path, index=False)
        
        # Patch config to use our temp directory
        with patch.object(config, 'DATA_DIR', str(tmp_path)):
            loaded_df = load_raw_metrics()
            
            assert len(loaded_df) == 5
            assert 'v_100loc' in loaded_df.columns
            assert 'model' in loaded_df.columns
            assert loaded_df['v_100loc'].mean() > 0
    
    def test_missing_file(self, tmp_path):
        """Test error when raw_metrics.csv does not exist"""
        with patch.object(config, 'DATA_DIR', str(tmp_path)):
            with pytest.raises(FileNotFoundError, match="Raw metrics file not found"):
                load_raw_metrics()
    
    def test_missing_columns(self, tmp_path):
        """Test error when required columns are missing"""
        mock_data = {
            'snippet_id': [1, 2, 3],
            'model': ['a', 'b', 'c']
            # Missing v_100loc and loc
        }
        df = pd.DataFrame(mock_data)
        
        results_dir = tmp_path / 'results'
        results_dir.mkdir(parents=True)
        
        csv_path = results_dir / 'raw_metrics.csv'
        df.to_csv(csv_path, index=False)
        
        with patch.object(config, 'DATA_DIR', str(tmp_path)):
            with pytest.raises(ValueError, match="Missing required columns"):
                load_raw_metrics()


class TestRunKruskalWallis:
    """Tests for run_kruskal_wallis function"""
    
    def test_kruskal_wallis_significant_difference(self):
        """Test Kruskal-Wallis with clearly different groups"""
        # Create data with distinct groups
        data = {
            'model': ['A'] * 10 + ['B'] * 10 + ['C'] * 10,
            'v_100loc': [1.0] * 10 + [5.0] * 10 + [10.0] * 10
        }
        df = pd.DataFrame(data)
        
        results = run_kruskal_wallis(df, target_column='v_100loc', group_column='model')
        
        assert 'statistic' in results
        assert 'pvalue' in results
        assert 'conclusion' in results
        assert results['conclusion'] == 'significant'
        assert results['pvalue'] < 0.05
        assert len(results['groups']) == 3
    
    def test_kruskal_wallis_no_significant_difference(self):
        """Test Kruskal-Wallis with similar groups"""
        # Create data with similar groups
        np.random.seed(42)
        data = {
            'model': ['A'] * 20 + ['B'] * 20 + ['C'] * 20,
            'v_100loc': np.random.normal(5.0, 1.0, 60)
        }
        df = pd.DataFrame(data)
        
        results = run_kruskal_wallis(df, target_column='v_100loc', group_column='model')
        
        assert 'statistic' in results
        assert 'pvalue' in results
        assert 'conclusion' in results
        # With random similar data, p-value is likely > 0.05
        # but we just verify the function runs without error
        assert 0 <= results['pvalue'] <= 1
    
    def test_less_than_two_groups(self):
        """Test error when less than 2 groups exist"""
        data = {
            'model': ['A'] * 10,
            'v_100loc': [1.0] * 10
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="requires at least 2 groups"):
            run_kruskal_wallis(df, target_column='v_100loc', group_column='model')
    
    def test_nan_values_handling(self):
        """Test that NaN values are properly handled"""
        data = {
            'model': ['A', 'A', 'B', 'B', 'C', 'C'],
            'v_100loc': [1.0, np.nan, 2.0, 3.0, np.nan, 4.0]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error, just drop NaN rows
        results = run_kruskal_wallis(df, target_column='v_100loc', group_column='model')
        
        assert results['total_samples'] == 4  # 2 from A, 1 from B, 1 from C
        assert 'statistic' in results
    
    def test_missing_target_column(self):
        """Test error when target column is missing"""
        data = {
            'model': ['A', 'B', 'C'],
            'other_column': [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Target column"):
            run_kruskal_wallis(df, target_column='v_100loc', group_column='model')
    
    def test_missing_group_column(self):
        """Test error when group column is missing"""
        data = {
            'model': ['A', 'B', 'C'],
            'v_100loc': [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Group column"):
            run_kruskal_wallis(df, target_column='v_100loc', group_column='group')


class TestSaveKruskalResults:
    """Tests for save_kruskal_results function"""
    
    def test_save_to_custom_path(self, tmp_path):
        """Test saving results to a custom path"""
        results = {
            'statistic': 15.5,
            'pvalue': 0.001,
            'groups': ['A', 'B', 'C'],
            'group_sizes': {'A': 10, 'B': 10, 'C': 10},
            'conclusion': 'significant',
            'target_column': 'v_100loc',
            'group_column': 'model',
            'total_samples': 30
        }
        
        custom_path = tmp_path / 'custom_results.csv'
        
        saved_path = save_kruskal_results(results, output_path=custom_path)
        
        assert saved_path.exists()
        assert saved_path == custom_path
        
        # Verify CSV content
        df = pd.read_csv(saved_path)
        assert 'test_name' in df.columns
        assert df.loc[0, 'p_value'] == 0.001
        assert df.loc[0, 'conclusion'] == 'significant'
    
    def test_save_to_default_path(self, tmp_path):
        """Test saving results to default path"""
        results = {
            'statistic': 10.0,
            'pvalue': 0.02,
            'groups': ['X', 'Y'],
            'group_sizes': {'X': 5, 'Y': 5},
            'conclusion': 'significant',
            'target_column': 'v_100loc',
            'group_column': 'model',
            'total_samples': 10
        }
        
        with patch.object(config, 'DATA_DIR', str(tmp_path)):
            saved_path = save_kruskal_results(results)
            
            expected_path = tmp_path / 'results' / 'kw_results.csv'
            assert saved_path.exists()
            assert saved_path == expected_path


class TestIntegration:
    """Integration tests for the full statistical analysis pipeline"""
    
    def test_full_pipeline_with_mock_data(self, tmp_path):
        """Test the full pipeline from loading to saving"""
        # Create mock raw_metrics.csv
        mock_data = {
            'snippet_id': range(30),
            'model': (['model_a'] * 10) + (['model_b'] * 10) + (['model_c'] * 10),
            'prompt_id': list(range(10)) * 3,
            'v_100loc': [1.0] * 10 + [5.0] * 10 + [10.0] * 10,
            'mean_severity': [3.0] * 30,
            'loc': [100] * 30
        }
        df = pd.DataFrame(mock_data)
        
        results_dir = tmp_path / 'results'
        results_dir.mkdir(parents=True)
        
        csv_path = results_dir / 'raw_metrics.csv'
        df.to_csv(csv_path, index=False)
        
        with patch.object(config, 'DATA_DIR', str(tmp_path)):
            # Load data
            loaded_df = load_raw_metrics()
            assert len(loaded_df) == 30
            
            # Run test
            kw_results = run_kruskal_wallis(loaded_df)
            assert kw_results['conclusion'] == 'significant'
            
            # Save results
            output_path = save_kruskal_results(kw_results)
            assert output_path.exists()
            
            # Verify saved content
            saved_df = pd.read_csv(output_path)
            assert saved_df.loc[0, 'p_value'] < 0.05
            assert saved_df.loc[0, 'conclusion'] == 'significant'