"""
SchNet-style GNN architecture for transition metal catalysis.
CPU-compatible implementation using PyTorch Geometric.
"""
import math
from typing import Optional, Tuple, Dict, Any, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops
from torch import Tensor

# Import config for hyperparameters if needed, though defaults are provided here
# from src.utils.config import get_config_value


class GaussianSmearing(nn.Module):
    """
    Gaussian radial basis function expansion for edge distances.
    Maps continuous distances to a fixed-size vector of Gaussian features.
    """
    def __init__(self, start: float = 0.0, stop: float = 5.0, num_gaussians: int = 50):
        super().__init__()
        self.start = start
        self.stop = stop
        self.num_gaussians = num_gaussians
        
        # Create centers for Gaussians
        offset = torch.linspace(start, stop, num_gaussians)
        self.coeffs = -1.0 / (offset[1] - offset[0])**2
        self.register_buffer('offset', offset)

    def forward(self, dist: Tensor) -> Tensor:
        """
        Args:
            dist: Tensor of shape (E,) where E is number of edges.
        Returns:
            Tensor of shape (E, num_gaussians)
        """
        # dist.unsqueeze(1) -> (E, 1)
        # offset -> (num_gaussians,)
        # diff -> (E, num_gaussians)
        diff = dist.unsqueeze(1) - self.offset
        # exp(coeffs * diff^2)
        out = torch.exp(self.coeffs * (diff ** 2))
        return out


class ContinuousFilterConv(MessagePassing):
    """
    Continuous-filter convolution layer as described in SchNet.
    Updates node embeddings based on edge distances and neighbor features.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 5.0,
        activation: Optional[nn.Module] = None,
    ):
        super().__init__(aggr='add')  # Sum aggregation
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_gaussians = num_gaussians
        self.cutoff = cutoff

        self.lin = nn.Linear(in_channels, out_channels, bias=False)
        
        # Filter network: maps Gaussian features to (out_channels, in_channels)
        self.filter_net = nn.Sequential(
            nn.Linear(num_gaussians, num_gaussians),
            nn.Softplus(),
            nn.Linear(num_gaussians, out_channels * in_channels),
        )

        self.activation = activation if activation else nn.Softplus()

    def forward(
        self,
        x: Tensor,
        edge_index: Tensor,
        edge_attr: Tensor,
        edge_weight: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Args:
            x: Node features (N, in_channels)
            edge_index: (2, E)
            edge_attr: Gaussian expansion of distances (E, num_gaussians)
            edge_weight: Optional scalar weights for edges
        """
        # Project node features
        x_proj = self.lin(x)
        
        # Generate filters from edge attributes
        # filter_weights shape: (E, out_channels, in_channels)
        filter_weights = self.filter_net(edge_attr).view(
            -1, self.out_channels, self.in_channels
        )

        # Apply message passing
        # We need to multiply x_proj[i] by filter_weights[j] for each edge j: i->k
        # Message: x_proj[source] * filter
        
        # To do this efficiently with MessagePassing:
        # We pass x_proj as x, and filter_weights as a secondary argument
        # But standard MessagePassing doesn't support matrix mult in message directly.
        # Alternative: Compute messages explicitly or use a custom implementation.
        # Here we implement the message function manually to handle the tensor shapes.
        
        row, col = edge_index
        
        # Get source node features
        x_source = x_proj[row] # (E, in_channels)
        
        # Expand filter weights to (E, out_channels, in_channels)
        # We want to compute: sum_over_neighbors ( x_source * filter_weights )
        # Result shape per node: (out_channels)
        
        # Reshape for batched matrix multiplication
        # x_source: (E, in_channels, 1)
        # filter_weights: (E, out_channels, in_channels)
        # We want (E, out_channels) = sum over in_channels of (x_source * filter_weights)
        
        # Efficiently: (E, out_channels, in_channels) @ (E, in_channels, 1) -> (E, out_channels, 1)
        # Then squeeze
        messages = torch.bmm(filter_weights, x_source.unsqueeze(2)).squeeze(2) # (E, out_channels)
        
        # Update aggregation
        out = self.propagate(edge_index, x=messages, edge_weight=edge_weight, size=(x.size(0), x.size(0)))
        
        return out

    def message(self, x_j: Tensor, edge_weight: Optional[Tensor]) -> Tensor:
        if edge_weight is not None:
            x_j = x_j * edge_weight.view(-1, 1)
        return x_j

    def update(self, aggr_out: Tensor) -> Tensor:
        if self.activation is not None:
            aggr_out = self.activation(aggr_out)
        return aggr_out


