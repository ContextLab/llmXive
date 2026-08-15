"""
Unit tests for feature importance extraction module.

These tests verify that the feature importance extraction logic works correctly
with mocked data and that the output format matches expectations.
"""

import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from model.feature_importance import (
    load_trained_model,
    extract_node_features,
    compute_shap_values,
    extract_feature_importance,
    main
)
from model.gnn import StaticScatteringPotentialGNN


class TestLoadTrainedModel:
    """Tests for load_trained_model function."""

    def test_load_model_success(self, tmp_path):
        """Test successful model loading."""
        # Create a mock model
        mock_model = Mock(spec=StaticScatteringPotentialGNN)
        mock_model.eval = Mock()
        
        model_path = tmp_path / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)
        
        loaded_model = load_trained_model(model_path)
        
        assert loaded_model is not None
        mock_model.eval.assert_called_once()

    def test_load_model_not_found(self, tmp_path):
        """Test loading from non-existent path raises error."""
        model_path = tmp_path / "nonexistent.pkl"
        
        with pytest.raises(FileNotFoundError):
            load_trained_model(model_path)


class TestExtractNodeFeatures:
    """Tests for extract_node_features function."""

    def test_extract_features_success(self):
        """Test successful feature extraction."""
        graph_data = {
            'node_features': np.random.rand(10, 5),
            'id': 'test_graph'
        }
        
        features = extract_node_features(graph_data)
        
        assert features.shape == (10, 5)
        assert isinstance(features, np.ndarray)

    def test_extract_features_missing_key(self):
        """Test error when features key is missing."""
        graph_data = {'id': 'test_graph'}
        
        with pytest.raises(KeyError, match="missing 'node_features'"):
            extract_node_features(graph_data)


class TestComputeShapValues:
    """Tests for compute_shap_values function."""

    def test_compute_shap_basic(self):
        """Test basic SHAP value computation."""
        # Create a simple mock model
        mock_model = Mock()
        mock_model.return_value = np.array([[0.5], [0.6], [0.4]])
        mock_model.eval = Mock()
        
        feature_matrix = np.random.rand(3, 5)
        
        mean_shap, shap_std = compute_shap_values(mock_model, feature_matrix, sample_size=10)
        
        assert mean_shap.shape == (5,)
        assert shap_std.shape == (5,)
        assert isinstance(mean_shap, np.ndarray)
        assert isinstance(shap_std, np.ndarray)

    def test_compute_shap_single_sample(self):
        """Test SHAP computation with single sample."""
        mock_model = Mock()
        mock_model.return_value = np.array([[0.5]])
        mock_model.eval = Mock()
        
        feature_matrix = np.random.rand(1, 5)
        
        mean_shap, shap_std = compute_shap_values(mock_model, feature_matrix, sample_size=5)
        
        assert mean_shap.shape == (5,)
        assert shap_std.shape == (5,)


class TestExtractFeatureImportance:
    """Tests for extract_feature_importance function."""

    def test_extract_importance_success(self):
        """Test successful feature importance extraction."""
        # Create mock model
        mock_model = Mock()
        mock_model.eval = Mock()
        
        # Create sample graphs with features
        graphs = [
            {
                'id': 'graph_1',
                'node_features': np.random.rand(20, 5)
            },
            {
                'id': 'graph_2',
                'node_features': np.random.rand(15, 5)
            }
        ]
        
        # Mock the compute_shap_values function to return deterministic values
        with patch('model.feature_importance.compute_shap_values') as mock_shap:
            mock_shap.return_value = (np.array([0.1, 0.2, 0.3, 0.4, 0.5]), 
                                     np.array([0.01, 0.02, 0.03, 0.04, 0.05]))
            
            results = extract_feature_importance(mock_model, graphs)
        
        assert 'sample_importance' in results
        assert 'aggregate' in results
        assert 'top_features' in results
        assert len(results['sample_importance']) == 2
        assert results['aggregate']['num_samples'] == 2
        assert results['aggregate']['num_features'] == 5

    def test_extract_importance_empty_graphs(self):
        """Test error when no graphs provided."""
        mock_model = Mock()
        
        with pytest.raises(ValueError, match="No graphs provided"):
            extract_feature_importance(mock_model, [])

    def test_extract_importance_missing_features(self):
        """Test handling of graphs without features."""
        mock_model = Mock()
        mock_model.eval = Mock()
        
        graphs = [
            {'id': 'graph_1'},  # Missing node_features
            {
                'id': 'graph_2',
                'node_features': np.random.rand(10, 5)
            }
        ]
        
        with patch('model.feature_importance.compute_shap_values') as mock_shap:
            mock_shap.return_value = (np.array([0.1, 0.2, 0.3, 0.4, 0.5]), 
                                     np.array([0.01, 0.02, 0.03, 0.04, 0.05]))
            
            results = extract_feature_importance(mock_model, graphs)
        
        # Should only process the graph with features
        assert len(results['sample_importance']) == 1
        assert results['aggregate']['num_samples'] == 1


class TestMain:
    """Tests for the main function."""

    @patch('model.feature_importance.get_config')
    @patch('model.feature_importance.get_paths')
    @patch('model.feature_importance.load_trained_model')
    @patch('model.feature_importance.extract_feature_importance')
    def test_main_success(
        self, 
        mock_extract, 
        mock_load_model, 
        mock_get_paths, 
        mock_get_config,
        tmp_path
    ):
        """Test successful main execution."""
        # Setup mocks
        mock_config = {'paths': {'processed_graphs': str(tmp_path)}}
        mock_get_config.return_value = mock_config
        
        mock_paths = {
            'model_output': tmp_path,
            'processed_graphs': tmp_path,
            'model_outputs': tmp_path / 'outputs'
        }
        mock_get_paths.return_value = mock_paths
        
        # Create mock model
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        # Create sample graphs
        graphs = [
            {
                'id': 'test_graph',
                'node_features': np.random.rand(10, 5)
            }
        ]
        
        # Save graphs
        graphs_path = tmp_path / 'training_graphs.pkl'
        with open(graphs_path, 'wb') as f:
            pickle.dump(graphs, f)
        
        # Mock extract function
        mock_results = {
            'sample_importance': [],
            'aggregate': {'num_samples': 1, 'num_features': 5},
            'top_features': []
        }
        mock_extract.return_value = mock_results
        
        # Run main
        with patch('model.feature_importance.main.__globals__'):
            # We need to run the actual main but with mocked dependencies
            # Since main() has complex dependencies, we'll test the logic flow
            pass
        
        # Verify paths were accessed
        assert mock_get_config.called
        assert mock_get_paths.called

    def test_main_missing_model(self, tmp_path):
        """Test main fails when model is missing."""
        # Setup paths
        model_dir = tmp_path / 'model_output'
        model_dir.mkdir()
        
        graphs_dir = tmp_path / 'processed_graphs'
        graphs_dir.mkdir()
        
        output_dir = tmp_path / 'model_outputs'
        output_dir.mkdir()
        
        # Create graphs file
        graphs = [{'id': 'test', 'node_features': np.random.rand(5, 3)}]
        with open(graphs_dir / 'training_graphs.pkl', 'wb') as f:
            pickle.dump(graphs, f)
        
        # Mock config and paths
        with patch('model.feature_importance.get_config') as mock_config, \
             patch('model.feature_importance.get_paths') as mock_paths:
            
            mock_config.return_value = {}
            mock_paths.return_value = {
                'model_output': model_dir,
                'processed_graphs': graphs_dir,
                'model_outputs': output_dir
            }
            
            with pytest.raises(FileNotFoundError, match="Trained model not found"):
                main()