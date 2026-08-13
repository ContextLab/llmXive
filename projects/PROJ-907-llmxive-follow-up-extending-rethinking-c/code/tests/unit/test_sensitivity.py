"""
Unit tests for sensitivity analysis logic (T027).
"""
import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.sensitivity import run_clustering_with_threshold, run_benchmark_for_threshold, run_sensitivity_sweep, THRESHOLD_SET

class TestSensitivitySweepLogic:
    
    @patch('src.sensitivity.load_routing_cache')
    @patch('src.sensitivity.compute_mean_routing_vectors')
    @patch('src.sensitivity.perform_clustering')
    @patch('src.sensitivity.save_cluster_centers')
    @patch('src.sensitivity.save_null_hypothesis_flag')
    def test_run_clustering_with_threshold_valid(
        self, mock_save_flag, mock_save_centers, mock_perform, mock_compute, mock_load
    ):
        """Test that clustering derivation runs and saves artifacts for a valid threshold."""
        mock_compute.return_value = np.random.rand(10, 32) # 10 timesteps, 32 dim
        mock_perform.return_value = (np.random.rand(2, 32), 0.5, False) # centers, score, is_null
        
        # Mock the get_routing_cache_path to return a dummy path that exists
        with patch('src.sensitivity.get_routing_cache_path') as mock_path:
            mock_path.return_value = MagicMock(exists=True)
            
            centers, is_null = run_clustering_with_threshold(0.05)
            
            assert centers is not None
            assert is_null is False
            mock_perform.assert_called_once()
            mock_save_centers.assert_called_once()
            mock_save_flag.assert_called_once()

    @patch('src.sensitivity.load_routing_cache')
    @patch('src.sensitivity.compute_mean_routing_vectors')
    @patch('src.sensitivity.perform_clustering')
    @patch('src.sensitivity.generate_global_average')
    @patch('src.sensitivity.save_cluster_centers')
    @patch('src.sensitivity.save_null_hypothesis_flag')
    def test_run_clustering_with_threshold_null_hypothesis(
        self, mock_save_flag, mock_save_centers, mock_gen_avg, mock_perform, mock_compute, mock_load
    ):
        """Test that null hypothesis is triggered and global average is generated."""
        mock_compute.return_value = np.random.rand(10, 32)
        # Simulate a low score that triggers null
        mock_perform.return_value = (np.random.rand(1, 32), 0.1, True) 
        
        mock_gen_avg.return_value = np.random.rand(32) # Global average vector
        
        with patch('src.sensitivity.get_routing_cache_path') as mock_path:
            mock_path.return_value = MagicMock(exists=True)
            
            centers, is_null = run_clustering_with_threshold(0.05)
            
            assert is_null is True
            mock_gen_avg.assert_called_once()
            mock_save_flag.assert_called_with(True, overwrite=True)

    @patch('subprocess.run')
    @patch('pandas.read_csv')
    @patch('src.sensitivity.get_results_path')
    def test_run_benchmark_for_threshold(self, mock_get_path, mock_read_csv, mock_subprocess):
        """Test that benchmark execution parses FID correctly."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Mock CSV content
        mock_df = MagicMock()
        mock_df.__getitem__ = lambda self, key: {'model_type': ['static', 'dynamic'], 'fid_score': [15.5, 12.0]}[key]
        mock_df.iloc = [[15.5, 12.0]] # Simplified
        mock_read_csv.return_value = mock_df
        
        # Mock the dataframe filtering
        with patch.object(mock_df, '__getitem__', return_value=pd.Series(['static', 'dynamic'])):
            with patch.object(mock_df, 'iloc', new_callable=MagicMock) as mock_iloc:
                # Setup mock for filtering
                mock_filtered = MagicMock()
                mock_filtered.iloc = [MagicMock(__getitem__=lambda self, key: 15.5)]
                mock_df.__getitem__ = lambda self, key: mock_filtered if key == 'model_type' else None
                # Actually, let's mock the DataFrame logic more simply
                pass

        # Re-mock for simplicity
        mock_read_csv.return_value = MagicMock(
            **{'iloc[-1]': {'fid_score': 15.5, 'model_type': 'static'}},
            **{'__getitem__': lambda self, key: [True, False] if key == 'model_type' else []} # Simplified filter
        )
        
        # Better mock for pandas
        import pandas as pd
        mock_df = pd.DataFrame({'model_type': ['static', 'dynamic'], 'fid_score': [15.5, 12.0]})
        mock_read_csv.return_value = mock_df

        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = lambda self, name: MagicMock(exists=True)
        mock_get_path.return_value = mock_path_instance

        fid = run_benchmark_for_threshold()
        assert fid == 15.5
        mock_subprocess.assert_called_once()

    @patch('src.sensitivity.run_clustering_with_threshold')
    @patch('src.sensitivity.run_benchmark_for_threshold')
    def test_run_sensitivity_sweep(self, mock_bench, mock_cluster):
        """Test the full sweep logic aggregates results correctly."""
        mock_cluster.return_value = (MagicMock(), False)
        mock_bench.return_value = 15.0
        
        with patch('src.sensitivity.THRESHOLD_SET', [0.01, 0.05]):
            with patch('src.sensitivity.ensure_directories_exist'):
                with patch('builtins.open', mock_open()) as mock_file:
                    results = run_sensitivity_sweep()
                    
                    assert len(results['thresholds']) == 2
                    assert len(results['fid_scores']) == 2
                    assert 'summary' in results
                    assert results['summary']['min_fid'] == 15.0
                    assert results['summary']['max_fid'] == 15.0
                    assert results['summary']['range'] == 0.0
                    mock_file.assert_called()