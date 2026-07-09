"""
Message Passing Neural Network (MPNN) implementation for molecular solubility prediction.
Designed for CPU-only execution using PyTorch Geometric.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data, Batch
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops

# Ensure CPU-only execution
if torch.cuda.is_available():
    logging.warning("CUDA detected but forcing CPU-only execution as per project constraints.")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class MPNNLayer(MessagePassing):
    """
    A single Message Passing Neural Network layer.
    Uses simple sum aggregation and a two-layer MLP for message construction.
    """
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int):
        super().__init__(aggr='add')  # Sum aggregation
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.hidden_dim = hidden_dim

        # Message MLP: [node_dim + edge_dim] -> [hidden_dim] -> [hidden_dim]
        self.message_mlp = nn.Sequential(
            nn.Linear(node_dim + edge_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

        # Update MLP: [node_dim + hidden_dim] -> [hidden_dim]
        self.update_mlp = nn.Sequential(
            nn.Linear(node_dim + hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor):
        # x: [num_nodes, node_dim]
        # edge_index: [2, num_edges]
        # edge_attr: [num_edges, edge_dim]
        
        # Add self-loops for message passing if not present
        edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))
        # Note: edge_attr needs to be expanded for self-loops if using them strictly,
        # but for simplicity in this MPNN variant, we often pass zero vectors or repeat.
        # To keep it robust, we'll assume edge_attr aligns with the new edge_index if passed,
        # or handle the mismatch by creating zero-edges for self-loops if necessary.
        # For this implementation, we assume the caller handles edge_attr alignment or
        # we construct a simple edge_attr for self-loops.
        
        # Simplified approach: assume edge_attr is provided for all edges in edge_index
        # If self-loops were added, we need corresponding edge_attr.
        # Let's create zero edge attributes for self-loops if the count mismatches.
        if edge_attr.size(0) != edge_index.size(1):
            # Create zero edge attributes for the new self-loops
            num_new_edges = edge_index.size(1) - edge_attr.size(0)
            if num_new_edges > 0:
                new_edge_attr = torch.zeros(num_new_edges, self.edge_dim, device=edge_attr.device)
                edge_attr = torch.cat([edge_attr, new_edge_attr], dim=0)

        out = self.propagate(edge_index, x=x, edge_attr=edge_attr)
        return out

    def message(self, x_j: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        # x_j: source node features [num_edges, node_dim]
        # edge_attr: edge features [num_edges, edge_dim]
        msg_input = torch.cat([x_j, edge_attr], dim=1)
        return self.message_mlp(msg_input)

    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        # aggr_out: aggregated messages [num_nodes, hidden_dim]
        # x: original node features [num_nodes, node_dim]
        update_input = torch.cat([x, aggr_out], dim=1)
        return self.update_mlp(update_input)


class GNNMPNN(nn.Module):
    """
    Full Graph Neural Network model for regression (logS prediction).
    Architecture:
      - Input projection
      - Multiple MPNN layers
      - Readout (sum pooling)
      - Regression head
    """
    def __init__(self, node_dim: int = 20, edge_dim: int = 10, hidden_dim: int = 64, num_layers: int = 3, output_dim: int = 1):
        super().__init__()
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Input projection
        self.input_proj = nn.Linear(node_dim, hidden_dim)

        # MPNN Layers
        self.mpnn_layers = nn.ModuleList([
            MPNNLayer(hidden_dim, edge_dim, hidden_dim)
            for _ in range(num_layers)
        ])

        # Readout projection (optional, but good for stability)
        self.readout_proj = nn.Linear(hidden_dim, hidden_dim)

        # Regression head
        self.regression_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim)
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, batch: Batch) -> torch.Tensor:
        """
        Forward pass.
        Args:
            batch: PyTorch Geometric Batch object containing x, edge_index, edge_attr, batch
        Returns:
            predictions: [num_graphs, 1]
        """
        x = batch.x
        edge_index = batch.edge_index
        edge_attr = batch.edge_attr
        batch_idx = batch.batch

        # Project input features
        h = self.input_proj(x)

        # Message passing layers
        for layer in self.mpnn_layers:
            h = layer(h, edge_index, edge_attr)
            h = F.relu(h)

        # Readout: sum pooling per graph
        # h: [num_nodes, hidden_dim]
        # batch_idx: [num_nodes]
        graph_h = torch.zeros(
            batch_idx.max().item() + 1,
            h.size(1),
            device=h.device
        )
        graph_h = graph_h.index_add(0, batch_idx, h)

        # Final projection and regression
        graph_h = self.readout_proj(graph_h)
        graph_h = F.relu(graph_h)
        out = self.regression_head(graph_h)

        return out

    def load_processed_data(self, data_path: str) -> Tuple[Batch, List[float]]:
        """
        Load preprocessed graph data from JSON files.
        Expected format in data_path: a list of graph dictionaries.
        """
        graphs = []
        with open(data_path, 'r') as f:
            graphs = json.load(f)

        data_list = []
        for g in graphs:
            x = torch.tensor(g['node_features'], dtype=torch.float)
            edge_index = torch.tensor(g['edge_index'], dtype=torch.long)
            edge_attr = torch.tensor(g['edge_features'], dtype=torch.float)
            y = torch.tensor([g['logS']], dtype=torch.float)
            
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
            data_list.append(data)

        if not data_list:
            raise ValueError("No data found in the provided file.")

        batch = Batch.from_data_list(data_list)
        # Extract targets for validation if needed, though usually handled outside
        targets = [d.y.item() for d in data_list]
        
        return batch, targets

def main():
    """
    Main function to demonstrate model instantiation and basic structure check.
    """
    logger.info("Initializing MPNN model structure...")
    
    # Dummy dimensions matching typical RDKit features
    node_dim = 20  # Example: atom features
    edge_dim = 10  # Example: bond features
    hidden_dim = 64
    num_layers = 3

    model = GNNMPNN(node_dim=node_dim, edge_dim=edge_dim, hidden_dim=hidden_dim, num_layers=num_layers)
    
    # Verify CPU-only constraint
    device = torch.device("cpu")
    model.to(device)
    
    logger.info(f"Model initialized on {device}")
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    
    # Create a dummy batch to test forward pass
    num_nodes = 10
    num_edges = 20
    dummy_x = torch.randn(num_nodes, node_dim)
    dummy_edge_index = torch.randint(0, num_nodes, (2, num_edges))
    dummy_edge_attr = torch.randn(num_edges, edge_dim)
    dummy_batch = torch.zeros(num_nodes, dtype=torch.long)
    
    dummy_data = Data(x=dummy_x, edge_index=dummy_edge_index, edge_attr=dummy_edge_attr, batch=dummy_batch)
    dummy_batch_obj = Batch.from_data_list([dummy_data])
    
    model.eval()
    with torch.no_grad():
        output = model(dummy_batch_obj)
    
    logger.info(f"Dummy forward pass output shape: {output.shape}")
    logger.info("MPNN model structure verified successfully.")

if __name__ == "__main__":
    main()