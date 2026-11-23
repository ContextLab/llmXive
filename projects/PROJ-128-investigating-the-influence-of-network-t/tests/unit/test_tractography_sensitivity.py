"""
Unit tests for Tractography Sensitivity Analysis (Task T042)

These tests verify the logic of the tractography confidence thresholding
and the calculation of graph metrics under different thresholds.
"""

import os
import sys
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.tractography_sensitivity import (
    load_connectivity_matrix_with_threshold,
    run_tractography_sensitivity_analysis
)
from preprocess.structural import calculate_graph_metrics

class TestLoadConnectivityMatrixWithThreshold:
    def test_thresholding_filters_edges(self):
        """Test that edges below the threshold are filtered out."""
        # Create a mock matrix and confidence
        matrix = np.array([
            [0, 0.5, 0.8],
            [0.5, 0, 0.3],
            [0.8, 0.3, 0]
        ])
        confidence = np.array([
            [0, 0.4, 0.9],
            [0.4, 0, 0.2],
            [0.9, 0.2, 0]
        ])
        
        # Mock the loader to return our test data
        with patch('analysis.tractography_sensitivity.load_hcp_dmri') as mock_loader:
            mock_loader.return_value = (matrix, confidence)
            
            config = {}
            result = load_connectivity_matrix_with_threshold('test_subject', 0.5, config)
            
            # Expected: edges with confidence < 0.5 should be zeroed
            expected = np.array([
                [0, 0, 0.8],
                [0, 0, 0],
                [0.8, 0, 0]
            ])
            
            np.testing.assert_array_almost_equal(result, expected)

    def test_diagonal_remains_zero(self):
        """Test that the diagonal remains zero after thresholding."""
        matrix = np.array([
            [0, 0.5, 0.8],
            [0.5, 0, 0.3],
            [0.8, 0.3, 0]
        ])
        confidence = np.ones_like(matrix) * 0.5
        
        with patch('analysis.tractography_sensitivity.load_hcp_dmri') as mock_loader:
            mock_loader.return_value = (matrix, confidence)
            
            config = {}
            result = load_connectivity_matrix_with_threshold('test_subject', 0.0, config)
            
            # Diagonal should be zero
            assert np.diag(result).sum() == 0

    def test_invalid_data_raises_error(self):
        """Test that invalid data raises an appropriate error."""
        with patch('analysis.tractography_sensitivity.load_hcp_dmri') as mock_loader:
            mock_loader.return_value = (None, None)
            
            config = {}
            with pytest.raises(ValueError):
                load_connectivity_matrix_with_threshold('test_subject', 0.5, config)

class TestRunTractographySensitivityAnalysis:
    @pytest.fixture
    def mock_config(self):
        return {
            'RAW_DATA_DIR': 'data/raw',
            'PROCESSED_DATA_DIR': 'data/processed',
            'TRACTOGRAPHY_CONFIDENCE_THRESHOLDS': [0.0, 0.5],
            'SUBJECT_IDS': ['sub_001', 'sub_002']
        }

    def test_runs_for_all_subjects_and_thresholds(self, mock_config):
        """Test that the analysis runs for all subjects and thresholds."""
        # Mock the loader and graph metric calculation
        with patch('analysis.tractography_sensitivity.load_hcp_dmri') as mock_loader:
            with patch('analysis.tractography_sensitivity.calculate_graph_metrics') as mock_metrics:
                mock_loader.return_value = (
                    np.array([[0, 0.5], [0.5, 0]]),
                    np.array([[0, 0.6], [0.6, 0]])
                )
                mock_metrics.return_value = {
                    'global_efficiency': 0.5,
                    'clustering_coefficient': 0.3,
                    'modularity': 0.4,
                    'num_nodes': 2,
                    'num_edges': 1,
                    'density': 0.5
                }
                
                result_df = run_tractography_sensitivity_analysis(
                    mock_config['SUBJECT_IDS'], mock_config
                )
                
                # Check that we have results for all combinations
                expected_rows = len(mock_config['SUBJECT_IDS']) * len(mock_config['TRACTOGRAPHY_CONFIDENCE_THRESHOLDS'])
                assert len(result_df) == expected_rows

    def test_handles_errors_gracefully(self, mock_config):
        """Test that errors are logged but do not stop the analysis."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second call
                raise Exception("Test error")
            return (np.array([[0, 0.5], [0.5, 0]]), np.array([[0, 0.6], [0.6, 0]]))
        
        with patch('analysis.tractography_sensitivity.load_hcp_dmri') as mock_loader:
            mock_loader.side_effect = side_effect
            
            with patch('analysis.tractography_sensitivity.calculate_graph_metrics') as mock_metrics:
                mock_metrics.return_value = {
                    'global_efficiency': 0.5,
                    'clustering_coefficient': 0.3,
                    'modularity': 0.4,
                    'num_nodes': 2,
                    'num_edges': 1,
                    'density': 0.5
                }
                
                result_df = run_tractography_sensitivity_analysis(
                    mock_config['SUBJECT_IDS'], mock_config
                )
                
                # Check that we have results for all attempts, even with errors
                assert len(result_df) == len(mock_config['SUBJECT_IDS']) * len(mock_config['TRACTOGRAPHY_CONFIDENCE_THRESHOLDS'])
                
                # Check that the error is recorded
                error_rows = result_df[result_df['global_efficiency'].isna()]
                assert len(error_rows) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
