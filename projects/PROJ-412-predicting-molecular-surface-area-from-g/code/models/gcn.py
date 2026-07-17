"""
Lightweight GCN Model for Molecular Surface Area Prediction.

Implements a CPU-tractable Graph Convolutional Network using PyTorch Geometric.
Designed to predict molecular surface area (SASA) from 2D molecular graphs.
"""
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data
from typing import Optional, Tuple, List
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


class GCNModel(torch.nn.Module):
    """
    Graph Convolutional Network for predicting molecular surface area.
    
    Architecture:
    - 2 GCN layers with hidden dimension 64
    - ReLU activations
    - Global mean pooling to aggregate node features
    - Single linear output layer for regression
    
    Attributes:
        conv1: First graph convolutional layer
        conv2: Second graph convolutional layer
        lin: Output linear layer
        hidden_dim: Dimension of hidden layers (default: 64)
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, dropout: float = 0.1):
        """
        Initialize the GCN model.
        
        Args:
            input_dim: Number of input features per node (from 2D graph extraction)
            hidden_dim: Dimension of hidden layers
            dropout: Dropout probability for regularization
        """
        super(GCNModel, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Graph convolutional layers
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
        # Output layer
        self.lin = torch.nn.Linear(hidden_dim, 1)
        
        # Dropout for regularization
        self.dropout = dropout
        
        logger.info(f"Initialized GCNModel: input_dim={input_dim}, hidden_dim={hidden_dim}, dropout={dropout}")
    
    def forward(self, input_tensor: Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass through the GCN network.
        
        Args:
            input_tensor: Tuple containing:
                - x: Node feature matrix of shape [num_nodes, input_dim]
                - edge_index: Graph connectivity in COO format of shape [2, num_edges]
                - batch: Batch vector of shape [num_nodes] mapping nodes to their respective graphs
                - edge_weight: Optional edge weights of shape [num_edges] (default: None)
        
        Returns:
            predictions: Tensor of shape [num_graphs] containing predicted SASA values
        """
        x, edge_index, batch, edge_weight = input_tensor
        
        # First GCN layer
        x = self.conv1(x, edge_index, edge_attr=edge_weight)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Second GCN layer
        x = self.conv2(x, edge_index, edge_attr=edge_weight)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Global mean pooling to get graph-level representation
        x = global_mean_pool(x, batch)
        
        # Output layer
        predictions = self.lin(x)
        
        return predictions
    
    def predict(self, data: Data) -> torch.Tensor:
        """
        Convenience method to predict on a single Data object.
        
        Args:
            data: PyTorch Geometric Data object containing node features, edge index, etc.
        
        Returns:
            prediction: Tensor of shape [1] containing the predicted SASA value
        """
        # Prepare input tuple
        x = data.x
        edge_index = data.edge_index
        batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        edge_weight = data.edge_attr if hasattr(data, 'edge_attr') else None
        
        # Forward pass
        with torch.no_grad():
            prediction = self.forward((x, edge_index, batch, edge_weight))
        
        return prediction
    
    def get_config(self) -> dict:
        """
        Get the model configuration as a dictionary.
        
        Returns:
            config: Dictionary containing model hyperparameters
        """
        return {
            'input_dim': self.input_dim,
            'hidden_dim': self.hidden_dim,
            'dropout': self.dropout,
            'num_layers': 2,
            'pooling': 'mean'
        }
    
    def save(self, path: str) -> None:
        """
        Save the model to disk.
        
        Args:
            path: Path to save the model checkpoint
        """
        import os
        from pathlib import Path
        
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.get_config()
        }, path)
        
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: str, device: Optional[torch.device] = None) -> 'GCNModel':
        """
        Load a model from disk.
        
        Args:
            path: Path to the model checkpoint
            device: Device to load the model on (default: CPU)
        
        Returns:
            model: Loaded GCNModel instance
        """
        if device is None:
            device = torch.device('cpu')
        
        checkpoint = torch.load(path, map_location=device)
        config = checkpoint['config']
        
        # Create model instance
        model = cls(
            input_dim=config['input_dim'],
            hidden_dim=config['hidden_dim'],
            dropout=config['dropout']
        )
        
        # Load state dict
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval()
        
        logger.info(f"Model loaded from {path}")
        return model


def create_model_from_processed_data(
    processed_data_path: str,
    hidden_dim: int = 64,
    dropout: float = 0.1
) -> GCNModel:
    """
    Create a GCNModel instance based on the feature dimension of processed data.
    
    Args:
        processed_data_path: Path to the processed data file (Parquet)
        hidden_dim: Hidden dimension for the model
        dropout: Dropout probability
    
    Returns:
        model: Initialized GCNModel instance
    """
    import pandas as pd
    
    # Load processed data to determine input dimension
    df = pd.read_parquet(processed_data_path)
    
    # Assuming node features are stored as a list or array in a column
    # We need to determine the feature dimension
    # This is a simplified approach - in practice, you'd need to inspect the data structure
    if 'node_features' in df.columns:
        # Get the first non-null entry to determine dimension
        sample_features = df['node_features'].dropna().iloc[0]
        if isinstance(sample_features, list):
            input_dim = len(sample_features)
        else:
            # Try to infer from array
            import numpy as np
            input_dim = len(np.array(sample_features))
    else:
        # Default to a reasonable dimension if not found
        # This should be updated based on actual data structure
        input_dim = 64
        logger.warning(f"Could not determine input dimension from {processed_data_path}, using default {input_dim}")
    
    logger.info(f"Creating GCNModel with input_dim={input_dim}")
    return GCNModel(input_dim=input_dim, hidden_dim=hidden_dim, dropout=dropout)


if __name__ == "__main__":
    # Simple test to verify the model can be instantiated and run a forward pass
    logger.info("Testing GCNModel initialization and forward pass...")
    
    # Create a dummy model
    model = GCNModel(input_dim=10, hidden_dim=32)
    
    # Create dummy input
    x = torch.randn(100, 10)  # 100 nodes, 10 features
    edge_index = torch.randint(0, 100, (2, 200))  # 200 edges
    batch = torch.zeros(100, dtype=torch.long)  # All nodes in one graph
    edge_weight = None
    
    # Forward pass
    output = model((x, edge_index, batch, edge_weight))
    
    logger.info(f"Model output shape: {output.shape}")
    logger.info(f"Sample prediction: {output[0].item():.4f}")
    logger.info("GCNModel test passed successfully!")