"""
Lightweight Message Passing Neural Network (MPNN) for molecular yield prediction.

CPU-optimized architecture with <1M parameters. No CUDA dependencies.
Implements a simplified Graph Convolutional Network (GCN) style message passing.
"""
import os
import sys
import json
import logging
import pickle
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, global_mean_pool

# Import project utilities
from src.utils.logging import get_logger, log_message
from src.utils.seeding import set_seed

# Configure logger
logger = get_logger(__name__)

class LightweightMPNN(nn.Module):
    """
    A lightweight Message Passing Neural Network for molecular graph regression.
    
    Architecture:
    - 2 GCN layers for message passing
    - Global mean pooling
    - 2-layer MLP for regression head
    - Total parameters < 1M (typically ~50k-100k depending on feature dim)
    
    Args:
        node_input_dim: Dimension of node features (atom features)
        edge_input_dim: Dimension of edge features (bond features) - currently unused for simplicity
        hidden_dim: Hidden dimension for GCN layers (default: 64)
        out_dim: Output dimension for regression (default: 1)
        dropout: Dropout rate (default: 0.1)
    """
    def __init__(
        self,
        node_input_dim: int = 42,  # Typical RDKit atom feature dim
        edge_input_dim: int = 10,
        hidden_dim: int = 64,
        out_dim: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.node_input_dim = node_input_dim
        self.edge_input_dim = edge_input_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.dropout = dropout
        
        # First GCN layer: input -> hidden
        self.conv1 = GCNConv(node_input_dim, hidden_dim)
        
        # Second GCN layer: hidden -> hidden
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
        # Regression head: pooled_graph_features -> out_dim
        # Pooled features = hidden_dim (from global_mean_pool)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, out_dim)
        
        # Initialize weights
        self._init_weights()
        
        logger.info(f"Initialized LightweightMPNN with {self.count_parameters()} parameters")
    
    def _init_weights(self):
        """Initialize weights with Xavier/Glorot initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, GCNConv):
                nn.init.xavier_uniform_(m.lin.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def count_parameters(self):
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass through the MPNN.
        
        Args:
            data: PyTorch Geometric Data object with:
                - x: Node features [num_nodes, node_input_dim]
                - edge_index: [2, num_edges]
                - edge_attr: [num_edges, edge_input_dim] (optional)
                - batch: [num_nodes] for pooling
        
        Returns:
            predictions: [num_graphs] tensor of predicted yields
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # First GCN layer with ReLU
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Second GCN layer with ReLU
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global mean pooling: [num_nodes, hidden_dim] -> [num_graphs, hidden_dim]
        x = global_mean_pool(x, batch)
        
        # Regression head
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.fc2(x)
        
        return x  # [num_graphs, 1]

def collate_fn(batch: List[Data]) -> Data:
    """
    Custom collate function for DataLoader.
    
    Args:
        batch: List of Data objects
    
    Returns:
        Batched Data object
    """
    return torch_geometric.data.Batch.from_data_list(batch)

def train_epoch(
    model: LightweightMPNN,
    loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int
) -> float:
    """
    Train the model for one epoch.
    
    Args:
        model: MPNN model
        loader: DataLoader for training set
        optimizer: Optimizer
        device: Device to run on
        epoch: Current epoch number
    
    Returns:
        Average training loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, batch in enumerate(loader):
        batch = batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(batch)
        
        # Assuming batch.y contains target yields
        if hasattr(batch, 'y'):
            targets = batch.y.view(-1)
            loss = F.mse_loss(outputs.squeeze(), targets)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        else:
            logger.warning(f"Batch {batch_idx} missing 'y' attribute, skipping")
    
    avg_loss = total_loss / max(num_batches, 1)
    log_message(logger, f"Epoch {epoch} - Training Loss: {avg_loss:.4f}")
    return avg_loss

def evaluate_epoch(
    model: LightweightMPNN,
    loader: torch.utils.data.DataLoader,
    device: torch.device
) -> Tuple[float, List[float], List[float]]:
    """
    Evaluate the model on a dataset.
    
    Args:
        model: MPNN model
        loader: DataLoader for evaluation set
        device: Device to run on
    
    Returns:
        Tuple of (average loss, list of predictions, list of targets)
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            
            outputs = model(batch)
            
            if hasattr(batch, 'y'):
                targets = batch.y.view(-1)
                loss = F.mse_loss(outputs.squeeze(), targets)
                
                total_loss += loss.item()
                num_batches += 1
                
                all_preds.extend(outputs.squeeze().cpu().numpy().tolist())
                all_targets.extend(targets.cpu().numpy().tolist())
    
    avg_loss = total_loss / max(num_batches, 1)
    return avg_loss, all_preds, all_targets

def create_model_and_optimizer(
    node_dim: int = 42,
    hidden_dim: int = 64,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5
) -> Tuple[LightweightMPNN, torch.optim.Optimizer]:
    """
    Create MPNN model and optimizer with specified hyperparameters.
    
    Args:
        node_dim: Node feature dimension
        hidden_dim: Hidden layer dimension
        learning_rate: Learning rate for optimizer
        weight_decay: Weight decay for regularization
    
    Returns:
        Tuple of (model, optimizer)
    """
    model = LightweightMPNN(
        node_input_dim=node_dim,
        hidden_dim=hidden_dim
    )
    
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )
    
    return model, optimizer

def save_model_checkpoint(
    model: LightweightMPNN,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    save_path: str,
    fold_idx: Optional[int] = None
):
    """
    Save model checkpoint to disk.
    
    Args:
        model: MPNN model
        optimizer: Optimizer state
        epoch: Current epoch
        loss: Training loss at this epoch
        save_path: Path to save checkpoint
        fold_idx: Optional fold index for naming
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'config': {
            'node_input_dim': model.node_input_dim,
            'hidden_dim': model.hidden_dim,
            'out_dim': model.out_dim,
            'dropout': model.dropout
        }
    }
    
    if fold_idx is not None:
        save_path = save_path.replace('.pt', f'_fold{fold_idx}.pt')
    
    torch.save(checkpoint, save_path)
    log_message(logger, f"Saved model checkpoint to {save_path}")

