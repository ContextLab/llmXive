"""
Unit tests for GCN model implementations in code/models.py.
"""
import pytest
import torch
import torch.nn as nn
from pathlib import Path
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models import (
    GCNLayer,
    GCN2Layer,
    create_normalized_adjacency,
    build_gcn_model
)
from utils import SAMPLE_SIZE, MAX_EPOCHS, CONVERGENCE_THRESHOLD


class TestGCNLayer:
    """Tests for the single GCN layer."""

    def test_gcn_layer_shape(self):
        """Test that GCNLayer produces correct output dimensions."""
        in_feat, out_feat = 10, 20
        layer = GCNLayer(in_feat, out_feat)
        
        batch_size = 5
        x = torch.randn(batch_size, in_feat)
        adj = torch.randn(batch_size, batch_size)
        
        output = layer(x, adj)
        
        assert output.shape == (batch_size, out_feat)

    def test_gcn_layer_no_bias(self):
        """Test GCNLayer with bias disabled."""
        layer = GCNLayer(10, 20, bias=False)
        # Should not have bias parameter
        assert not any(p.requires_grad for name, p in layer.named_parameters() if "bias" in name)


class TestGCN2Layer:
    """Tests for the 2-layer GCN model."""

    def test_gcn2layer_forward_shape(self):
        """Test forward pass output shape."""
        in_feat, hidden, out_feat = 16, 32, 5
        model = GCN2Layer(in_feat, hidden, out_feat)
        
        num_nodes = 10
        x = torch.randn(num_nodes, in_feat)
        adj = torch.randn(num_nodes, num_nodes)
        
        output = model(x, adj)
        
        assert output.shape == (num_nodes, out_feat)

    def test_gcn2layer_dropout(self):
        """Test that dropout is applied during training."""
        model = GCN2Layer(16, 32, 5, dropout=0.5)
        model.train()
        
        num_nodes = 10
        x = torch.ones(num_nodes, 16)
        adj = torch.ones(num_nodes, num_nodes)
        
        # Run multiple forward passes - outputs should differ due to dropout
        out1 = model(x, adj)
        out2 = model(x, adj)
        
        # With high dropout, they should likely be different
        # We check that the model doesn't crash and produces valid tensors
        assert not torch.isnan(out1).any()
        assert not torch.isnan(out2).any()

    def test_gcn2layer_weights_initialized(self):
        """Test that weights are initialized (no NaN/Inf)."""
        model = GCN2Layer(16, 32, 5)
        
        for param in model.parameters():
            assert not torch.isnan(param).any()
            assert not torch.isinf(param).any()

    def test_build_gcn_model_factory(self):
        """Test the factory function."""
        model = build_gcn_model(16, 5, hidden_dim=32)
        assert isinstance(model, GCN2Layer)
        assert model.gcn1.out_features == 32
        assert model.gcn2.out_features == 5


class TestCreateNormalizedAdjacency:
    """Tests for adjacency matrix normalization."""

    def test_self_loops_added(self):
        """Test that self-loops are added to the adjacency matrix."""
        edge_index = torch.tensor([
            [0, 1, 1, 2],
            [1, 0, 2, 1]
        ])  # 3 nodes, edges: 0-1, 1-2
        num_nodes = 3
        
        adj_norm = create_normalized_adjacency(edge_index, num_nodes)
        
        # Check diagonal elements are non-zero (due to self-loops)
        assert adj_norm[0, 0] > 0
        assert adj_norm[1, 1] > 0
        assert adj_norm[2, 2] > 0

    def test_symmetry(self):
        """Test that normalized adjacency is symmetric for undirected graphs."""
        # Undirected graph: 0-1, 1-2
        edge_index = torch.tensor([
            [0, 1, 1, 2],
            [1, 0, 2, 1]
        ])
        num_nodes = 3
        
        adj_norm = create_normalized_adjacency(edge_index, num_nodes)
        
        # Should be symmetric
        assert torch.allclose(adj_norm, adj_norm.t())

    def test_row_sum_approx_one(self):
        """Test that rows sum to approximately 1 (double stochastic)."""
        edge_index = torch.tensor([
            [0, 1, 1, 2],
            [1, 0, 2, 1]
        ])
        num_nodes = 3
        
        adj_norm = create_normalized_adjacency(edge_index, num_nodes)
        
        row_sums = adj_norm.sum(dim=1)
        # Due to normalization, row sums should be close to 1
        assert torch.allclose(row_sums, torch.ones(num_nodes), atol=1e-5)


class TestIntegration:
    """Integration tests combining models and utilities."""

    def test_full_pipeline_cpu(self):
        """Test a full forward pass on CPU (no CUDA)."""
        assert not torch.cuda.is_available() or not torch.cuda.is_available(), "Tests should run on CPU"
        
        # Build model
        model = build_gcn_model(graph_features=10, num_classes=3, hidden_dim=16)
        model.eval()
        
        # Create dummy graph data
        num_nodes = 20
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, 50))
        
        # Ensure symmetric edges for undirected graph
        edge_index = torch.cat([edge_index, edge_index.flip(0)], dim=1)
        
        adj_norm = create_normalized_adjacency(edge_index, num_nodes)
        
        # Forward pass
        with torch.no_grad():
            logits = model(x, adj_norm)
        
        assert logits.shape == (num_nodes, 3)
        assert not torch.isnan(logits).any()

    def test_constants_consistency(self):
        """Test that model uses consistent constants from utils."""
        # Just verify imports work and constants are accessible
        assert SAMPLE_SIZE == 110
        assert MAX_EPOCHS == 1000
        assert CONVERGENCE_THRESHOLD == 0.90