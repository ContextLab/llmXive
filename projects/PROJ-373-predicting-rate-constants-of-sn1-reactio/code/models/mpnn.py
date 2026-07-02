import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class MPNNConfig:
    input_dim: int
    hidden_dim: int = 64
    num_layers: int = 2
    output_dim: int = 1
    dropout: float = 0.1

class MPNNMessagePassingLayer(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.linear = nn.Linear(input_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # Simplified message passing
        x = self.linear(x)
        x = F.relu(x)
        x = self.norm(x)
        return x

class MPNN(nn.Module):
    def __init__(self, config: MPNNConfig):
        super().__init__()
        if config.num_layers < 1 or config.num_layers > 4:
            raise ValueError(f"num_layers must be between 1 and 4, got {config.num_layers}")

        self.layers = nn.ModuleList([
            MPNNMessagePassingLayer(
                config.input_dim if i == 0 else config.hidden_dim,
                config.hidden_dim
            ) for i in range(config.num_layers)
        ])
        self.head = nn.Linear(config.hidden_dim, config.output_dim)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            x = layer(x, edge_index)
            x = self.dropout(x)
        return self.head(x)

def create_mpnn_from_config(config: MPNNConfig) -> MPNN:
    """Create MPNN from config."""
    return MPNN(config)

def main():
    """Main entry point for MPNN model."""
    config = MPNNConfig(input_dim=10, hidden_dim=64, num_layers=2)
    model = create_mpnn_from_config(config)
    print(f"Created MPNN with {sum(p.numel() for p in model.parameters())} parameters")

if __name__ == "__main__":
    main()
