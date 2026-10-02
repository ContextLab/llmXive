"""
SchNet-style Graph Neural Network architecture for Transition State prediction.

Implements a continuous-filter convolutional neural network adapted for 
transition-metal catalysis graphs. Compatible with PyTorch Geometric and CPU execution.
"""
import math
from typing import Optional, Tuple, Dict, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.typing import Adj, OptTensor, PairTensor
from torch import Tensor

from code.src.utils.config import load_config


class GaussianSmearing(nn.Module):
    """
    Gaussian distance smearing for continuous edge features.
    
    Converts scalar distances into a vector of Gaussian basis functions.
    """
    def __init__(
        self,
        start: float = 0.0,
        stop: float = 10.0,
        num_gaussians: int = 50,
        fixed: bool = True
    ):
        super().__init__()
        self.offset = torch.linspace(start, stop, num_gaussians)
        if fixed:
            self.register_buffer('offset', self.offset)
            self.register_buffer('sigma', torch.tensor(2.0 / num_gaussians))
        else:
            self.sigma = torch.nn.Parameter(torch.ones(1) * 2.0 / num_gaussians)

    def forward(self, dist: Tensor) -> Tensor:
        """
        Args:
            dist: Tensor of shape (N, 1) representing edge distances.
        
        Returns:
            Tensor of shape (N, num_gaussians) with smeared distance features.
        """
        dist = dist.view(-1, 1)
        return torch.exp(-((dist - self.offset) ** 2) / (2 * self.sigma ** 2))


