import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Tuple, Optional

class LightweightGNN(nn.Module):
    """Lightweight GNN for elastic moduli prediction."""
    
    def __init__(self, node_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.conv1 = GCNConv(node_dim, hidden_dim)
        self.convs = nn.ModuleList([
            GCNConv(hidden_dim, hidden_dim) for _ in range(num_layers - 1)
        ])
        self.lin = nn.Linear(hidden_dim, 6)  # 6 elastic tensor components
        
    def forward(self, x, edge_index, batch):
        x = F.relu(self.conv1(x, edge_index))
        for conv in self.convs:
            x = F.relu(conv(x, edge_index))
        x = global_mean_pool(x, batch)
        return self.lin(x)

def create_model(node_dim: int, hidden_dim: int = 64, num_layers: int = 2) -> LightweightGNN:
    """Create a lightweight GNN model."""
    return LightweightGNN(node_dim, hidden_dim, num_layers)
