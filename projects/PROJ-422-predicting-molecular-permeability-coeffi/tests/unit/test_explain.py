"""
Unit tests for code/analysis/explain.py.

Tests explainability functions (SHAP and GNNExplainer) using mock models
to ensure the logic runs without requiring full model training or real data.
"""
import pytest
import json
import numpy as np
import torch
import torch.nn as nn
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys
import os

# Add the project root to the path to allow relative imports
# Assuming tests/unit is at depth 2 from root, and code is at depth 1
# But the import structure in the project suggests we run from root
# and import code.*
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.explain import load_test_graphs_from_csv, explain_gnn, main
from code.models.gnn import MPNN
from code.models.rf import train_random_forest, predict
import pandas as pd

# ----------------------------------------------------------------------
# Fixtures / Mock Data Generators
# ----------------------------------------------------------------------

@pytest.fixture
def mock_rf_model():
    """Create a mock Random Forest model with a predict method."""
    model = MagicMock()
    model.predict = MagicMock(return_value=np.array([0.5, 0.6, 0.7]))
    model.feature_importances_ = np.array([0.1, 0.2, 0.3, 0.4])
    return model

@pytest.fixture
def mock_gnn_model():
    """Create a mock GNN model (MPNN) compatible with PyTorch Geometric."""
    # We need a mock that looks like an MPNN instance
    model = MagicMock(spec=MPNN)
    model.eval = MagicMock()
    # Mock forward to return a dummy tensor
    model.forward = MagicMock(return_value=torch.tensor([0.5, 0.6, 0.7]))
    return model

