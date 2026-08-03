"""
Utility functions for molecular graph construction from SMILES.

This module provides the core functionality to convert SMILES strings into
graph representations (nodes and edges) suitable for Graph Neural Networks.
It handles molecule parsing, feature extraction, and graph validation.
"""
from typing import List, Dict, Tuple, Any, Optional, Set
import logging
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdchem

logger = logging.getLogger("utils.graph_utils")

def smiles_to_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit molecule object.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        RDKit Mol object or None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
        return mol
    except Exception as e:
        logger.error(f"Error parsing SMILES {smiles}: {e}")
        return None

def get_node_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract node features for a molecule.
    
    Features extracted per atom:
    1. Atomic number (int)
    2. Hybridization state (encoded as int)
    3. Formal charge (int)
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Numpy array of shape (N_atoms, 3) containing node features.
    """
    features = []
    for atom in mol.GetAtoms():
        # Atomic number
        atomic_num = atom.GetAtomicNum()
        
        # Hybridization
        hybridization = atom.GetHybridization()
        
        # Formal charge
        formal_charge = atom.GetFormalCharge()
        
        # Encode hybridization as integer
        hybrid_map = {
            rdchem.HybridizationType.S: 0,
            rdchem.HybridizationType.SP: 1,
            rdchem.HybridizationType.SP2: 2,
            rdchem.HybridizationType.SP3: 3,
            rdchem.HybridizationType.SP3D: 4,
            rdchem.HybridizationType.SP3D2: 5,
            rdchem.HybridizationType.UNSPECIFIED: 6
        }
        hybrid_val = hybrid_map.get(hybridization, 6)
        
        features.append([float(atomic_num), float(hybrid_val), float(formal_charge)])
        
    return np.array(features, dtype=np.float32)

def get_edge_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract edge features for a molecule.
    
    Features extracted per bond:
    1. Start atom index (int)
    2. End atom index (int)
    3. Bond type (encoded as int)
    4. Conjugation flag (int: 0 or 1)
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Numpy array of shape (N_bonds, 4) containing edge features.
    """
    edges = []
    for bond in mol.GetBonds():
        start = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        
        # Bond type
        bond_type = bond.GetBondType()
        # Conjugation
        conjugated = bond.GetIsConjugated()
        
        # Encode bond type
        type_map = {
            rdchem.BondType.SINGLE: 0,
            rdchem.BondType.DOUBLE: 1,
            rdchem.BondType.TRIPLE: 2,
            rdchem.BondType.AROMATIC: 3
        }
        type_val = type_map.get(bond_type, 0)
        
        edges.append([float(start), float(end), float(type_val), float(int(conjugated))])
        
    return np.array(edges, dtype=np.float32)

def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph dictionary.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        Dictionary with 'nodes', 'edges', and 'smiles' keys, or None if parsing fails.
        'nodes' is a numpy array of shape (N, 3).
        'edges' is a numpy array of shape (M, 4).
    """
    mol = smiles_to_molecule(smiles)
    if mol is None:
        return None
        
    node_features = get_node_features(mol)
    edge_features = get_edge_features(mol)
    
    return {
        "smiles": smiles,
        "nodes": node_features,
        "edges": edge_features
    }

def batch_smiles_to_graphs(smiles_list: List[str]) -> List[Optional[Dict[str, Any]]]:
    """
    Convert a list of SMILES strings to graph dictionaries.
    
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
    Validate a graph dictionary.
    
    Checks:
    - Required keys present: 'nodes', 'edges', 'smiles'
    - 'nodes' is a 2D numpy array
    - 'edges' is a 2D numpy array
    - 'smiles' is a string
    
    Args:
        graph: Graph dictionary.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(graph, dict):
        return False
        
    if "nodes" not in graph or "edges" not in graph or "smiles" not in graph:
        return False
        
    if not isinstance(graph["nodes"], np.ndarray) or graph["nodes"].ndim != 2:
        return False
        
    if not isinstance(graph["edges"], np.ndarray) or graph["edges"].ndim != 2:
        return False
        
    if not isinstance(graph["smiles"], str):
        return False
        
    return True

def get_feature_dimensions() -> Dict[str, int]:
    """
    Get the dimensions of node and edge features.
    
    Returns:
        Dictionary with 'node_features' and 'edge_features' dimensions.
    """
    return {
        "node_features": 3,  # atomic_num, hybridization, formal_charge
        "edge_features": 4   # start, end, bond_type, conjugated
    }

if __name__ == "__main__":
    # Basic test
    test_smiles = "CCO"
    graph = smiles_to_graph(test_smiles)
    if graph:
        print(f"Graph for {test_smiles}:")
        print(f"  Nodes shape: {graph['nodes'].shape}")
        print(f"  Edges shape: {graph['edges'].shape}")
        print(f"  Valid: {validate_graph(graph)}")
    else:
        print(f"Failed to generate graph for {test_smiles}")