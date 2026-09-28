"""
Graph Convolutional Network (GCN) implementation optimized for CPU execution.

Implements a GCN architecture with ≤2 layers and hidden size 128 as per FR-003.
Designed for efficient CPU training within the project's constraints.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
from typing import Optional, List, Tuple

from utils.config import get_config
from utils.logger import setup_logger

logger = setup_logger()
config = get_config()
SEED = config.get('seed', 42)
DEVICE = config.get('device', 'cpu')

# Set global seed for reproducibility
torch.manual_seed(SEED)
if DEVICE == 'cuda':
    torch.cuda.manual_seed_all(SEED)

class GCN(nn.Module):
    """
    Graph Convolutional Network for molecular property prediction.
    
    Architecture:
    - Input Layer: Node features -> Hidden (128)
    - Hidden Layer 1: GCNConv -> ReLU -> Dropout
    - Hidden Layer 2 (Optional): GCNConv -> ReLU -> Dropout
    - Output Layer: Linear -> Output (1 for regression)
    
    Constraints:
    - Maximum 2 GCN layers (FR-003)
    - Hidden size 128
    - Optimized for CPU execution
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        output_dim: int = 1,
        num_layers: int = 2,
        dropout: float = 0.5
    ):
        """
        Initialize the GCN model.
        
        Args:
            input_dim: Dimension of input node features
            hidden_dim: Hidden layer dimension (default 128 per FR-003)
            output_dim: Output dimension (1 for PCE regression)
            num_layers: Number of GCN layers (max 2 per FR-003)
            dropout: Dropout probability
        """
        super(GCN, self).__init__()
        
        # Validate constraints
        if num_layers > 2:
            logger.warning(f"num_layers={num_layers} exceeds max 2, clamping to 2")
            num_layers = 2
        if num_layers < 1:
            raise ValueError("num_layers must be at least 1")
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Layer 1: Input -> Hidden
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        
        # Layer 2 (if needed): Hidden -> Hidden
        if num_layers == 2:
            self.conv2 = GCNConv(hidden_dim, hidden_dim)
            self.bn2 = nn.BatchNorm1d(hidden_dim)
        
        # Output layer
        self.fc = nn.Linear(hidden_dim, output_dim)
        
        logger.info(f"Initialized GCN with {num_layers} layers, hidden_dim={hidden_dim}")
    
    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass through the GCN.
        
        Args:
            data: PyTorch Geometric Data object containing x, edge_index, batch
        
        Returns:
            Tensor of shape (num_graphs, output_dim)
        """
        x, edge_index = data.x, data.edge_index
        
        # Layer 1
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Layer 2 (if applicable)
        if self.num_layers == 2:
            x = self.conv2(x, edge_index)
            x = self.bn2(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        # Graph pooling: mean readout
        # Assuming data.batch is provided for batched graphs
        if hasattr(data, 'batch') and data.batch is not None:
            x = torch_scatter.scatter_mean(x, data.batch, dim=0)
        else:
            # If not batched, assume single graph and mean over nodes
            x = x.mean(dim=0, keepdim=True)
        
        # Output
        x = self.fc(x)
        return x

# Import scatter here to avoid circular imports if torch_scatter is not installed
# We'll use a fallback implementation if torch_scatter is missing
try:
    from torch_scatter import scatter_mean
except ImportError:
    logger.warning("torch_scatter not found, using fallback mean implementation")
    
    def scatter_mean(src: torch.Tensor, index: torch.Tensor, dim: int = 0) -> torch.Tensor:
        """Fallback mean implementation without torch_scatter."""
        max_index = index.max().item() + 1
        out = torch.zeros((max_index,) + src.shape[1:], device=src.device, dtype=src.dtype)
        out = out.index_add(dim, index, src)
        count = torch.zeros(max_index, device=src.device, dtype=src.dtype)
        count = count.index_add(dim, index, torch.ones_like(index, dtype=src.dtype))
        return out / count.unsqueeze(dim).expand_as(out)

def create_gcn_model(
    input_dim: int,
    hidden_dim: int = 128,
    num_layers: int = 2,
    dropout: float = 0.5
) -> GCN:
    """
    Factory function to create a GCN model.
    
    Args:
        input_dim: Dimension of input features
        hidden_dim: Hidden layer dimension
        num_layers: Number of GCN layers
        dropout: Dropout probability
    
    Returns:
        Initialized GCN model on the configured device
    """
    model = GCN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout
    )
    model = model.to(DEVICE)
    logger.info(f"Model moved to device: {DEVICE}")
    return model

def count_parameters(model: nn.Module) -> int:
    """
    Count the number of trainable parameters in a model.
    
    Args:
        model: PyTorch model
    
    Returns:
        Number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def main():
    """
    Main function to demonstrate GCN model creation and basic usage.
    """
    logger.info("Starting GCN model demonstration...")
    
    # Create a dummy graph for testing
    num_nodes = 10
    num_edges = 20
    input_dim = 10  # Example feature dimension
    
    x = torch.randn(num_nodes, input_dim)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    batch = torch.zeros(num_nodes, dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index, batch=batch)
    
    # Create model
    model = create_gcn_model(input_dim=input_dim)
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        output = model(data)
    
    logger.info(f"Model created with {count_parameters(model)} parameters")
    logger.info(f"Output shape: {output.shape}")
    logger.info("GCN model demonstration completed successfully")

if __name__ == "__main__":
    main()
