"""
Utility functions for molecular graph construction from SMILES.
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
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Numpy array of node features.
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
        
        features.append([atomic_num, hybrid_val, formal_charge])
        
    return np.array(features, dtype=np.float32)

def get_edge_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract edge features for a molecule.
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Numpy array of edge features.
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
        
        edges.append([start, end, type_val, int(conjugated)])
        
    return np.array(edges, dtype=np.float32)

def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph dictionary.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        Dictionary with 'nodes', 'edges', and 'smiles' keys, or None if parsing fails.
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
    return [smiles_to_graph(smiles) for smiles in smiles_list]

def validate_graph(graph: Dict[str, Any]) -> bool:
    """
    Validate a graph dictionary.
    
    Args:
        graph: Graph dictionary.
        
    Returns:
        True if valid, False otherwise.
    """
    if "nodes" not in graph or "edges" not in graph or "smiles" not in graph:
        return False
    if not isinstance(graph["nodes"], np.ndarray) or graph["nodes"].ndim != 2:
        return False
    if not isinstance(graph["edges"], np.ndarray) or graph["edges"].ndim != 2:
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
    # Test
    test_smiles = "CCO"
    graph = smiles_to_graph(test_smiles)
    if graph:
        print(f"Graph for {test_smiles}: {graph}")
    else:
        print(f"Failed to generate graph for {test_smiles}")
