"""
SchNet-style Graph Neural Network for Transition State Barrier Prediction.

Implements a continuous-filter convolutional neural network as described in:
"SchNet: A Continuous-filter Convolutional Neural Network for Modeling Quantum Interactions"

Compatible with PyTorch Geometric and CPU execution.
"""
import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, radius_graph
from torch_geometric.typing import Adj, OptTensor

class GaussianSmearing(nn.Module):
    """
    Gaussian Smearing for distance expansion.
    
    Converts scalar distances into a vector of Gaussian features.
    """
    def __init__(
        self,
        start: float = 0.0,
        stop: float = 10.0,
        num_gaussians: int = 50
    ):
        super().__init__()
        self.start = start
        self.stop = stop
        self.num_gaussians = num_gaussians
        self.register_buffer(
            'offset',
            torch.linspace(start, stop, num_gaussians)
        )
        self.register_buffer(
            'delta',
            torch.tensor((stop - start) / (num_gaussians - 1))
        )

    def forward(self, dist: torch.Tensor) -> torch.Tensor:
        """
        Args:
            dist: Tensor of shape (num_edges,) containing distances.
        Returns:
            Tensor of shape (num_edges, num_gaussians).
        """
        dist = dist.unsqueeze(-1)
        return torch.exp(-((dist - self.offset) / self.delta) ** 2)


class ContinuousFilterConv(MessagePassing):
    """
    Continuous-Filter Convolution Layer.
    
    Computes edge weights via a learned MLP on distance features,
    then applies these weights to the message passing.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 5.0,
        activation: str = 'silu'
    ):
        super().__init__(aggr='add')
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.cutoff = cutoff

        # Distance expansion
        self.distance_expansion = GaussianSmearing(
            start=0.0, stop=cutoff, num_gaussians=num_gaussians
        )

        # Filter network (MLP)
        self.filter_net = nn.Sequential(
            nn.Linear(num_gaussians, num_gaussians),
            nn.SiLU() if activation == 'silu' else nn.ReLU(),
            nn.Linear(num_gaussians, out_channels)
        )

        # Node update network
        self.update_net = nn.Sequential(
            nn.Linear(in_channels + out_channels, out_channels),
            nn.SiLU() if activation == 'silu' else nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Adj,
        edge_attr: OptTensor = None,
        pos: OptTensor = None
    ) -> torch.Tensor:
        # Calculate distances if not provided (assuming 3D positions)
        if pos is not None:
            row, col = edge_index
            dist = (pos[row] - pos[col]).norm(dim=-1)
            # Apply cutoff mask
            mask = dist <= self.cutoff
            # Expand distances for Gaussian smearing
            dist_expanded = self.distance_expansion(dist)
            # Filter network to get edge weights
            edge_weights = self.filter_net(dist_expanded)
            # Apply mask to edge weights (set to zero if beyond cutoff)
            edge_weights = edge_weights * mask.unsqueeze(-1).to(edge_weights.dtype)
        else:
            # Fallback if edge_attr (pre-computed weights) is provided
            # This path is less common in standard SchNet but handles pre-processed graphs
            if edge_attr is None:
                raise ValueError("Either pos or edge_attr must be provided")
            edge_weights = edge_attr

        # Propagate messages
        out = self.propagate(
            edge_index,
            x=x,
            edge_weight=edge_weights,
            size=None
        )

        # Update node features
        out = self.update_net(torch.cat([x, out], dim=-1))
        return out

    def message(
        self,
        x_j: torch.Tensor,
        edge_weight: torch.Tensor
    ) -> torch.Tensor:
        # Element-wise multiplication of node feature with edge weight
        return x_j * edge_weight


class SchNetBlock(nn.Module):
    """
    A block of Continuous Filter Convolutions.
    """
    def __init__(
        self,
        hidden_channels: int,
        num_gaussians: int,
        cutoff: float = 5.0,
        activation: str = 'silu'
    ):
        super().__init__()
        self.conv = ContinuousFilterConv(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            num_gaussians=num_gaussians,
            cutoff=cutoff,
            activation=activation
        )
        self.norm = nn.LayerNorm(hidden_channels)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Adj,
        pos: torch.Tensor
    ) -> torch.Tensor:
        x_res = x
        x = self.conv(x, edge_index, pos=pos)
        x = self.norm(x)
        x = x + x_res
        return F.silu(x)


class SchNet(nn.Module):
    """
    SchNet Model for Transition State Barrier Prediction.
    
    Architecture:
    1. Embedding layer for atomic numbers.
    2. Stack of SchNetBlocks (Continuous Filter Convolutions).
    3. Readout layer (sum pooling) to get graph-level representation.
    4. Output MLP to predict energy/barrier.
    
    Args:
        atomic_number_range: Tuple (min, max) of atomic numbers.
        hidden_channels: Number of hidden channels in the GNN.
        num_filters: Number of filters in the distance MLP (same as num_gaussians).
        num_layers: Number of SchNet blocks.
        cutoff: Cutoff radius for interactions (Angstroms).
        output_dim: Dimension of the output (1 for scalar energy).
    """
    def __init__(
        self,
        atomic_number_range: Tuple[int, int] = (1, 30),
        hidden_channels: int = 128,
        num_filters: int = 50,
        num_layers: int = 4,
        cutoff: float = 5.0,
        output_dim: int = 1
    ):
        super().__init__()
        self.atomic_number_range = atomic_number_range
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers
        self.cutoff = cutoff

        # Embedding layer for atomic numbers
        self.num_atomic_types = atomic_number_range[1] - atomic_number_range[0] + 1
        self.embedding = nn.Embedding(self.num_atomic_types, hidden_channels)

        # SchNet blocks
        self.blocks = nn.ModuleList([
            SchNetBlock(
                hidden_channels=hidden_channels,
                num_gaussians=num_filters,
                cutoff=cutoff
            )
            for _ in range(num_layers)
        ])

        # Readout and prediction head
        self.readout = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.SiLU(),
            nn.Linear(hidden_channels, output_dim)
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Adj,
        pos: torch.Tensor,
        batch: OptTensor = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features (atomic numbers as indices) of shape (num_nodes,).
            edge_index: Edge indices of shape (2, num_edges).
            pos: Node positions of shape (num_nodes, 3).
            batch: Batch vector of shape (num_nodes,).
        
        Returns:
            Predicted scalar values (e.g., barrier height) of shape (num_graphs,).
        """
        # Normalize atomic numbers to indices 0..N
        atomic_indices = x - self.atomic_number_range[0]
        x = self.embedding(atomic_indices)

        # Pass through SchNet blocks
        for block in self.blocks:
            x = block(x, edge_index, pos)

        # Readout (sum pooling)
        if batch is None:
            # If no batch vector, assume single graph
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        
        graph_repr = torch_scatter.scatter(x, batch, dim=0, reduce='sum')
        
        # Predict
        out = self.readout(graph_repr)
        return out


