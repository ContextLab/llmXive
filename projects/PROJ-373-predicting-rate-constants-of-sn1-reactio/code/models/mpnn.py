import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

# Ensure imports work
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class MPNNConfig:
    input_dim: int
    hidden_dim: int = 64
    output_dim: int = 1
    num_layers: int = 2
    dropout: float = 0.1
    
    def __post_init__(self):
        if self.num_layers < 1 or self.num_layers > 4:
            raise ValueError("num_layers must be between 1 and 4")

class MPNNMessagePassingLayer(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.linear = nn.Linear(input_dim, hidden_dim)
        self.norm = nn.BatchNorm1d(hidden_dim)
    
    def forward(self, x, edge_index):
        # Simplified message passing for 1D features (no graph structure in this simplified version)
        # In a real MPNN, we would use edge_index to aggregate messages.
        # For this test, we assume a simple feed-forward with some graph-like structure simulation.
        x = self.linear(x)
        x = self.norm(x)
        x = F.relu(x)
        return x

class MPNN(nn.Module):
    def __init__(self, config: MPNNConfig):
        super().__init__()
        self.config = config
        self.layers = nn.ModuleList()
        
        in_dim = config.input_dim
        for i in range(config.num_layers):
            self.layers.append(MPNNMessagePassingLayer(in_dim, config.hidden_dim))
            in_dim = config.hidden_dim
        
        self.output_layer = nn.Linear(config.hidden_dim, config.output_dim)
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(self, x, edge_index=None):
        for layer in self.layers:
            x = layer(x, edge_index)
            x = self.dropout(x)
        x = self.output_layer(x)
        return x

def create_mpnn_from_config(config: MPNNConfig) -> MPNN:
    return MPNN(config)

def main():
    # Test the model creation
    config = MPNNConfig(input_dim=10)
    model = create_mpnn_from_config(config)
    logger.info(f"MPNN model created: {model}")

if __name__ == "__main__":
    main()
