"""
Unit tests for code/models/gnn.py and code/models/rf.py.
Tests forward pass, shape checks, and basic functionality.
"""
import pytest
import torch
import numpy as np
import pandas as pd
import joblib
import tempfile
import os
from pathlib import Path

# Import from the project's model modules
from models.gnn import MPNNLayer, MPNN, create_mpnn_model, train_epoch, validate_epoch
from models.rf import train_random_forest, predict, evaluate_model


class TestMPNNLayer:
    """Tests for the MPNNLayer class."""

    def test_forward_pass_shape(self):
        """Test that forward pass produces correct output shapes."""
        # Create dummy input data
        batch_size = 4
        num_nodes = 10
        in_features = 64
        out_features = 128

        # Create a simple MPNNLayer
        layer = MPNNLayer(in_features, out_features)

        # Create dummy node features (batch_size * num_nodes, in_features)
        x = torch.randn(batch_size * num_nodes, in_features)

        # Create dummy edge index (2, num_edges)
        num_edges = 20
        edge_index = torch.randint(0, num_nodes, (2, num_edges * batch_size))

        # Adjust edge_index for batch
        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        # Forward pass
        out = layer(x, batch_edge_index)

        # Check output shape
        assert out.shape == (batch_size * num_nodes, out_features)

    def test_forward_pass_with_edge_features(self):
        """Test forward pass with edge features."""
        in_features = 32
        out_features = 64
        edge_dim = 16

        layer = MPNNLayer(in_features, out_features, edge_dim=edge_dim)

        batch_size = 2
        num_nodes = 5
        x = torch.randn(batch_size * num_nodes, in_features)

        num_edges = 8
        edge_index = torch.randint(0, num_nodes, (2, num_edges * batch_size))

        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        edge_attr = torch.randn(num_edges * batch_size, edge_dim)

        out = layer(x, batch_edge_index, edge_attr)

        assert out.shape == (batch_size * num_nodes, out_features)


class TestMPNN:
    """Tests for the full MPNN model."""

    def test_create_mpnn_model(self):
        """Test model creation with default parameters."""
        model = create_mpnn_model(
            input_dim=64,
            hidden_dim=128,
            output_dim=1,
            num_layers=3
        )

        assert isinstance(model, MPNN)
        assert len(model.layers) == 3

    def test_forward_pass_full_model(self):
        """Test full model forward pass."""
        model = create_mpnn_model(
            input_dim=64,
            hidden_dim=128,
            output_dim=1,
            num_layers=2
        )

        batch_size = 4
        num_nodes = 10
        x = torch.randn(batch_size * num_nodes, 64)

        # Create batch vector
        batch = torch.repeat_interleave(
            torch.arange(batch_size),
            num_nodes
        )

        # Create edge index
        num_edges = 20
        edge_index = torch.randint(0, num_nodes, (2, num_edges * batch_size))

        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        out = model(x, batch_edge_index, batch)

        # Output should be (batch_size, output_dim)
        assert out.shape == (batch_size, 1)

    def test_forward_pass_with_graph_level_output(self):
        """Test model with graph-level pooling."""
        model = create_mpnn_model(
            input_dim=32,
            hidden_dim=64,
            output_dim=3,
            num_layers=2,
            pooling="mean"
        )

        batch_size = 2
        num_nodes = 8
        x = torch.randn(batch_size * num_nodes, 32)
        batch = torch.repeat_interleave(
            torch.arange(batch_size),
            num_nodes
        )

        num_edges = 12
        edge_index = torch.randint(0, num_nodes, (2, num_edges * batch_size))

        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        out = model(x, batch_edge_index, batch)

        assert out.shape == (batch_size, 3)


