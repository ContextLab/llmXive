import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from analysis.ablation import (
    extract_composition_features,
    train_composition_only_baseline,
    evaluate_full_gnn_on_test,
    run_ablation_study,
    AblationResult,
    CompositionOnlyNN
)

@pytest.fixture
def sample_graph():
    """Create a sample graph dictionary for testing."""
    return {
        'id': 'test_001',
        'composition': {'C': 1, 'Si': 2},
        'target_moduli': np.array([100.0, 50.0, 0.3]),
        'node_features': np.random.rand(3, 10),
        'edge_features': np.random.rand(5, 5),
        'family_id': 'graphene_family'
    }

@pytest.fixture
def sample_graphs(sample_graph):
    """Create a list of sample graphs."""
    return [sample_graph] * 10

@pytest.fixture
def train_test_ids():
    """Return train and test IDs."""
    return (['test_001'] * 7, ['test_001'] * 3)

def test_extract_composition_features():
    """Test that extract_composition_features returns a valid feature vector."""
    graph = {
        'composition': {'C': 2, 'Si': 1, 'O': 3}
    }
    
    features = extract_composition_features(graph)
    
    # Check that features is a numpy array
    assert isinstance(features, np.ndarray)
    
    # Check that features has the expected length (7 features + 4 normalized counts = 11)
    # Actually, the implementation returns 10 features: [num_elements, total_atoms, mean, std, min, max, 4 normalized]
    assert len(features) == 10
    
    # Check that features are finite
    assert np.all(np.isfinite(features))
    
    # Check that num_elements is correct
    assert features[0] == 3  # C, Si, O
    
    # Check that total_atoms is correct
    assert features[1] == 6  # 2 + 1 + 3

def test_extract_composition_features_empty():
    """Test extract_composition_features with empty composition."""
    graph = {
        'composition': {}
    }
    
    features = extract_composition_features(graph)
    
    assert isinstance(features, np.ndarray)
    assert len(features) == 10
    assert np.all(features == 0)

def test_composition_only_nn_forward():
    """Test the forward pass of the CompositionOnlyNN model."""
    model = CompositionOnlyNN(input_dim=10, hidden_dim=64, output_dim=3)
    
    x = torch.randn(1, 10)
    output = model(x)
    
    assert output.shape == (1, 3)

def test_train_composition_only_baseline(sample_graphs, train_test_ids):
    """Test training the composition-only baseline model."""
    train_ids, test_ids = train_test_ids
    
    # Mock the Config to avoid file loading
    with patch('analysis.ablation.Config') as mock_config:
        mock_config.return_value = MagicMock()
        
        model, metrics = train_composition_only_baseline(
            sample_graphs, train_ids, test_ids, mock_config.return_value
        )
    
    # Check that model is a CompositionOnlyNN instance
    assert isinstance(model, CompositionOnlyNN)
    
    # Check that metrics is a dictionary
    assert isinstance(metrics, dict)
    
    # Check that metrics contains expected keys
    assert 'final_mape' in metrics
    assert 'final_rmse' in metrics
    assert 'training_epochs' in metrics
    assert 'best_val_loss' in metrics
    
    # Check that MAPE is a reasonable value (between 0 and 1000)
    assert 0 <= metrics['final_mape'] <= 1000

def test_run_ablation_study_with_mock_gnn(sample_graphs, train_test_ids):
    """Test running the ablation study with a mock GNN model."""
    train_ids, test_ids = train_test_ids
    
    # Create a mock GNN model that returns a fixed MAPE
    mock_gnn_model = {'mape': 5.0}
    
    result = run_ablation_study(
        sample_graphs, train_ids, test_ids, mock_gnn_model
    )
    
    # Check that result is an AblationResult
    assert isinstance(result, AblationResult)
    
    # Check that full_gnn_mape is the mocked value
    assert result.full_gnn_mape == 5.0
    
    # Check that composition_only_mape is a reasonable value
    assert 0 <= result.composition_only_mape <= 1000
    
    # Check that delta is calculated correctly
    expected_delta = result.composition_only_mape - result.full_gnn_mape
    assert np.isclose(result.delta, expected_delta)

def test_run_ablation_study_without_gnn_raises_error(sample_graphs, train_test_ids):
    """Test that run_ablation_study raises an error when no GNN model is provided."""
    train_ids, test_ids = train_test_ids
    
    with pytest.raises(ValueError, match="GNN model must be provided"):
        run_ablation_study(sample_graphs, train_ids, test_ids, None)

def test_evaluate_full_gnn_on_test_with_mock():
    """Test evaluate_full_gnn_on_test with a mock model."""
    graphs = [{'id': 'test_001', 'target_moduli': np.array([100.0, 50.0, 0.3])}]
    test_ids = ['test_001']
    mock_model = {'mape': 10.0}
    
    mape = evaluate_full_gnn_on_test(mock_model, graphs, test_ids)
    
    assert mape == 10.0

def test_evaluate_full_gnn_on_test_without_model_raises_error():
    """Test that evaluate_full_gnn_on_test raises an error when model is None."""
    graphs = [{'id': 'test_001', 'target_moduli': np.array([100.0, 50.0, 0.3])}]
    test_ids = ['test_001']
    
    with pytest.raises(ValueError, match="Model is None"):
        evaluate_full_gnn_on_test(None, graphs, test_ids)

# Import torch for the tests that need it
import torch

if __name__ == "__main__":
    pytest.main([__file__, "-v"])