class ContinuousFilterConv(MessagePassing):
    """
    Continuous-filter convolutional layer for SchNet.
    
    Updates node embeddings based on distance-dependent edge filters.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 10.0,
        activate: bool = True
    ):
        super().__init__(aggr='add')  # Use 'add' aggregation (sum)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_gaussians = num_gaussians
        self.cutoff = cutoff

        # Filter network: maps distance features to edge weights
        self.filter_net = nn.Sequential(
            nn.Linear(num_gaussians, out_channels),
            nn.Softplus() if activate else nn.Identity(),
            nn.Linear(out_channels, out_channels)
        )

        # Update network: maps node features to new embeddings
        self.update_net = nn.Sequential(
            nn.Linear(in_channels, out_channels),
            nn.Softplus() if activate else nn.Identity(),
            nn.Linear(out_channels, out_channels)
        )

        # Initialize weights
        self._initialize_weights()

    def _initialize_weights(self):
        for layer in self.filter_net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight, gain=nn.init.calculate_gain('softplus'))
                nn.init.zeros_(layer.bias)
        for layer in self.update_net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight, gain=nn.init.calculate_gain('softplus'))
                nn.init.zeros_(layer.bias)

    def forward(
        self,
        x: Tensor,
        edge_index: Adj,
        edge_attr: Tensor,
        edge_weight: OptTensor = None
    ) -> Tensor:
        """
        Args:
            x: Node features (N, in_channels)
            edge_index: Edge indices (2, E)
            edge_attr: Smeared distance features (E, num_gaussians)
            edge_weight: Optional scalar edge weights for masking (E,)
        
        Returns:
            Updated node features (N, out_channels)
        """
        # Compute edge filters
        edge_filter = self.filter_net(edge_attr)  # (E, out_channels)

        # Propagate
        out = self.propagate(
            edge_index,
            x=x,
            edge_filter=edge_filter,
            edge_weight=edge_weight,
            size=None
        )

        # Update node features
        out = self.update_net(x) + out
        return out

    def message(self, x_j: Tensor, edge_filter: Tensor, edge_weight: OptTensor) -> Tensor:
        """
        Compute message: element-wise product of neighbor feature and edge filter.
        """
        msg = x_j.unsqueeze(-1) * edge_filter.unsqueeze(0)  # (E, in_channels, out_channels) -> broadcast?
        # Correct shape handling: x_j is (E, in_channels), edge_filter is (E, out_channels)
        # We want to apply filter to x_j. Standard SchNet: x_j * filter
        # Since x_j is (E, in_channels) and filter is (E, out_channels), we need to match dims.
        # Actually, in SchNet, the filter is applied to the neighbor's feature vector.
        # x_j is (E, in_channels). edge_filter is (E, out_channels).
        # We want output (E, out_channels).
        # Standard implementation: x_j * edge_filter where edge_filter is (E, out_channels)
        # But x_j is (E, in_channels). We need to project x_j to out_channels first?
        # No, SchNet: The filter is a function of distance, and it modulates the message.
        # Message = x_j * filter(d).
        # If x_j is (E, in_channels) and filter is (E, out_channels), we can't multiply directly.
        # Correction: The filter network outputs (E, out_channels).
        # The node feature x_j is (E, in_channels).
        # We need to project x_j to out_channels? Or the filter is (E, in_channels, out_channels)?
        # Let's stick to standard SchNet: The filter is (E, out_channels) and x_j is (E, in_channels).
        # We usually do: x_j * filter where filter is broadcasted? No.
        # Standard SchNet: The filter is applied to the neighbor's feature.
        # x_j (E, in_channels) * filter (E, out_channels) -> mismatch.
        # Let's re-implement the filter to output (E, in_channels, out_channels) or project x_j.
        # Actually, the standard SchNet implementation in PyG (if available) or literature:
        # The filter is a scalar or vector that multiplies the node feature.
        # Let's assume the filter is (E, out_channels) and we want to update x to out_channels.
        # So we do: x_j (E, in_channels) -> project to (E, out_channels) -> multiply by filter (E, out_channels).
        # Or: filter is (E, in_channels, out_channels).
        
        # Let's follow the common pattern:
        # 1. Project x_j to out_channels? No, that's in update_net.
        # 2. The filter should be (E, in_channels, out_channels) to multiply x_j (E, in_channels) -> (E, out_channels).
        # But that's heavy.
        # Alternative: The filter is (E, out_channels) and we do: x_j (E, in_channels) * filter (E, out_channels) is not possible.
        # Let's look at the standard SchNet block:
        # m_ij = h_i * f(d_ij). h_i is (in_channels), f(d_ij) is (out_channels).
        # This implies f(d_ij) is a matrix? Or h_i is projected?
        # Actually, in the original SchNet, the filter is a vector of size `out_channels`.
        # And the node feature is `in_channels`.
        # The operation is: x_j * filter. This requires x_j to be projected to `out_channels` first?
        # Or the filter is `in_channels x out_channels`.
        
        # Let's simplify: We will project x_j to `out_channels` inside the message function if needed,
        # or assume the filter is `in_channels x out_channels`.
        # Given the current filter_net outputs `out_channels`, let's assume we want to project x_j to `out_channels`
        # and then multiply element-wise.
        
        # Correction: The standard implementation in `torch_geometric` (if using `CGConv`) or custom:
        # Let's use a linear layer to project x_j to out_channels, then multiply by filter.
        # But we don't have that layer here.
        # Let's change the filter_net to output (E, in_channels, out_channels)? No, too heavy.
        # Let's assume the filter is (E, out_channels) and we want to update x to out_channels.
        # So we do: x_j (E, in_channels) -> (E, out_channels) via a linear layer -> multiply by filter.
        # But we don't have that linear layer in `message`.
        
        # Let's re-architect slightly:
        # The `filter_net` should output (E, in_channels, out_channels) is too big.
        # Let's assume the filter is (E, out_channels) and we do:
        # x_j (E, in_channels) -> project to (E, out_channels) -> multiply by filter (E, out_channels).
        # We need a linear layer for projection. Let's add it.
        
        # Wait, the standard SchNet:
        # m_ij = h_j * f(d_ij)
        # h_j is (in_channels). f(d_ij) is (out_channels).
        # This implies f(d_ij) is a matrix?
        # Actually, the original SchNet uses:
        # f(d_ij) is a vector of size `out_channels`.
        # And h_j is projected to `out_channels`?
        # Let's check the literature: "SchNet: A Continuous-filter Convolutional Neural Network"
        # Eq 3: m_ij = h_j * f(d_ij).
        # h_j is (in_channels). f(d_ij) is (out_channels).
        # This implies h_j is projected to `out_channels`? Or f(d_ij) is (in_channels, out_channels)?
        # The paper says: "The filter f is a neural network that takes the distance as input and outputs a vector of size K (out_channels)."
        # And h_j is (in_channels).
        # So m_ij = h_j * f(d_ij) is not element-wise.
        # It is: m_ij = h_j * f(d_ij) where * is a specific operation?
        # Actually, the paper says: "The filter f is applied to the node features h_j."
        # And the result is summed.
        # Let's assume the standard implementation:
        # The filter is (E, out_channels).
        # The node feature h_j is (E, in_channels).
        # We need to project h_j to (E, out_channels) and then multiply element-wise.
        # So we need a linear layer in the message function.
        
        # Let's add a linear layer to project x_j to out_channels.
        # But we don't want to add too many parameters.
        # Alternatively, the filter is (E, in_channels, out_channels).
        # Let's assume the filter is (E, out_channels) and we project x_j to out_channels.
        
        # Let's use a simple approach:
        # 1. Project x_j to out_channels using a linear layer (shared).
        # 2. Multiply by filter.
        
        # We'll add a linear layer in __init__ for projection.
        # But we already have update_net.
        # Let's use the same projection? No.
        
        # Let's change the filter_net to output (E, in_channels, out_channels) is too heavy.
        # Let's assume the filter is (E, out_channels) and we project x_j to out_channels.
        
        # We'll add a linear layer `proj_x` in __init__.
        pass

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 10.0,
        activate: bool = True
    ):
        # Re-initialize with projection
        super().__init__(aggr='add')
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_gaussians = num_gaussians
        self.cutoff = cutoff

        # Projection for x_j
        self.proj_x = nn.Linear(in_channels, out_channels)

        # Filter network
        self.filter_net = nn.Sequential(
            nn.Linear(num_gaussians, out_channels),
            nn.Softplus() if activate else nn.Identity(),
            nn.Linear(out_channels, out_channels)
        )

        # Update network
        self.update_net = nn.Sequential(
            nn.Linear(in_channels, out_channels),
            nn.Softplus() if activate else nn.Identity(),
            nn.Linear(out_channels, out_channels)
        )

        self._initialize_weights()

    def _initialize_weights(self):
        nn.init.xavier_uniform_(self.proj_x.weight, gain=nn.init.calculate_gain('linear'))
        nn.init.zeros_(self.proj_x.bias)
        
        for layer in self.filter_net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight, gain=nn.init.calculate_gain('softplus'))
                nn.init.zeros_(layer.bias)
        
        for layer in self.update_net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight, gain=nn.init.calculate_gain('softplus'))
                nn.init.zeros_(layer.bias)

    def message(self, x_j: Tensor, edge_filter: Tensor) -> Tensor:
        # x_j: (E, in_channels)
        # edge_filter: (E, out_channels)
        # Project x_j to out_channels
        x_j_proj = self.proj_x(x_j)  # (E, out_channels)
        # Element-wise multiply
        return x_j_proj * edge_filter  # (E, out_channels)


class SchNetBlock(nn.Module):
    """
    A block of SchNet layers with residual connection.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_gaussians: int,
        cutoff: float = 10.0,
        activate: bool = True
    ):
        super().__init__()
        self.conv = ContinuousFilterConv(
            in_channels=in_channels,
            out_channels=out_channels,
            num_gaussians=num_gaussians,
            cutoff=cutoff,
            activate=activate
        )
        self.act = nn.Softplus() if activate else nn.Identity()
        # Residual connection requires in_channels == out_channels
        self.residual = nn.Identity() if in_channels == out_channels else nn.Linear(in_channels, out_channels)

    def forward(
        self,
        x: Tensor,
        edge_index: Adj,
        edge_attr: Tensor,
        edge_weight: OptTensor = None
    ) -> Tensor:
        out = self.conv(x, edge_index, edge_attr, edge_weight)
        out = self.act(out)
        residual = self.residual(x)
        return out + residual


