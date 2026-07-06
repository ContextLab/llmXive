"""
Unit tests for SchNet architecture initialization and basic forward pass.
"""
import pytest
import torch
from torch_geometric.data import Data
from src.models.schnet import SchNet, GaussianSmearing, ContinuousFilterConv

class TestGaussianSmearing:
    def test_output_shape(self):
        smearing = GaussianSmearing(start=0.0, stop=10.0, num_gaussians=50)
        dist = torch.tensor([1.0, 2.0, 3.0])
        out = smearing(dist)
        assert out.shape == (3, 50)

    def test_values_positive(self):
        smearing = GaussianSmearing()
        dist = torch.tensor([5.0])
        out = smearing(dist)
        assert torch.all(out > 0)


class TestSchNetArchitecture:
    @pytest.fixture
    def simple_graph(self):
        """Create a simple dummy graph for testing."""
        # 4 nodes, 2 edges
        x = torch.tensor([1, 2, 3, 4], dtype=torch.long) # Atomic numbers
        edge_index = torch.tensor([
            [0, 1, 2],
            [1, 2, 3]
        ])
        pos = torch.tensor([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [4.5, 0.0, 0.0]
        ], dtype=torch.float)
        batch = torch.tensor([0, 0, 0, 0], dtype=torch.long)
        return x, edge_index, pos, batch

    def test_init(self):
        model = SchNet()
        assert model.hidden_channels == 128
        assert model.num_layers == 4

    def test_forward_pass(self, simple_graph):
        x, edge_index, pos, batch = simple_graph
        model = SchNet()
        model.eval()
        
        with torch.no_grad():
            out = model(x, edge_index, pos, batch)
        
        assert out.shape == (1, 1) # 1 graph, 1 output dim
        assert not torch.isnan(out).any()
        assert not torch.isinf(out).any()

    def test_multi_graph_batch(self):
        """Test forward pass with multiple graphs in a batch."""
        # Graph 1: 2 nodes
        # Graph 2: 2 nodes
        x = torch.tensor([1, 2, 3, 4], dtype=torch.long)
        edge_index = torch.tensor([
            [0, 2], # Edge in graph 1
            [1, 3]  # Edge in graph 2
        ])
        pos = torch.tensor([
            [0.0, 0.0, 0.0], [1.5, 0.0, 0.0], # Graph 1
            [0.0, 0.0, 0.0], [1.5, 0.0, 0.0]  # Graph 2
        ], dtype=torch.float)
        batch = torch.tensor([0, 0, 1, 1], dtype=torch.long)

        model = SchNet()
        model.eval()
        
        with torch.no_grad():
            out = model(x, edge_index, pos, batch)
        
        assert out.shape == (2, 1) # 2 graphs

class TestContinuousFilterConv:
    def test_forward(self):
        # Dummy inputs
        x = torch.randn(4, 128)
        edge_index = torch.tensor([
            [0, 1, 2, 3],
            [1, 2, 3, 0]
        ])
        pos = torch.randn(4, 3)

        conv = ContinuousFilterConv(
            in_channels=128,
            out_channels=128,
            num_gaussians=50,
            cutoff=5.0
        )

        out = conv(x, edge_index, pos=pos)
        assert out.shape == x.shape