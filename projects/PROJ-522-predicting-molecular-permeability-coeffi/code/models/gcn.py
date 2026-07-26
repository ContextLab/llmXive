import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Optional, Tuple

class MolecularGCN(nn.Module):
    def __init__(self, num_features: int = 32, hidden_channels: int = 64, num_layers: int = 3, dropout: float = 0.5):
        super().__init__()
        self.conv1 = GCNConv(num_features, hidden_channels)
        self.convs = nn.ModuleList()
        
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
        
        self.dropout = nn.Dropout(dropout)
        self.lin = nn.Linear(hidden_channels, 1)

    def forward(self, data: Data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        
        for conv in self.convs:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = self.dropout(x)
        
        x = global_mean_pool(x, batch)
        x = self.lin(x)
        return x

def create_model(num_features: int = 32):
    """
    Factory function to create a MolecularGCN model.
    """
    return MolecularGCN(num_features=num_features)