class TestMPNNEvaluation:
    """Tests for MPNN training and validation functions."""

    def test_train_epoch_returns_loss(self):
        """Test that train_epoch returns a loss value."""
        model = create_mpnn_model(64, 128, 1, 2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        batch_size = 4
        num_nodes = 10
        x = torch.randn(batch_size * num_nodes, 64)
        batch = torch.repeat_interleave(torch.arange(batch_size), num_nodes)
        edge_index = torch.randint(0, num_nodes, (2, 20 * batch_size))

        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        y = torch.randn(batch_size, 1)

        loss = train_epoch(model, x, batch_edge_index, batch, y, optimizer)

        assert isinstance(loss, float)
        assert loss >= 0

    def test_validate_epoch_returns_metrics(self):
        """Test that validate_epoch returns metrics."""
        model = create_mpnn_model(64, 128, 1, 2)

        batch_size = 4
        num_nodes = 10
        x = torch.randn(batch_size * num_nodes, 64)
        batch = torch.repeat_interleave(torch.arange(batch_size), num_nodes)
        edge_index = torch.randint(0, num_nodes, (2, 20 * batch_size))

        batch_edge_index = []
        for b in range(batch_size):
            offset = b * num_nodes
            batch_edge_index.append(edge_index + offset)
        batch_edge_index = torch.cat(batch_edge_index, dim=1)

        y = torch.randn(batch_size, 1)

        metrics = validate_epoch(model, x, batch_edge_index, batch, y)

        assert isinstance(metrics, dict)
        assert "loss" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics


class TestRandomForest:
    """Tests for Random Forest functions."""

    def test_train_random_forest(self):
        """Test training a Random Forest model."""
        # Create dummy data
        n_samples = 100
        n_features = 20
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)

        model = train_random_forest(X, y)

        assert model is not None
        assert hasattr(model, "predict")

    def test_predict(self):
        """Test prediction with Random Forest."""
        n_samples = 100
        n_features = 20
        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randn(n_samples)

        model = train_random_forest(X_train, y_train)

        X_test = np.random.randn(10, n_features)
        predictions = predict(model, X_test)

        assert predictions.shape == (10,)
        assert isinstance(predictions, np.ndarray)

    def test_evaluate_model(self):
        """Test model evaluation."""
        n_samples = 100
        n_features = 20
        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randn(n_samples)

        model = train_random_forest(X_train, y_train)

        X_test = np.random.randn(20, n_features)
        y_test = np.random.randn(20)

        metrics = evaluate_model(model, X_test, y_test)

        assert isinstance(metrics, dict)
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r2" in metrics

    def test_model_serialization(self):
        """Test that RF model can be saved and loaded."""
        n_samples = 50
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)

        model = train_random_forest(X, y)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as f:
            temp_path = f.name

        try:
            joblib.dump(model, temp_path)
            loaded_model = joblib.load(temp_path)

            X_test = np.random.randn(5, n_features)
            original_pred = predict(model, X_test)
            loaded_pred = predict(loaded_model, X_test)

            np.testing.assert_array_almost_equal(original_pred, loaded_pred)
        finally:
            os.unlink(temp_path)

    def test_evaluate_model_with_pandas(self):
        """Test evaluation with pandas DataFrames."""
        n_samples = 50
        n_features = 10
        X_train = pd.DataFrame(np.random.randn(n_samples, n_features))
        y_train = pd.Series(np.random.randn(n_samples))

        model = train_random_forest(X_train, y_train)

        X_test = pd.DataFrame(np.random.randn(10, n_features))
        y_test = pd.Series(np.random.randn(10))

        metrics = evaluate_model(model, X_test, y_test)

        assert isinstance(metrics, dict)
        assert "rmse" in metrics

class TestIntegration:
    """Integration tests for model components."""

    def test_gnn_rf_pipeline_consistency(self):
        """Test that both models can process similar data structures."""
        # GNN model
        gnn_model = create_mpnn_model(10, 20, 1, 2)

        # RF model
        X = np.random.randn(50, 10)
        y = np.random.randn(50)
        rf_model = train_random_forest(X, y)

        # Both should be callable
        assert gnn_model is not None
        assert rf_model is not None

    def test_model_parameter_count(self):
        """Test that GNN model has reasonable parameter count."""
        model = create_mpnn_model(64, 128, 1, 3)
        total_params = sum(p.numel() for p in model.parameters())

        assert total_params > 0
        # Should not be excessively large for CPU training
        assert total_params < 1000000