@pytest.fixture
def mock_test_graphs_data(tmp_path):
    """Generate a temporary CSV file with mock graph data for testing."""
    csv_path = tmp_path / "test_graphs.csv"
    data = {
        "smiles": ["CCO", "CCO", "CCO"],
        "node_features": [
            "[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]",
            "[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]",
            "[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]"
        ],
        "edge_index": [
            "[[0, 1, 1, 2], [1, 0, 2, 1]]",
            "[[0, 1, 1, 2], [1, 0, 2, 1]]",
            "[[0, 1, 1, 2], [1, 0, 2, 1]]"
        ],
        "target": [0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

# ----------------------------------------------------------------------
# Tests for load_test_graphs_from_csv
# ----------------------------------------------------------------------

def test_load_test_graphs_from_csv_success(mock_test_graphs_data):
    """Test that load_test_graphs_from_csv correctly parses the CSV."""
    graphs, targets = load_test_graphs_from_csv(str(mock_test_graphs_data))
    
    assert len(graphs) == 3
    assert len(targets) == 3
    assert targets[0] == 0.5
    # Verify that node_features and edge_index are parsed as lists
    assert isinstance(graphs[0]["node_features"], list)
    assert isinstance(graphs[0]["edge_index"], list)

def test_load_test_graphs_from_csv_missing_file():
    """Test that load_test_graphs_from_csv raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_test_graphs_from_csv("non_existent_path.csv")

# ----------------------------------------------------------------------
# Tests for explain_gnn (GNNExplainer logic)
# ----------------------------------------------------------------------

@patch("code.analysis.explain.MPNN")
def test_explain_gnn_basic_flow(mock_mpnn_class, mock_gnn_model, mock_test_graphs_data):
    """Test that explain_gnn runs the explanation loop without crashing."""
    # Setup mock for the class constructor if needed, or just use the instance
    # The function expects an MPNN instance, so we pass mock_gnn_model directly
    
    # Mock the internal logic that might try to load the model from disk
    # or perform complex graph operations
    with patch("code.analysis.explain.logger") as mock_logger:
        # We need to mock the GNNExplainer class if it's imported inside the function
        # or if the function instantiates it. Since the function signature is 
        # explain_gnn(model, graphs, targets), we assume it uses the model passed in.
        
        # Simulate the internal logic of explain_gnn
        # The function should iterate over graphs and generate importance scores
        
        # Mock the GNNExplainer if it's imported in the module
        with patch("code.analysis.explain.GNNExplainer") as MockGNNExplainer:
            mock_explainer_instance = MagicMock()
            # Mock explain_instance to return dummy node/edge masks
            mock_explainer_instance.explain = MagicMock(
                return_value=(
                    torch.tensor([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]), # node_mask
                    torch.tensor([[0.1], [0.2], [0.3], [0.4]])          # edge_mask
                )
            )
            MockGNNExplainer.return_value = mock_explainer_instance

            # Call the function
            result = explain_gnn(mock_gnn_model, str(mock_test_graphs_data))
            
            # Verify basic structure of the result
            assert "substructures" in result
            assert "importance_scores" in result
            assert len(result["substructures"]) > 0
            assert len(result["importance_scores"]) > 0

def test_explain_gnn_empty_graphs(mock_gnn_model, tmp_path):
    """Test explain_gnn with an empty CSV."""
    csv_path = tmp_path / "empty_graphs.csv"
    df = pd.DataFrame(columns=["smiles", "node_features", "edge_index", "target"])
    df.to_csv(csv_path, index=False)
    
    with patch("code.analysis.explain.logger"):
        with patch("code.analysis.explain.GNNExplainer"):
            result = explain_gnn(mock_gnn_model, str(csv_path))
            # Should handle empty input gracefully or return empty lists
            assert isinstance(result, dict)

# ----------------------------------------------------------------------
# Tests for main entry point
# ----------------------------------------------------------------------

@patch("code.analysis.explain.load_test_graphs_from_csv")
@patch("code.analysis.explain.explain_gnn")
@patch("code.analysis.explain.logger")
def test_main_execution(mock_logger, mock_explain_gnn, mock_load_graphs, mock_gnn_model, tmp_path):
    """Test the main function orchestrates the explainability pipeline."""
    # Setup mocks
    mock_load_graphs.return_value = (
        [{"node_features": [[1]], "edge_index": [[0], [1]]}], 
        [0.5]
    )
    mock_explain_gnn.return_value = {
        "substructures": ["aromatic_ring"],
        "importance_scores": [0.9]
    }
    
    # Create a temporary output path
    output_path = tmp_path / "gnn_importance.json"
    
    # Mock the model loading (assuming main loads the model from a path)
    # We need to patch the part of main that loads the model
    with patch("code.analysis.explain.create_mpnn_model") as mock_create_model:
        mock_create_model.return_value = mock_gnn_model
        
        # Mock sys.argv to simulate command line arguments
        original_argv = sys.argv
        sys.argv = ["test", str(tmp_path / "train_graphs.csv"), str(output_path)]
        
        try:
            # We need to patch the file writing part if it's not mocked by open
            with patch("builtins.open", mock_open()) as mock_file:
                main()
                
                # Verify that explain_gnn was called
                mock_explain_gnn.assert_called_once()
                # Verify that the result was written to the file
                assert mock_file.called
        finally:
            sys.argv = original_argv

# ----------------------------------------------------------------------
# Tests for SHAP integration (if applicable in explain.py)
# ----------------------------------------------------------------------
# Note: The current API surface for explain.py lists: load_test_graphs_from_csv, explain_gnn, main.
# It does NOT explicitly list explain_rf. However, the task description mentions 
# "mock models for explainability checks" which implies testing the logic that 
# might handle both or the specific GNN logic.
# If the actual implementation of explain.py includes SHAP logic for RF, 
# we would add tests for that here. Since the API surface only shows GNN functions,
# we focus on the GNN side. If the implementation file (omitted in prompt) 
# has RF logic, this test file would need to be extended to import and test it.
# For now, we assume the task is to test the exposed public API.

def test_import_structure():
    """Ensure the module can be imported and public names exist."""
    from code.analysis.explain import load_test_graphs_from_csv, explain_gnn, main
    assert callable(load_test_graphs_from_csv)
    assert callable(explain_gnn)
    assert callable(main)
    
def test_explain_gnn_error_handling(mock_gnn_model, tmp_path):
    """Test that explain_gnn handles invalid graph data gracefully."""
    csv_path = tmp_path / "bad_graphs.csv"
    # Create a CSV with malformed JSON in the features
    data = {
        "smiles": ["CCO"],
        "node_features": ["invalid_json"], 
        "edge_index": ["[0, 1]"],
        "target": [0.5]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    with patch("code.analysis.explain.logger") as mock_logger:
        with patch("code.analysis.explain.GNNExplainer"):
            # Should not crash, but might return empty or log an error
            result = explain_gnn(mock_gnn_model, str(csv_path))
            assert isinstance(result, dict)
            # Depending on implementation, it might return empty lists or partial results
            # The key is it shouldn't raise an unhandled exception