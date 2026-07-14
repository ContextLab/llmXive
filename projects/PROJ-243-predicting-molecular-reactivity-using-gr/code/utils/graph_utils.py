"""
Graph construction utilities for molecular data.

Converts SMILES strings into graph structures with node and edge features
suitable for Graph Neural Networks.

Node Features:
  - Atomic number
  - Hybridization (One-hot: sp, sp2, sp3, sp3d, sp3d2, other)
  - Formal charge
  - Number of hydrogens attached
  - Aromaticity flag

Edge Features:
  - Bond type (One-hot: single, double, triple, aromatic)
  - Conjugation flag
  - In ring flag
"""

from typing import List, Dict, Tuple, Any, Optional
import logging

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdchem

logger = logging.getLogger(__name__)

# Constants for one-hot encoding
HYBRIDIZATION_MAP = {
    rdchem.HybridizationType.SP: 0,
    rdchem.HybridizationType.SP2: 1,
    rdchem.HybridizationType.SP3: 2,
    rdchem.HybridizationType.SP3D: 3,
    rdchem.HybridizationType.SP3D2: 4,
    rdchem.HybridizationType.OTHER: 5,
}

BOND_TYPE_MAP = {
    rdchem.BondType.SINGLE: 0,
    rdchem.BondType.DOUBLE: 1,
    rdchem.BondType.TRIPLE: 2,
    rdchem.BondType.AROMATIC: 3,
}

# Default values for unmapped types
DEFAULT_HYBRIDIZATION_IDX = 5  # OTHER
DEFAULT_BOND_TYPE_IDX = 0      # SINGLE

# Feature dimensions
NUM_HYBRIDIZATION_TYPES = len(HYBRIDIZATION_MAP)
NUM_BOND_TYPES = len(BOND_TYPE_MAP)

def smiles_to_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit molecule object.
    
    Args:
        smiles: SMILES string representation of a molecule.
        
    Returns:
        RDKit Mol object, or None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        
        # Add hydrogens to ensure correct hydrogen counts
        mol = Chem.AddHs(mol)
        return mol
    except Exception as e:
        logger.error(f"Error parsing SMILES '{smiles}': {e}")
        return None

def get_node_features(atom: Chem.Atom) -> np.ndarray:
    """
    Extract node features for a single atom.
    
    Features:
      - Atomic number (integer)
      - Hybridization (one-hot)
      - Formal charge (integer)
      - Number of hydrogens (integer)
      - Aromaticity (binary)
    
    Args:
        atom: RDKit Atom object.
        
    Returns:
        Numpy array of node features.
    """
    atomic_num = atom.GetAtomicNum()
    
    # Hybridization one-hot
    hyb_type = atom.GetHybridization()
    hyb_idx = HYBRIDIZATION_MAP.get(hyb_type, DEFAULT_HYBRIDIZATION_IDX)
    hyb_one_hot = np.zeros(NUM_HYBRIDIZATION_TYPES, dtype=np.int32)
    hyb_one_hot[hyb_idx] = 1
    
    formal_charge = atom.GetFormalCharge()
    num_hydrogens = atom.GetTotalNumHs()
    is_aromatic = 1 if atom.GetIsAromatic() else 0
    
    # Concatenate all features
    # [atomic_num, hyb_one_hot..., formal_charge, num_h, aromatic]
    features = np.concatenate([
        np.array([atomic_num], dtype=np.int32),
        hyb_one_hot,
        np.array([formal_charge], dtype=np.int32),
        np.array([num_hydrogens], dtype=np.int32),
        np.array([is_aromatic], dtype=np.int32),
    ])
    
    return features

