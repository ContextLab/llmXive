"""
Molecular Graph Neural Network (MPNN) and Baseline Models.

This module implements:
1. MPNN: A Message Passing Neural Network with 2 layers, mean aggregation,
   designed to have <1M parameters.
2. RidgeBaseline: A baseline model using ECFP fingerprints + Ridge Regression.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops
from torch_geometric.data import Data
from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np
from typing import Tuple, List, Optional
import os
import sys

# Ensure device is CPU-only as per constraints
DEVICE = torch.device('cpu')

class MPNNLayer(MessagePassing):
    """
    A single Message Passing layer with mean aggregation.
    """
    def __init__(self, in_channels: int, out_channels: int):
        super(MPNNLayer, self).__init__(aggr='mean')
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Message MLP
        self.message_mlp = nn.Sequential(
            nn.Linear(in_channels * 2, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )

        # Update MLP
        self.update_mlp = nn.Sequential(
            nn.Linear(in_channels + out_channels, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # x: [N, in_channels]
        # edge_index: [2, E]
        # Propagate messages
        out = self.propagate(edge_index, x=x)
        
        # Update node features
        # Concat original x with aggregated messages
        out = torch.cat([x, out], dim=1)
        out = self.update_mlp(out)
        return out

    def message(self, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
        # x_i: target, x_j: source
        msg_input = torch.cat([x_i, x_j], dim=1)
        return self.message_mlp(msg_input)

class MPNN(nn.Module):
    """
    Message Passing Neural Network for molecular property prediction.
    
    Architecture:
    - 2 Message Passing Layers
    - Mean aggregation
    - Global mean pooling
    - 2-layer MLP head
    
    Target: <1M parameters.
    """
    def __init__(self, in_features: int = 2048, hidden_dim: int = 128, 
                 num_layers: int = 2, out_features: int = 1):
        super(MPNN, self).__init__()
        
        self.embedding = nn.Linear(in_features, hidden_dim)
        
        # 2 MPNN layers
        self.mpnn_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.mpnn_layers.append(MPNNLayer(hidden_dim, hidden_dim))
        
        # Global pooling (mean)
        # Then MLP head
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, out_features)
        )
        
        self._init_weights()
        self._count_params()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def _count_params(self):
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        # Log to ensure <1M constraint
        print(f"Model Parameters: Total={total_params:,}, Trainable={trainable_params:,}")
        if trainable_params >= 1_000_000:
            print(f"WARNING: Model has {trainable_params} params, exceeds 1M limit.")
        else:
            print(f"OK: Model has {trainable_params} params (<1M).")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Node features [N, in_features]
            edge_index: [2, E]
            batch: Batch vector [N] (optional, for multiple graphs)
        Returns:
            predictions: [num_graphs]
        """
        # Embedding
        x = self.embedding(x)
        x = F.relu(x)
        
        # Message Passing
        for layer in self.mpnn_layers:
            x = layer(x, edge_index)
            x = F.relu(x)
        
        # Global Pooling
        if batch is None:
            # Single graph case
            graph_repr = x.mean(dim=0, keepdim=True)
        else:
            # Multiple graphs case
            from torch_geometric.nn import global_mean_pool
            graph_repr = global_mean_pool(x, batch)
        
        # Head
        out = self.head(graph_repr)
        return out

