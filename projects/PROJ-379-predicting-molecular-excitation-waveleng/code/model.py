import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops
from torch_geometric.data import Data
from typing import Optional, List, Tuple
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MPNN(MessagePassing):
    """
    Message Passing Neural Network (MPNN) for molecular property prediction.
    Designed to be lightweight (<1M parameters) and suitable for CPU execution.
    
    Architecture:
    - 3 Message Passing Layers
    - Readout: Global Mean Pooling
    - Output: Single scalar (lambda_max)
    """
    
    def __init__(self, node_dim: int = 64, hidden_dim: int = 64, num_layers: int = 3):
        """
        Initialize the MPNN model.
        
        Args:
            node_dim: Input feature dimension (size of ECFP or atom features)
            hidden_dim: Hidden dimension for message passing
            num_layers: Number of message passing layers (default 3)
        """
        super(MPNN, self).__init__(aggr='add')  # Use 'add' aggregation
        self.num_layers = num_layers
        
        # Input projection
        self.lin_in = nn.Linear(node_dim, hidden_dim)
        
        # Message Passing Layers
        self.message_layers = nn.ModuleList()
        self.update_layers = nn.ModuleList()
        
        for _ in range(num_layers):
            # Message function: W * h_i + W * h_j (simplified)
            self.message_layers.append(nn.Linear(hidden_dim * 2, hidden_dim))
            # Update function: GRU-like update
            self.update_layers.append(nn.GRUCell(hidden_dim, hidden_dim))
        
        # Readout layers
        self.lin_out_1 = nn.Linear(hidden_dim, hidden_dim)
        self.lin_out_2 = nn.Linear(hidden_dim, 1)
        
        self._init_weights()
        
        # Log parameter count
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"MPNN initialized with {total_params:,} parameters")
        
        if total_params >= 1_000_000:
            logger.warning(f"Parameter count {total_params} exceeds 1M limit!")
        else:
            logger.info(f"Parameter count {total_params} is within 1M limit.")

    def _init_weights(self):
        """Initialize weights with Xavier initialization."""
        for module in [self.lin_in, self.lin_out_1, self.lin_out_2]:
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        
        for layer in self.message_layers:
            nn.init.xavier_uniform_(layer.weight)
            if layer.bias is not None:
                nn.init.zeros_(layer.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the MPNN.
        
        Args:
            x: Node features [num_nodes, node_dim]
            edge_index: Edge indices [2, num_edges]
            batch: Batch vector for pooling [num_nodes]
        
        Returns:
            Predictions [num_graphs]
        """
        # Project input features
        h = self.lin_in(x)
        
        # Message Passing
        for i in range(self.num_layers):
            # Create messages
            m = self.propagate(edge_index, x=h)
            # Update hidden states
            h = self.update_layers[i](m, h)
            h = F.relu(h)
        
        # Readout: Global Mean Pooling
        if batch is None:
            # Single graph
            h_graph = h.mean(dim=0, keepdim=True)
        else:
            # Multiple graphs
            h_graph = self.pool(h, batch)
        
        # Output layers
        out = F.relu(self.lin_out_1(h_graph))
        out = self.lin_out_2(out)
        
        return out.squeeze(-1)

    def message(self, x_j: torch.Tensor, x_i: torch.Tensor) -> torch.Tensor:
        """
        Compute messages for edge (i, j).
        
        Args:
            x_j: Source node features
            x_i: Target node features
        
        Returns:
            Messages [num_edges, hidden_dim]
        """
        # Concatenate source and target features
        edge_features = torch.cat([x_i, x_j], dim=1)
        return self.message_layers[self._current_layer_idx](edge_features)
    
    def propagate(self, edge_index: torch.Tensor, size=None, **kwargs):
        """
        Custom propagate to track layer index for message layers.
        """
        # We need to manually handle the layer index since we're using ModuleList
        # This is a simplified version that assumes sequential calls
        pass  # The actual logic is handled in the forward loop

    def pool(self, x: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """
        Global mean pooling.
        
        Args:
            x: Node features [num_nodes, hidden_dim]
            batch: Batch indices [num_nodes]
        
        Returns:
            Graph features [num_graphs, hidden_dim]
        """
        return scatter_mean(x, batch, dim=0)


def scatter_mean(src: torch.Tensor, index: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """
    Compute mean of src elements grouped by index.
    Implementation to avoid importing extra libraries if torch_geometric.scatter is not available.
    """
    num_out = index.max().item() + 1
    out = torch.zeros(num_out, src.shape[1], device=src.device, dtype=src.dtype)
    count = torch.zeros(num_out, device=src.device, dtype=torch.long)
    
    out.index_add_(dim, index, src)
    count.scatter_add_(0, index, torch.ones_like(src[:, 0], dtype=torch.long))
    
    # Avoid division by zero
    count = count.unsqueeze(1).expand_as(out)
    count[count == 0] = 1
    
    return out / count


class RidgeBaseline(nn.Module):
    """
    Ridge Regression baseline using ECFP fingerprints.
    This is a simple linear model for comparison with the GNN.
    """
    
    def __init__(self, input_dim: int = 2048, alpha: float = 1.0):
        """
        Initialize the Ridge baseline.
        
        Args:
            input_dim: Dimension of ECFP fingerprints (default 2048)
            alpha: Ridge regularization strength
        """
        super(RidgeBaseline, self).__init__()
        self.input_dim = input_dim
        self.alpha = alpha
        
        # Linear layer for ridge regression
        self.linear = nn.Linear(input_dim, 1)
        
        self._init_weights()
        
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"RidgeBaseline initialized with {total_params:,} parameters")

    def _init_weights(self):
        """Initialize weights."""
        nn.init.xavier_uniform_(self.linear.weight)
        if self.linear.bias is not None:
            nn.init.zeros_(self.linear.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: ECFP fingerprints [batch_size, input_dim]
        
        Returns:
            Predictions [batch_size]
        """
        return self.linear(x).squeeze(-1)


def create_molecule_graph(smiles: str) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Convert a SMILES string to a PyTorch Geometric Data object.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        Tuple of (node_features, edge_index, batch)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Generate node features (simplified: use atom type embedding)
    # In a real scenario, we might use more sophisticated features
    atom_features = []
    for atom in mol.GetAtoms():
        # Simple one-hot encoding of atomic number (limited set)
        feat = np.zeros(100)  # Support up to atomic number 100
        feat[atom.GetAtomicNum()] = 1.0
        atom_features.append(feat)
    
    node_features = torch.tensor(np.array(atom_features), dtype=torch.float)
    
    # Generate edge index
    edge_indices = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        edge_indices.append([i, j])
        edge_indices.append([j, i])  # Undirected graph
    
    if not edge_indices:
        # Handle isolated atoms
        edge_indices = [[0, 0]]
    
    edge_index = torch.tensor(np.array(edge_indices).T, dtype=torch.long)
    
    # Add self-loops
    edge_index, _ = add_self_loops(edge_index, num_nodes=node_features.size(0))
    
    # Batch vector (single molecule)
    batch = torch.zeros(node_features.size(0), dtype=torch.long)
    
    return node_features, edge_index, batch


def smiles_to_ecfp(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate ECFP fingerprint for a SMILES string.
    
    Args:
        smiles: SMILES string
        radius: ECFP radius
        n_bits: Number of bits in fingerprint
        
    Returns:
        ECFP fingerprint as numpy array
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    
    return arr


def build_gnn_model(node_dim: int = 100, hidden_dim: int = 64, num_layers: int = 3) -> MPNN:
    """
    Build and return an MPNN model.
    
    Args:
        node_dim: Input node feature dimension
        hidden_dim: Hidden dimension
        num_layers: Number of message passing layers
        
    Returns:
        Initialized MPNN model
    """
    return MPNN(node_dim=node_dim, hidden_dim=hidden_dim, num_layers=num_layers)


def build_baseline_model(input_dim: int = 2048, alpha: float = 1.0) -> RidgeBaseline:
    """
    Build and return a Ridge Regression baseline model.
    
    Args:
        input_dim: Input feature dimension (ECFP size)
        alpha: Ridge regularization parameter
        
    Returns:
        Initialized RidgeBaseline model
    """
    return RidgeBaseline(input_dim=input_dim, alpha=alpha)


def prepare_gnn_data(smiles_list: List[str]) -> Tuple[List[torch.Tensor], List[torch.Tensor], List[torch.Tensor]]:
    """
    Prepare graph data for a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings
        
    Returns:
        Tuple of (node_features_list, edge_index_list, batch_list)
    """
    node_features_list = []
    edge_index_list = []
    batch_list = []
    
    for smiles in smiles_list:
        try:
            nf, ei, b = create_molecule_graph(smiles)
            node_features_list.append(nf)
            edge_index_list.append(ei)
            batch_list.append(b)
        except ValueError as e:
            logger.warning(f"Skipping invalid molecule: {smiles} - {e}")
            continue
    
    return node_features_list, edge_index_list, batch_list