# Helper for scatter if torch_scatter is not explicitly imported in environment
# We will implement a simple fallback or assume torch_geometric provides it
# torch_geometric.nn.pool usually relies on torch_scatter
try:
    from torch_scatter import scatter
except ImportError:
    # Fallback implementation if torch_scatter is missing (unlikely in standard GNN env)
    def scatter(src: torch.Tensor, index: torch.Tensor, dim: int = 0, reduce: str = 'sum') -> torch.Tensor:
        """Simple fallback scatter implementation for sum."""
        if reduce != 'sum':
            raise NotImplementedError("Fallback scatter only supports 'sum'")
        out = torch.zeros(
            index.max().item() + 1, src.size(-1),
            device=src.device, dtype=src.dtype
        )
        out = out.index_add_(dim, index, src)
        return out

# Patch the module if needed, but usually torch_scatter is available with torch_geometric
# For this implementation, we assume standard environment.
# If torch_scatter is not found, the import above handles it.

# Re-define the class to use the imported or fallback scatter
class SchNet(nn.Module):
    """
    SchNet Model for Transition State Barrier Prediction.
    """
    def __init__(
        self,
        atomic_number_range: Tuple[int, int] = (1, 30),
        hidden_channels: int = 128,
        num_filters: int = 50,
        num_layers: int = 4,
        cutoff: float = 5.0,
        output_dim: int = 1
    ):
        super().__init__()
        self.atomic_number_range = atomic_number_range
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers
        self.cutoff = cutoff

        self.num_atomic_types = atomic_number_range[1] - atomic_number_range[0] + 1
        self.embedding = nn.Embedding(self.num_atomic_types, hidden_channels)

        self.blocks = nn.ModuleList([
            SchNetBlock(
                hidden_channels=hidden_channels,
                num_gaussians=num_filters,
                cutoff=cutoff
            )
            for _ in range(num_layers)
        ])

        self.readout = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.SiLU(),
            nn.Linear(hidden_channels, output_dim)
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Adj,
        pos: torch.Tensor,
        batch: OptTensor = None
    ) -> torch.Tensor:
        atomic_indices = x - self.atomic_number_range[0]
        x = self.embedding(atomic_indices)

        for block in self.blocks:
            x = block(x, edge_index, pos)

        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        
        # Use the imported or fallback scatter
        graph_repr = scatter(x, batch, dim=0, reduce='sum')
        
        out = self.readout(graph_repr)
        return out

def get_model_config(hidden_channels: int = 128) -> dict:
    """
    Returns a configuration dictionary for the SchNet model.
    """
    return {
        "atomic_number_range": (1, 30),
        "hidden_channels": hidden_channels,
        "num_filters": 50,
        "num_layers": 4,
        "cutoff": 5.0,
        "output_dim": 1
    }
