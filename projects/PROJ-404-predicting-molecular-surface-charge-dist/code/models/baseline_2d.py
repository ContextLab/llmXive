"""
2D Connectivity-only baseline model.
"""
from typing import Optional
import torch
import torch.nn as nn
from torch_geometric.nn import MessagePassing
from torch_geometric.nn import global_mean_pool
from torch_geometric.utils import add_self_loops

class EdgeEncoder(nn.Module):
    def __init__(self, edge_dim: int = 1):
        super().__init__()
        self.lin = nn.Linear(edge_dim, 128)

    def forward(self, edge_attr: torch.Tensor) -> torch.Tensor:
        return self.lin(edge_attr)

class ConnectivityGNNLayer(MessagePassing):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__(aggr='mean')
        self.lin = nn.Linear(in_channels, out_channels)
        self.act = nn.SiLU()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor):
        x = self.lin(x)
        x = self.act(x)
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j

class Baseline2DModel(nn.Module):
    def __init__(self, num_features: int = 1, hidden_dim: int = 128):
        super().__init__()
        self.encoder = nn.Linear(num_features, hidden_dim)
        self.conv1 = ConnectivityGNNLayer(hidden_dim, hidden_dim)
        self.conv2 = ConnectivityGNNLayer(hidden_dim, hidden_dim)
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: Optional[torch.Tensor] = None):
        x = self.encoder(x)
        x = self.conv1(x, edge_index)
        x = self.conv2(x, edge_index)
        
        if batch is None:
            out = self.readout(x).squeeze(-1)
        else:
            out = self.readout(x).squeeze(-1)
            out = global_mean_pool(out, batch)
        return out

def create_baseline_2d_model(num_features: int = 1, hidden_dim: int = 128):
    return Baseline2DModel(num_features, hidden_dim)
