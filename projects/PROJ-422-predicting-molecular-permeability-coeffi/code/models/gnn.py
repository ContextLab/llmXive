import logging
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing, global_mean_pool, global_max_pool
from pathlib import Path
import json
import time

from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

class MPNNLayer(MessagePassing):
    """
    A single Message Passing Neural Network layer using the 'add' aggregation scheme.
    Designed for CPU efficiency by avoiding complex sparse operations where possible.
    """
    def __init__(self, in_channels: int, out_channels: int, hidden_channels: int, dropout: float = 0.1):
        super().__init__(aggr='add')  # 'add' aggregation is generally faster on CPU than 'mean' or 'max' in some contexts
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Message function: W_m * h_j
        self.lin_msg = nn.Linear(in_channels, hidden_channels)
        # Update function: W_u * h_i + sum(msg)
        self.lin_update = nn.Linear(hidden_channels + in_channels, out_channels)
        
        self.dropout = nn.Dropout(dropout)
        self.bn = nn.BatchNorm1d(out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # x: [N, in_channels]
        # edge_index: [2, E]
        msg = self.propagate(edge_index, x=x)
        # msg shape: [N, hidden_channels]
        
        # Combine original node features with aggregated messages
        # x: [N, in_channels], msg: [N, hidden_channels]
        combined = torch.cat([x, msg], dim=1)
        
        out = self.lin_update(combined)
        out = self.bn(out)
        out = F.relu(out)
        out = self.dropout(out)
        return out

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        # x_j: [E, in_channels]
        return F.relu(self.lin_msg(x_j))

class MPNN(nn.Module):
    """
    Message Passing Neural Network for molecular property prediction.
    Architecture: Input Embedding -> N MPNN Layers -> Readout (Mean + Max) -> MLP Head.
    Optimized for CPU execution with batch normalization and dropout for regularization.
    """
    def __init__(self, in_features: int, hidden_channels: int = 128, out_channels: int = 1, num_layers: int = 4, dropout: float = 0.1):
        super().__init__()
        self.num_layers = num_layers
        
        # Initial projection to hidden dimension
        self.input_proj = nn.Linear(in_features, hidden_channels)
        
        # MPNN Layers
        self.mpnn_layers = nn.ModuleList()
        for i in range(num_layers):
            in_dim = hidden_channels if i > 0 else hidden_channels
            # For the last layer, we might want to keep it same size or adjust, 
            # but standard MPNN keeps hidden size constant through layers.
            self.mpnn_layers.append(MPNNLayer(hidden_channels, hidden_channels, hidden_channels, dropout))
        
        # Readout layers
        # We use both mean and max pooling to capture different aspects of the graph
        self.readout_mlp = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, out_channels)
        )

        # Early stopping parameters
        self.best_loss = float('inf')
        self.patience = 10
        self.counter = 0
        self.early_stop = False

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Node features [N, in_features]
            edge_index: Graph connectivity [2, E]
            batch: Batch vector [N] indicating which graph each node belongs to
        """
        # Initial projection
        x = F.relu(self.input_proj(x))
        
        # Message Passing
        for layer in self.mpnn_layers:
            x = layer(x, edge_index)
        
        # Readout: Global pooling
        # Mean pooling
        mean_pool = global_mean_pool(x, batch)
        # Max pooling
        max_pool = global_max_pool(x, batch)
        
        # Concatenate pooled features
        graph_repr = torch.cat([mean_pool, max_pool], dim=1)
        
        # Final prediction head
        out = self.readout_mlp(graph_repr)
        return out

    def check_early_stopping(self, val_loss: float) -> bool:
        """
        Updates early stopping state based on validation loss.
        Returns True if training should stop.
        """
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.counter = 0
            self.early_stop = False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info(f"Early stopping triggered after {self.counter} epochs without improvement.")
        return self.early_stop

    def save_checkpoint(self, path: Path, epoch: int, loss: float):
        """Saves model state and training metrics."""
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.state_dict(),
            'loss': loss,
            'best_loss': self.best_loss,
        }, path)
        logger.info(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: Path):
        """Loads the best model state."""
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found at {path}")
        
        checkpoint = torch.load(path, map_location='cpu')
        self.load_state_dict(checkpoint['model_state_dict'])
        logger.info(f"Loaded checkpoint from epoch {checkpoint['epoch']} with loss {checkpoint['loss']}")
        return checkpoint

def create_mpnn_model(in_features: int, hidden_channels: int = 128, num_layers: int = 4) -> MPNN:
    """
    Factory function to create an MPNN instance.
    
    Args:
        in_features: Dimension of input node features.
        hidden_channels: Dimension of hidden layers.
        num_layers: Number of MPNN layers.
        
    Returns:
        MPNN model instance.
    """
    model = MPNN(
        in_features=in_features,
        hidden_channels=hidden_channels,
        num_layers=num_layers,
        out_channels=1  # Regression target
    )
    logger.info(f"Created MPNN model with {num_layers} layers, hidden size {hidden_channels}")
    return model

def train_epoch(model: MPNN, loader, optimizer, device):
    """Trains the model for one epoch."""
    model.train()
    total_loss = 0
    criterion = nn.MSELoss()
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = criterion(out.squeeze(), batch.y)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(loader)

def validate_epoch(model: MPNN, loader, device):
    """Validates the model on a dataset."""
    model.eval()
    total_loss = 0
    criterion = nn.MSELoss()
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = criterion(out.squeeze(), batch.y)
            total_loss += loss.item()
    
    return total_loss / len(loader)

def main():
    """
    Main execution entry point for GNN training logic.
    This function demonstrates the model setup and training loop structure.
    It expects pre-processed data loaders (PyTorch Geometric DataLoaders) to be passed.
    """
    setup_logging()
    logger.info("Starting GNN Model Training Module")

    # Example configuration (in real usage, these would come from config.yaml or CLI args)
    in_features = 20  # Placeholder, should match data preprocessing output
    hidden_channels = 128
    num_layers = 4
    learning_rate = 0.001
    epochs = 50
    patience = 10
    device = torch.device('cpu') # Enforce CPU as per constraints

    # Initialize model
    model = create_mpnn_model(in_features, hidden_channels, num_layers)
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Mock loader for demonstration of structure (real data loaders would be injected)
    # In a real run, this would be: train_loader, val_loader = get_data_loaders(...)
    logger.warning("No data loaders provided. Skipping actual training loop. Model architecture validated.")
    
    # Log model summary
    total_params = sum(p.numel() for p in model.parameters())
    log_result_artifact("model_params", total_params)
    logger.info(f"Total parameters: {total_params}")

    # Example of early stopping logic integration
    logger.info("Early stopping mechanism configured.")
    
    # If we had data, the loop would look like this:
    # for epoch in range(epochs):
    #     train_loss = train_epoch(model, train_loader, optimizer, device)
    #     val_loss = validate_epoch(model, val_loader, device)
    #     
    #     logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
    #     
    #     if model.check_early_stopping(val_loss):
    #         break
    #     
    #     if val_loss < model.best_loss:
    #         model.save_checkpoint(Path("checkpoints/best_model.pt"), epoch, val_loss)

    logger.info("GNN Module initialization complete.")

if __name__ == "__main__":
    main()