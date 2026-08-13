"""
Unit tests for sensitivity analysis logic.
"""
import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sensitivity import _simple_greedy_clustering, THRESHOLDS

class TestSensitivitySweepLogic:
    def test_thresholds_defined(self):
        """Verify the set of thresholds to sweep is correct."""
        assert set(THRESHOLDS) == {0.01, 0.05, 0.1}

    def test_simple_greedy_clustering_empty(self):
        """Test clustering with empty input."""
        vectors = np.array([]).reshape(0, 10)
        clusters, k, score = _simple_greedy_clustering(vectors, 0.1)
        assert clusters == []
        assert k == 0

    def test_simple_greedy_clustering_single(self):
        """Test clustering with single vector."""
        vectors = np.array([[0.1, 0.2, 0.3]])
        clusters, k, score = _simple_greedy_clustering(vectors, 0.1)
        assert len(clusters) >= 1
        assert k >= 1

    @patch('sensitivity.run_clustering_with_threshold')
    @patch('sensitivity.run_benchmark_with_map')
    @patch('sensitivity.RESULTS_DIR')
    @patch('sensitivity.CACHE_DIR')
    def test_sensitivity_analysis_flow(self, mock_cache_dir, mock_results_dir, mock_run_bench, mock_run_cluster):
        """Test the main flow of sensitivity analysis."""
        from sensitivity import run_sensitivity_analysis
        
        # Mock file existence
        mock_temp_map = MagicMock()
        mock_temp_map.exists.return_value = True
        
        mock_run_cluster.return_value = True
        mock_run_bench.return_value = {
            'fid_score': 0.5,
            'latency_s': 10.0,
            'model_type': 'static',
            'timestamp': '2023-01-01'
        }
        
        # Mock the temporary map path
        with patch('sensitivity.CACHE_DIR.__truediv__', return_value=mock_temp_map):
            with patch('builtins.open', mock_open()) as mock_file:
                result = run_sensitivity_analysis()
                
                # Verify clustering was called for each threshold
                assert mock_run_cluster.call_count == len(THRESHOLDS)
                # Verify benchmark was called for each threshold
                assert mock_run_bench.call_count == len(THRESHOLDS)
                
                # Verify output structure
                assert 'thresholds_swept' in result
                assert 'results' in result
                assert 'fid_degradation_range' in result
                assert result['fid_degradation_range']['range'] is not None