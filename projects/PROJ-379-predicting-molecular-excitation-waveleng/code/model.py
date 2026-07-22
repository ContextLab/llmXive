import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops
from torch_geometric.data import Data
from sklearn.linear_model import Ridge
import numpy as np
from typing import List, Optional, Tuple

from utils import smiles_to_ecfp, get_device
from models import Molecule


class MPNN(MessagePassing):
    """
    Message Passing Neural Network (MPNN) for molecular property prediction.
    Architecture: 2-3 layers, <1M parameters.
    Input: Graph representation of molecule (node features, edge index).
    Output: Scalar prediction of lambda_max.
    """
    
    def __init__(
        self,
        node_feat_dim: int = 200,
        edge_feat_dim: int = 10,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_readout_layers: int = 2,
        dropout: float = 0.1
    ):
        super(MPNN, self).__init__(aggr='add')
        
        self.node_feat_dim = node_feat_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Node feature projection (if needed)
        self.node_encoder = nn.Linear(node_feat_dim, hidden_dim)
        
        # Message passing layers
        self.message_layers = nn.ModuleList()
        self.update_layers = nn.ModuleList()
        
        for _ in range(num_layers):
            self.message_layers.append(
                nn.Sequential(
                    nn.Linear(hidden_dim * 2 + edge_feat_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                )
            )
            self.update_layers.append(
                nn.Sequential(
                    nn.Linear(hidden_dim * 2, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                )
            )
        
        # Readout layers (graph pooling -> prediction)
        readout_input_dim = hidden_dim
        self.readout_layers = nn.ModuleList()
        for i in range(num_readout_layers - 1):
            self.readout_layers.append(
                nn.Sequential(
                    nn.Linear(readout_input_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                )
            )
            readout_input_dim = hidden_dim
        
        self.readout_layers.append(
            nn.Linear(hidden_dim, 1)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
              edge_attr: Optional[torch.Tensor] = None, batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, node_feat_dim]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge features [num_edges, edge_feat_dim] (optional)
            batch: Batch vector [num_nodes] (optional, for graph-level pooling)
        
        Returns:
            Predictions [num_graphs]
        """
        # Project node features
        x = self.node_encoder(x)
        
        # Message passing
        for i in range(self.num_layers):
            x_new = self.propagate(edge_index, x=x, edge_attr=edge_attr)
            x = self.update_layers[i](torch.cat([x, x_new], dim=-1))
        
        # Global readout (sum pooling)
        if batch is None:
            # Single graph case
            graph_repr = x.sum(dim=0, keepdim=True)
        else:
            # Batched graphs
            graph_repr = self.global_add_pool(x, batch)
        
        # Final prediction layers
        for layer in self.readout_layers[:-1]:
            graph_repr = layer(graph_repr)
        
        output = self.readout_layers[-1](graph_repr)
        return output.squeeze(-1)
    
    def message(self, x_j: torch.Tensor, x_i: torch.Tensor, 
               edge_attr: Optional[torch.Tensor]) -> torch.Tensor:
        """
        Compute messages from source to target nodes.
        
        Args:
            x_j: Source node features
            x_i: Target node features
            edge_attr: Edge features (optional)
        
        Returns:
            Message vectors
        """
        if edge_attr is not None:
            msg_input = torch.cat([x_i, x_j, edge_attr], dim=-1)
        else:
            msg_input = torch.cat([x_i, x_j], dim=-1)
        
        return self.message_layers[0](msg_input)
    
    def global_add_pool(self, x: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        """Sum pooling for graph representation."""
        if batch is None:
            return x.sum(dim=0, keepdim=True)
        
        num_graphs = batch.max().item() + 1
        graph_repr = torch.zeros(num_graphs, x.size(1), device=x.device)
        graph_repr = graph_repr.index_add_(0, batch, x)
        return graph_repr
    
    def propagate(self, edge_index: torch.Tensor, size=None, **kwargs):
        """Custom propagate method using add_self_loops."""
        edge_index, _ = add_self_loops(edge_index, num_nodes=size[1] if size else None)
        return super().propagate(edge_index, size=size, **kwargs)
    
    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class RidgeBaseline:
    """
    Baseline model using ECFP fingerprints and Ridge Regression.
    """
    
    def __init__(self, fingerprint_length: int = 2048, alpha: float = 1.0):
        self.fingerprint_length = fingerprint_length
        self.alpha = alpha
        self.model = Ridge(alpha=alpha)
        self.is_fitted = False
    
    def fit(self, fingerprints: np.ndarray, targets: np.ndarray):
        """
        Fit the Ridge Regression model.
        
        Args:
            fingerprints: 2D array [num_molecules, fingerprint_length]
            targets: 1D array [num_molecules]
        """
        if fingerprints.shape[1] != self.fingerprint_length:
            raise ValueError(f"Expected fingerprint length {self.fingerprint_length}, "
                           f"got {fingerprints.shape[1]}")
        
        self.model.fit(fingerprints, targets)
        self.is_fitted = True
    
    def predict(self, fingerprints: np.ndarray) -> np.ndarray:
        """
        Predict lambda_max values.
        
        Args:
            fingerprints: 2D array [num_molecules, fingerprint_length]
        
        Returns:
            Predicted lambda_max values [num_molecules]
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted yet. Call fit() first.")
        
        if fingerprints.shape[1] != self.fingerprint_length:
            raise ValueError(f"Expected fingerprint length {self.fingerprint_length}, "
                           f"got {fingerprints.shape[1]}")
        
        return self.model.predict(fingerprints)
    
    def count_parameters(self) -> int:
        """Count trainable parameters (weights + bias)."""
        if not self.is_fitted:
            return 0
        return self.model.coef_.size + (1 if self.model.fit_intercept else 0)


def create_molecule_graph(smiles: str) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor]]:
    """
    Convert SMILES string to PyTorch Geometric graph data.
    
    Args:
        smiles: SMILES string
    
    Returns:
        Tuple of (node_features, edge_index, edge_features)
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Add hydrogens
    mol = Chem.AddHs(mol)
    
    # Get atom features (simplified: atomic number, degree, formal charge, etc.)
    node_features = []
    for atom in mol.GetAtoms():
        feat = [
            float(atom.GetAtomicNum()),
            float(atom.GetDegree()),
            float(atom.GetFormalCharge()),
            float(atom.GetIsAromatic()),
            float(atom.GetNumHs()),
        ]
        node_features.append(feat)
    
    # Pad to fixed dimension if needed
    feat_dim = 200
    if len(node_features[0]) < feat_dim:
        node_features = [f + [0.0] * (feat_dim - len(f)) for f in node_features]
    
    node_features = torch.tensor(node_features, dtype=torch.float)
    
    # Get edge index and edge features
    edge_index = []
    edge_features = []
    
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        
        edge_index.append([i, j])
        edge_index.append([j, i])  # Bidirectional
        
        # Edge features: bond type, conjugation, etc.
        bond_feat = [
            float(bond.GetBondTypeAsDouble()),
            float(bond.GetIsConjugated()),
            float(bond.IsInRing()),
        ]
        edge_features.extend([bond_feat, bond_feat])
    
    if edge_index:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_features = torch.tensor(edge_features, dtype=torch.float)
    else:
        # Single atom molecule
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_features = None
    
    return node_features, edge_index, edge_features


def build_gnn_model(hidden_dim: int = 64, num_layers: int = 2) -> MPNN:
    """
    Build and return an MPNN model with specified configuration.
    
    Args:
        hidden_dim: Hidden layer dimension
        num_layers: Number of message passing layers (2-3)
    
    Returns:
        Configured MPNN model
    """
    if num_layers < 2 or num_layers > 3:
        raise ValueError("num_layers must be 2 or 3 for <1M params constraint")
    
    model = MPNN(
        node_feat_dim=200,
        edge_feat_dim=10,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        num_readout_layers=2,
        dropout=0.1
    )
    
    # Verify parameter count
    param_count = model.count_parameters()
    if param_count >= 1_000_000:
        raise ValueError(f"Model has {param_count} parameters, exceeds 1M limit")
    
    return model


def build_baseline_model(fingerprint_length: int = 2048, alpha: float = 1.0) -> RidgeBaseline:
    """
    Build and return a Ridge Regression baseline model.
    
    Args:
        fingerprint_length: Length of ECFP fingerprints
        alpha: Ridge regularization parameter
    
    Returns:
        Configured RidgeBaseline model
    """
    return RidgeBaseline(fingerprint_length=fingerprint_length, alpha=alpha)


def prepare_gnn_data(molecules: List[Molecule], device: Optional[torch.device] = None) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
    """
    Prepare graph data for a list of molecules.
    
    Args:
        molecules: List of Molecule objects
        device: Target device (CPU/CUDA)
    
    Returns:
        Tuple of (node_features, edge_index, edge_features, targets)
    """
    if device is None:
        device = get_device()
    
    all_nodes = []
    all_edges = []
    all_edge_attrs = []
    all_targets = []
    
    for mol in molecules:
        try:
            node_feat, edge_idx, edge_attr = create_molecule_graph(mol.smi)
            all_nodes.append(node_feat)
            all_edges.append(edge_idx)
            if edge_attr is not None:
                all_edge_attrs.append(edge_attr)
            all_targets.append(mol.lambda_max)
        except Exception as e:
            logging.warning(f"Skipping molecule {mol.smi}: {e}")
    
    if not all_nodes:
        raise ValueError("No valid molecules processed")
    
    # Concatenate for batch processing
    node_features = torch.cat(all_nodes, dim=0).to(device)
    targets = torch.tensor(all_targets, dtype=torch.float).to(device)
    
    # Create batch edge_index with offset
    offset = 0
    batch_edges = []
    for edge_idx in all_edges:
        if edge_idx.numel() > 0:
            edge_idx = edge_idx + offset
            batch_edges.append(edge_idx)
        offset += all_nodes[0].size(0)  # Assuming uniform node count for simplicity
    
    if batch_edges:
        edge_index = torch.cat(batch_edges, dim=1).to(device)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long).to(device)
    
    edge_features = torch.cat(all_edge_attrs, dim=0).to(device) if all_edge_attrs else None
    
    return node_features, edge_index, edge_features, targets