class SchNetBlock(nn.Module):
    """
    A block of SchNet layers.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 5.0,
        activation: Optional[nn.Module] = None,
    ):
        super().__init__()
        self.conv = ContinuousFilterConv(
            in_channels, out_channels, num_gaussians, cutoff, activation
        )
        self.act = activation if activation else nn.Softplus()

    def forward(
        self,
        x: Tensor,
        edge_index: Tensor,
        edge_attr: Tensor,
    ) -> Tensor:
        out = self.conv(x, edge_index, edge_attr)
        return out


class SchNet(nn.Module):
    """
    SchNet model for predicting scalar properties (e.g., barrier heights) from graphs.
    """
    def __init__(
        self,
        num_atom_types: int = 100,
        embedding_dim: int = 128,
        num_filters: int = 128,
        num_interactions: int = 3,
        num_gaussians: int = 50,
        cutoff: float = 5.0,
        output_dim: int = 1,
    ):
        super().__init__()
        self.num_atom_types = num_atom_types
        self.embedding_dim = embedding_dim
        self.num_filters = num_filters
        self.num_interactions = num_interactions
        self.num_gaussians = num_gaussians
        self.cutoff = cutoff
        self.output_dim = output_dim

        # Atom embedding
        self.embedding = nn.Embedding(num_atom_types, embedding_dim)

        # Gaussian smearing
        self.smearing = GaussianSmearing(0.0, cutoff, num_gaussians)

        # Interaction blocks
        self.interactions = nn.ModuleList()
        for _ in range(num_interactions):
            self.interactions.append(
                SchNetBlock(embedding_dim, embedding_dim, num_gaussians, cutoff)
            )

        # Output network
        self.output_net = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.Softplus(),
            nn.Linear(embedding_dim, output_dim),
        )

    def forward(
        self,
        x: Tensor,
        edge_index: Tensor,
        edge_attr: Tensor,
        batch: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Args:
            x: Atomic numbers (N,) or node features
            edge_index: (2, E)
            edge_attr: Gaussian expanded distances (E, num_gaussians)
            batch: Graph assignment vector (N,) for pooling
        Returns:
            Predicted property (num_graphs,) or (num_graphs, output_dim)
        """
        # Embed atoms
        if x.dim() == 1:
            x = self.embedding(x)
        else:
            x = x.float() # Assume already embedded if 2D

        # Apply interactions
        for interaction in self.interactions:
            x = x + interaction(x, edge_index, edge_attr)

        # Global pooling
        if batch is None:
            # If no batch provided, assume single graph
            # Sum or mean over all nodes
            out = x.sum(dim=0, keepdim=True)
        else:
            # Use scatter add for graph-level representation
            # torch_geometric.nn.pool.global_add_pool is usually used, but here we do it manually
            # to avoid extra imports if not available in strict environment
            from torch_scatter import scatter_add
            out = scatter_add(x, batch, dim=0)

        # Predict property
        out = self.output_net(out)
        return out


def get_model_config() -> Dict[str, Any]:
    """
    Returns default configuration for SchNet model.
    These values can be overridden by loading config from YAML.
    """
    return {
        "num_atom_types": 100,
        "embedding_dim": 128,
        "num_filters": 128,
        "num_interactions": 3,
        "num_gaussians": 50,
        "cutoff": 5.0,
        "output_dim": 1,
    }