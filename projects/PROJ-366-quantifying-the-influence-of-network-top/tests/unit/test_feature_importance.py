"""
Unit tests for the feature importance extraction module (T032).
"""
import json
import os
import tempfile
from pathlib import Path
import pickle
import numpy as np
import pytest

# Import the module under test
from model.feature_importance import (
    load_trained_model,
    extract_node_features,
    extract_feature_importance,
    compute_shap_values
)
from model.gnn import StaticScatteringPotentialGNN

# Mock model for testing if SHAP is not available or for speed
class MockGNN:
    def __init__(self):
        self.eval_called = False
    
    def eval(self):
        self.eval_called = True
    
    def forward(self, x):
        # Return dummy predictions
        return np.ones(x.shape[0])

def test_extract_node_features():
    """Test that node features are extracted correctly."""
    graph_data = {
        'nodes': [
            {'id': 1, 'degree': 4, 'clustering_coeff': 0.5},
            {'id': 2, 'degree': 3, 'clustering_coeff': 0.2},
            {'id': 3, 'degree': 5, 'clustering_coeff': 0.8}
        ]
    }
    
    features = extract_node_features(graph_data)
    
    assert features.shape == (3, 2)
    assert np.allclose(features[0], [4.0, 0.5])
    assert np.allclose(features[1], [3.0, 0.2])
    assert np.allclose(features[2], [5.0, 0.8])

def test_extract_node_features_empty():
    """Test extraction on an empty graph."""
    graph_data = {'nodes': []}
    features = extract_node_features(graph_data)
    assert features.size == 0

def test_extract_feature_importance_integration(tmp_path):
    """
    Integration test for feature importance extraction.
    This test mocks the model to avoid dependency on a real trained model.
    """
    # Create temporary directories
    model_dir = tmp_path / "models"
    graphs_dir = tmp_path / "graphs"
    output_dir = tmp_path / "output"
    
    model_dir.mkdir()
    graphs_dir.mkdir()
    output_dir.mkdir()
    
    # Create a mock model
    mock_model = MockGNN()
    model_path = model_dir / "trained_gnn.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(mock_model, f)
    
    # Create mock graph files
    graph_data_1 = {
        'nodes': [
            {'id': 1, 'degree': 4, 'clustering_coeff': 0.5},
            {'id': 2, 'degree': 3, 'clustering_coeff': 0.2}
        ]
    }
    graph_data_2 = {
        'nodes': [
            {'id': 1, 'degree': 5, 'clustering_coeff': 0.8},
            {'id': 2, 'degree': 4, 'clustering_coeff': 0.3}
        ]
    }
    
    with open(graphs_dir / "graph_1.pkl", 'wb') as f:
        pickle.dump(graph_data_1, f)
    with open(graphs_dir / "graph_2.pkl", 'wb') as f:
        pickle.dump(graph_data_2, f)
    
    output_file = output_dir / "shap_values.npy"
    
    # Run the extraction
    # Note: This will fail if shap is not installed, which is expected behavior
    # for a real environment without dependencies.
    try:
        import shap
        output_path, metadata = extract_feature_importance(
            model_path=model_path,
            graphs_path=graphs_dir,
            output_path=output_file
        )
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify SHAP values shape
        shap_values = np.load(output_path)
        assert shap_values.shape[0] == 2 # 2 samples
        assert shap_values.shape[1] == 2 # 2 features (degree, clustering)
        
        # Verify metadata
        assert metadata['n_samples'] == 2
        assert metadata['n_features'] == 2
        
    except ImportError:
        # If shap is not installed, we expect the function to raise an error
        # as per the "Fail loudly" constraint.
        with pytest.raises(RuntimeError, match="SHAP library is required"):
            extract_feature_importance(
                model_path=model_path,
                graphs_path=graphs_dir,
                output_path=output_file
            )

def test_extract_feature_importance_file_exists(tmp_path):
    """Test that the output file is created."""
    model_dir = tmp_path / "models"
    graphs_dir = tmp_path / "graphs"
    output_dir = tmp_path / "output"
    
    model_dir.mkdir()
    graphs_dir.mkdir()
    output_dir.mkdir()
    
    # Create mock model and graphs as in previous test
    mock_model = MockGNN()
    model_path = model_dir / "trained_gnn.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(mock_model, f)
    
    graph_data = {
        'nodes': [
            {'id': 1, 'degree': 4, 'clustering_coeff': 0.5},
            {'id': 2, 'degree': 3, 'clustering_coeff': 0.2}
        ]
    }
    with open(graphs_dir / "graph_1.pkl", 'wb') as f:
        pickle.dump(graph_data, f)
    
    output_file = output_dir / "shap_values.npy"
    
    try:
        import shap
        extract_feature_importance(
            model_path=model_path,
            graphs_path=graphs_dir,
            output_path=output_file
        )
        
        # Assert file exists
        assert output_file.exists()
        assert np.load(output_file).shape[0] == 1
    except ImportError:
        # Expected if shap is not installed
        pass