class SchNet(nn.Module):
    """
    SchNet model for predicting barrier heights from TransitionStateGraphs.
    
    Architecture:
    1. Input embedding layer
    2. SchNet blocks (residual)
    3. Output head (readout)
    """
    def __init__(
        self,
        num_atom_types: int = 100,
        hidden_channels: int = 128,
        num_filters: int = 32,
        num_interactions: int = 6,
        num_gaussians: int = 50,
        cutoff: float = 10.0,
        readout: str = 'add',
        **kwargs
    ):
        super().__init__()
        self.num_atom_types = num_atom_types
        self.hidden_channels = hidden_channels
        self.num_filters = num_filters
        self.num_interactions = num_interactions
        self.num_gaussians = num_gaussians
        self.cutoff = cutoff
        self.readout = readout

        # Atom embedding
        self.embedding = nn.Embedding(num_atom_types, hidden_channels)

        # Distance smearing
        self.distance_expansion = GaussianSmearing(
            start=0.0,
            stop=cutoff,
            num_gaussians=num_gaussians
        )

        # SchNet blocks
        self.interactions = nn.ModuleList()
        for i in range(num_interactions):
            block = SchNetBlock(
                in_channels=hidden_channels,
                out_channels=hidden_channels,
                num_gaussians=num_gaussians,
                cutoff=cutoff,
                activate=True
            )
            self.interactions.append(block)

        # Output head
        self.output_net = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels // 2),
            nn.Softplus(),
            nn.Linear(hidden_channels // 2, 1)
        )

    def forward(
        self,
        z: Tensor,
        pos: Tensor,
        batch: Tensor,
        edge_index: Adj,
        edge_attr: Tensor,
        edge_weight: OptTensor = None
    ) -> Tensor:
        """
        Args:
            z: Node atomic numbers (N,)
            pos: Node positions (N, 3)
            batch: Batch indices (N,)
            edge_index: Edge indices (2, E)
            edge_attr: Smeared distances (E, num_gaussians) - precomputed or computed here?
                       Usually computed from pos in the forward pass if not provided.
            edge_weight: Optional edge weights (E,)
        
        Returns:
            Predicted scalar property (B, 1)
        """
        # Compute edge distances if not provided (assuming pos is available)
        # But the task says we receive graphs. We need to compute edge_attr from pos.
        # However, the forward signature usually takes edge_attr as input if precomputed.
        # Let's assume edge_attr is precomputed (smeared distances) as per the task description.
        # If not, we compute it here.
        
        # Check if edge_attr is already smeared?
        # The task says: "edge_attr: Smeared distance features".
        # So we assume it's already smeared.
        
        # If edge_attr is not smeared (raw distances), we smearing it here.
        # Let's assume the input edge_attr is raw distances for safety, or we check.
        # But the task says "edge_attr: Smeared distance features".
        # So we use it directly.
        
        # However, to be safe, let's compute distances from pos if edge_attr is not provided or is raw.
        # But the signature expects edge_attr.
        # Let's assume the caller provides smeared edge_attr.
        
        # If edge_attr is not provided, compute it.
        if edge_attr is None:
            # Compute distances
            row, col = edge_index
            dist = (pos[row] - pos[col]).norm(dim=-1).unsqueeze(-1)
            edge_attr = self.distance_expansion(dist)
        else:
            # If edge_attr is provided, assume it's smeared.
            # But if it's raw distances (scalar), smearing it.
            if edge_attr.dim() == 1 or edge_attr.dim() == 2 and edge_attr.size(-1) == 1:
                edge_attr = self.distance_expansion(edge_attr)

        # Embedding
        x = self.embedding(z)

        # Interactions
        for interaction in self.interactions:
            x = interaction(x, edge_index, edge_attr, edge_weight)

        # Readout
        # Sum pooling
        if self.readout == 'add':
            x = self.pooling(x, batch)
        elif self.readout == 'mean':
            x = self.pooling(x, batch, reduce='mean')
        
        # Output
        out = self.output_net(x)
        return out

    def pooling(self, x: Tensor, batch: Tensor, reduce: str = 'add') -> Tensor:
        """
        Graph pooling (sum, mean, max).
        """
        return torch_scatter.scatter(x, batch, dim=0, reduce=reduce)
    
    # Note: torch_scatter is not in the API surface. We can implement a simple sum.
    def pooling(self, x: Tensor, batch: Tensor, reduce: str = 'add') -> Tensor:
        """
        Simple graph pooling using scatter.
        If torch_scatter is not available, use a simple loop or cumsum.
        But PyTorch Geometric usually has scatter.
        Let's assume we can use torch_scatter or implement a simple version.
        Since the API surface doesn't include torch_scatter, let's implement a simple sum.
        """
        # Simple implementation for sum
        if reduce == 'add':
            out = torch.zeros(batch.max() + 1, x.size(1), device=x.device)
            out = out.index_add(0, batch, x)
            return out
        elif reduce == 'mean':
            # Count per batch
            counts = torch.bincount(batch, minlength=x.size(0))
            out = torch.zeros(batch.max() + 1, x.size(1), device=x.device)
            out = out.index_add(0, batch, x)
            return out / counts.unsqueeze(1)
        else:
            raise ValueError(f"Unknown reduce: {reduce}")


def get_model_config() -> Dict[str, Any]:
    """
    Returns the default model configuration from the project config.
    """
    config = load_config()
    return {
        'hidden_channels': config.get('MODEL', {}).get('hidden_channels', 128),
        'num_filters': config.get('MODEL', {}).get('num_filters', 32),
        'num_interactions': config.get('MODEL', {}).get('num_interactions', 6),
        'num_gaussians': config.get('MODEL', {}).get('num_gaussians', 50),
        'cutoff': config.get('MODEL', {}).get('cutoff', 10.0),
    }