def load_model_checkpoint(
    checkpoint_path: str,
    device: torch.device,
    map_location: Optional[torch.device] = None
) -> Tuple[LightweightMPNN, Dict[str, Any]]:
    """
    Load model checkpoint from disk.
    
    Args:
        checkpoint_path: Path to checkpoint file
        device: Device to load model to
        map_location: Optional map_location for torch.load
    
    Returns:
        Tuple of (model, checkpoint metadata)
    """
    checkpoint = torch.load(checkpoint_path, map_location=map_location or device)
    
    config = checkpoint.get('config', {})
    model = LightweightMPNN(
        node_input_dim=config.get('node_input_dim', 42),
        hidden_dim=config.get('hidden_dim', 64),
        out_dim=config.get('out_dim', 1),
        dropout=config.get('dropout', 0.1)
    )
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    log_message(logger, f"Loaded model from {checkpoint_path} (epoch {checkpoint.get('epoch', 'N/A')})")
    return model, checkpoint

def main():
    """
    Main function for standalone testing of the MPNN module.
    
    Creates a synthetic graph, runs forward pass, and verifies output shape.
    This is for module validation only; actual training happens in train.py.
    """
    logger.info("Running MPNN module self-test...")
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Create a dummy graph
    num_nodes = 10
    num_edges = 20
    node_dim = 42
    
    x = torch.randn(num_nodes, node_dim)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    batch = torch.zeros(num_nodes, dtype=torch.long)  # All nodes in one graph
    
    data = Data(x=x, edge_index=edge_index, batch=batch)
    
    # Create model
    model, optimizer = create_model_and_optimizer(node_dim=node_dim, hidden_dim=64)
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(data)
    
    assert output.shape == (1, 1), f"Expected output shape (1, 1), got {output.shape}"
    assert not torch.isnan(output).any(), "Output contains NaN values"
    assert not torch.isinf(output).any(), "Output contains Inf values"
    
    param_count = model.count_parameters()
    logger.info(f"Model parameters: {param_count}")
    assert param_count < 1_000_000, f"Model has too many parameters: {param_count}"
    
    logger.info("MPNN module self-test PASSED")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