class RidgeBaseline(nn.Module):
    """
    Baseline model: ECFP fingerprints + Ridge Regression (via MLP with L2 penalty).
    Implemented as a simple Linear layer with L2 regularization in the loss.
    """
    def __init__(self, input_dim: int = 2048, hidden_dim: int = 128):
        super(RidgeBaseline, self).__init__()
        self.fc = nn.Linear(input_dim, 1)
        self.alpha = 1.0  # Ridge penalty coefficient

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)

    def compute_loss(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        mse = F.mse_loss(preds, targets)
        l2_reg = torch.tensor(0., requires_grad=True, device=preds.device)
        for param in self.fc.parameters():
            l2_reg += torch.norm(param) ** 2
        return mse + self.alpha * l2_reg

def create_molecule_graph(smiles: str) -> Optional[Data]:
    """
    Convert a SMILES string to a PyTorch Geometric Data object.
    
    Features: ECFP6 fingerprints (2048 bits) used as node features.
    For simplicity in this baseline, we treat the molecule as a single node
    with the full fingerprint, or we can map atoms to bits.
    
    To strictly follow GNN, we map atoms to features.
    Strategy:
    1. Parse SMILES with RDKit.
    2. For each atom, generate a local fingerprint (radius 1).
    3. Edge features: bond type.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Ensure Hs are added for feature completeness
    mol = Chem.AddHs(mol)
    
    num_atoms = mol.GetNumAtoms()
    if num_atoms == 0:
        return None
        
    # Node features: ECFP-like local environment (simplified to atom type + degree)
    # We will use a fixed-size vector representing atom properties
    # For this implementation, we use a simple one-hot of atom type + degree
    # To match the MPNN input dim of 2048, we can pad or use a learned embedding.
    # However, the MPNN expects in_features=2048.
    # Let's generate a 2048-bit Morgan fingerprint for the WHOLE molecule
    # and split it? No, that's not local.
    
    # Alternative: Use a pre-computed global fingerprint as a single node graph
    # or use a small feature set and embed it to 2048.
    # Given the constraint of <1M params and simplicity, let's use the 
    # global fingerprint as a single-node graph for the baseline,
    # but for the GNN, we need atom-level.
    
    # Let's use a simple atom feature vector: [atomic_num, degree, formal_charge, is_aromatic]
    # Then embed to hidden_dim. But MPNN is defined with fixed in_features=2048.
    # We will map atom features to 2048 via an embedding layer inside MPNN?
    # No, MPNN constructor takes in_features.
    
    # Let's assume the input to the model is already processed.
    # Here we construct the graph structure.
    # We will use a dummy feature of size 2048 for now, filled with atom properties.
    
    # Better approach for GNN:
    # 1. Atom features: One-hot of element (100 dims) + properties.
    # 2. Embed these to 2048? Or just use 2048 as the hidden size and input is small.
    # The MPNN class above expects in_features=2048.
    # Let's generate a 2048-bit Morgan fingerprint for the molecule.
    # And treat the molecule as a single node? That's not a GNN.
    # Let's treat each atom as a node, and use a 2048-bit fingerprint 
    # computed for the atom's environment (radius 2).
    
    atom_features = []
    for atom in mol.GetAtoms():
        # Generate local fingerprint for this atom
        fp = AllChem.GetMorganFingerprintAsBitVect(atom, 2, nBits=2048)
        arr = np.zeros(2048, dtype=np.float32)
        for idx in fp.GetOnBits():
            arr[idx] = 1.0
        atom_features.append(arr)
    
    x = torch.tensor(np.array(atom_features), dtype=torch.float)
    
    # Edges
    row, col = [], []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        row.append(i)
        col.append(j)
        row.append(j)
        col.append(i)
    
    if len(row) == 0:
        # Single atom molecule
        edge_index = torch.tensor([[0], [0]], dtype=torch.long)
    else:
        edge_index = torch.tensor([row, col], dtype=torch.long)
    
    # Add self loops if needed (handled in MPNNLayer if we want, but good to have)
    edge_index, _ = add_self_loops(edge_index, num_nodes=num_atoms)
    
    return Data(x=x, edge_index=edge_index)

def smiles_to_ecfp(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate ECFP fingerprint for a SMILES string.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.float32)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros(n_bits, dtype=np.float32)
    for idx in fp.GetOnBits():
        arr[idx] = 1.0
    return arr

def build_gnn_model(hidden_dim: int = 128) -> MPNN:
    """
    Factory function to build the MPNN model.
    """
    return MPNN(in_features=2048, hidden_dim=hidden_dim, num_layers=2)

def build_baseline_model(input_dim: int = 2048) -> RidgeBaseline:
    """
    Factory function to build the RidgeBaseline model.
    """
    return RidgeBaseline(input_dim=input_dim)

def prepare_gnn_data(df: 'pd.DataFrame') -> Tuple[List[Data], List[float]]:
    """
    Prepare a list of PyTorch Geometric Data objects and targets from a dataframe.
    """
    import pandas as pd
    graphs = []
    targets = []
    for _, row in df.iterrows():
        smiles = row['smi']
        lam_max = row['lambda_max']
        graph = create_molecule_graph(smiles)
        if graph is not None:
            graphs.append(graph)
            targets.append(lam_max)
    return graphs, targets