def get_edge_features(bond: Chem.Bond) -> np.ndarray:
    """
    Extract edge features for a single bond.
    
    Features:
      - Bond type (one-hot)
      - Conjugation (binary)
      - In ring (binary)
    
    Args:
        bond: RDKit Bond object.
        
    Returns:
        Numpy array of edge features.
    """
    bond_type = bond.GetBondType()
    type_idx = BOND_TYPE_MAP.get(bond_type, DEFAULT_BOND_TYPE_IDX)
    type_one_hot = np.zeros(NUM_BOND_TYPES, dtype=np.int32)
    type_one_hot[type_idx] = 1
    
    is_conjugated = 1 if bond.GetIsConjugated() else 0
    in_ring = 1 if bond.IsInRing() else 0
    
    features = np.concatenate([
        type_one_hot,
        np.array([is_conjugated], dtype=np.int32),
        np.array([in_ring], dtype=np.int32),
    ])
    
    return features

def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph dictionary.
    
    The graph dictionary contains:
      - 'nodes': List of node feature vectors
      - 'edges': List of (src_idx, dst_idx, edge_features) tuples
      - 'smiles': Original SMILES string
      - 'num_nodes': Number of nodes
      - 'num_edges': Number of edges
    
    Args:
        smiles: SMILES string.
        
    Returns:
        Graph dictionary, or None if conversion fails.
    """
    mol = smiles_to_molecule(smiles)
    if mol is None:
        return None
    
    num_atoms = mol.GetNumAtoms()
    nodes = []
    edges = []
    
    # Extract node features
    for atom in mol.GetAtoms():
        node_feat = get_node_features(atom)
        nodes.append(node_feat)
    
    # Extract edge features
    for bond in mol.GetBonds():
        src_idx = bond.GetBeginAtomIdx()
        dst_idx = bond.GetEndAtomIdx()
        edge_feat = get_edge_features(bond)
        edges.append((src_idx, dst_idx, edge_feat))
        
        # RDKit bonds are undirected, but we might want to add reverse edges
        # depending on the GNN implementation. For now, we store one direction.
        # If bidirectional edges are needed, uncomment below:
        # edges.append((dst_idx, src_idx, edge_feat))
    
    graph = {
        'smiles': smiles,
        'nodes': nodes,
        'edges': edges,
        'num_nodes': num_atoms,
        'num_edges': len(edges),
    }
    
    return graph

def batch_smiles_to_graphs(smiles_list: List[str]) -> List[Optional[Dict[str, Any]]]:
    """
    Convert a list of SMILES strings to a list of graph dictionaries.
    
    Args:
        smiles_list: List of SMILES strings.
        
    Returns:
        List of graph dictionaries (None for invalid SMILES).
    """
    graphs = []
    for smiles in smiles_list:
        graph = smiles_to_graph(smiles)
        graphs.append(graph)
    return graphs

def validate_graph(graph: Dict[str, Any]) -> bool:
    """
    Validate a graph dictionary structure.
    
    Args:
        graph: Graph dictionary.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ['nodes', 'edges', 'num_nodes', 'num_edges', 'smiles']
    if not all(key in graph for key in required_keys):
        return False
    
    if not isinstance(graph['nodes'], list) or len(graph['nodes']) != graph['num_nodes']:
        return False
    
    if not isinstance(graph['edges'], list) or len(graph['edges']) != graph['num_edges']:
        return False
    
    # Check node feature dimensions (assuming fixed feature size)
    if graph['num_nodes'] > 0:
        first_node = graph['nodes'][0]
        if not isinstance(first_node, np.ndarray):
            return False
    
    return True

def get_feature_dimensions() -> Dict[str, int]:
    """
    Return the dimensions of node and edge features.
    
    Returns:
        Dictionary with 'node_dim' and 'edge_dim'.
    """
    # Node features: atomic_num(1) + hyb_one_hot(NUM_HYBRIDIZATION_TYPES) + 
    #                 formal_charge(1) + num_h(1) + aromatic(1)
    node_dim = 1 + NUM_HYBRIDIZATION_TYPES + 1 + 1 + 1
    
    # Edge features: type_one_hot(NUM_BOND_TYPES) + conjugated(1) + in_ring(1)
    edge_dim = NUM_BOND_TYPES + 1 + 1
    
    return {
        'node_dim': node_dim,
        'edge_dim': edge_dim,
    }