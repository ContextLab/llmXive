"""
Graph construction utilities for molecular data.

Converts SMILES strings to graph representations (nodes and edges)
suitable for Graph Neural Networks.

Dependencies: rdkit, numpy
"""

from typing import List, Dict, Tuple, Any, Optional, Set
import logging
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdchem, Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

# Feature dimensions (must match model expectations)
# Node features: [atom_type, degree, num_h, hybridization, is_aromatic, charge, chiral]
# Edge features: [bond_type, is_conjugated, is_in_ring, stereo]

ATOM_FEATURE_DIM = 7
BOND_FEATURE_DIM = 4

# Atom type mapping (simplified periodic table)
ATOM_TYPES = [
    'C', 'N', 'O', 'S', 'P', 'F', 'Cl', 'Br', 'I', 'B', 'Si', 'As',
    'Se', 'Te', 'At', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn', 'Li', 'Na',
    'K', 'Rb', 'Cs', 'Mg', 'Ca', 'Sr', 'Ba', 'Ti', 'Fe', 'Cu', 'Zn',
    'Ag', 'Au', 'Pd', 'Pt', 'Hg', 'Cd', 'Co', 'Ni', 'Mn', 'Cr', 'V',
    'Other'
]

# Bond type mapping
BOND_TYPES = [
    Chem.rdchem.BondType.SINGLE,
    Chem.rdchem.BondType.DOUBLE,
    Chem.rdchem.BondType.TRIPLE,
    Chem.rdchem.BondType.AROMATIC
]

# Hybridization mapping
HYBRIDIZATION_TYPES = [
    Chem.rdchem.HybridizationType.SP,
    Chem.rdchem.HybridizationType.SP2,
    Chem.rdchem.HybridizationType.SP3,
    Chem.rdchem.HybridizationType.SP3D,
    Chem.rdchem.HybridizationType.SP3D2,
    Chem.rdchem.HybridizationType.OTHER
]

def smiles_to_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit molecule object.
    
    Args:
        smiles: SMILES string representation of a molecule
        
    Returns:
        RDKit Mol object or None if parsing fails
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
        
        # Add hydrogens for accurate feature extraction
        mol = Chem.AddHs(mol)
        return mol
    except Exception as e:
        logger.error(f"Error parsing SMILES '{smiles}': {e}")
        return None

def get_atom_feature(atom: Chem.Atom) -> np.ndarray:
    """
    Extract feature vector for a single atom.
    
    Args:
        atom: RDKit Atom object
        
    Returns:
        Feature vector of length ATOM_FEATURE_DIM
    """
    features = np.zeros(ATOM_FEATURE_DIM, dtype=np.float32)
    
    # 1. Atom type (one-hot encoded index)
    symbol = atom.GetSymbol()
    try:
        features[0] = ATOM_TYPES.index(symbol)
    except ValueError:
        features[0] = ATOM_TYPES.index('Other')
    
    # 2. Degree (number of bonds)
    degree = atom.GetDegree()
    features[1] = min(degree, 10) / 10.0  # Normalize to [0, 1]
    
    # 3. Number of implicit hydrogens
    num_h = atom.GetTotalNumHs()
    features[2] = min(num_h, 5) / 5.0  # Normalize
    
    # 4. Hybridization
    hybridization = atom.GetHybridization()
    try:
        features[3] = HYBRIDIZATION_TYPES.index(hybridization) / len(HYBRIDIZATION_TYPES)
    except ValueError:
        features[3] = 0.5  # Default for unknown
    
    # 5. Is aromatic
    features[4] = 1.0 if atom.GetIsAromatic() else 0.0
    
    # 6. Formal charge
    charge = atom.GetFormalCharge()
    features[5] = min(max(charge / 5.0, -1.0), 1.0)  # Clamp to [-1, 1]
    
    # 7. Chirality
    chiral_tag = atom.GetChiralTag()
    features[6] = 1.0 if chiral_tag != Chem.rdchem.ChiralType.CHI_UNSPECIFIED else 0.0
    
    return features

def get_node_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract node features for all atoms in a molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        2D array of shape (num_atoms, ATOM_FEATURE_DIM)
    """
    atoms = mol.GetAtoms()
    num_atoms = mol.GetNumAtoms()
    
    if num_atoms == 0:
        return np.zeros((0, ATOM_FEATURE_DIM), dtype=np.float32)
    
    features = np.zeros((num_atoms, ATOM_FEATURE_DIM), dtype=np.float32)
    for i, atom in enumerate(atoms):
        features[i] = get_atom_feature(atom)
    
    return features

def get_bond_feature(bond: Chem.Bond) -> np.ndarray:
    """
    Extract feature vector for a single bond.
    
    Args:
        bond: RDKit Bond object
        
    Returns:
        Feature vector of length BOND_FEATURE_DIM
    """
    features = np.zeros(BOND_FEATURE_DIM, dtype=np.float32)
    
    # 1. Bond type
    bond_type = bond.GetBondType()
    try:
        features[0] = BOND_TYPES.index(bond_type) / len(BOND_TYPES)
    except ValueError:
        features[0] = 0.0  # Default for unknown
    
    # 2. Is conjugated
    features[1] = 1.0 if bond.GetIsConjugated() else 0.0
    
    # 3. Is in ring
    features[2] = 1.0 if bond.IsInRing() else 0.0
    
    # 4. Stereo configuration
    stereo = bond.GetStereo()
    # Map stereo to a normalized value
    if stereo == Chem.rdchem.BondStereo.STEREONONE:
        features[3] = 0.0
    elif stereo == Chem.rdchem.BondStereo.STEREOANY:
        features[3] = 0.33
    elif stereo == Chem.rdchem.BondStereo.STEREOZ:
        features[3] = 0.66
    elif stereo == Chem.rdchem.BondStereo.STEREOE:
        features[3] = 1.0
    else:
        features[3] = 0.0
    
    return features

def get_edge_features(mol: Chem.Mol) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract edge features and adjacency for a molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Tuple of (edge_index, edge_features)
        - edge_index: 2D array of shape (2, num_edges) with source and target nodes
        - edge_features: 2D array of shape (num_edges, BOND_FEATURE_DIM)
    """
    bonds = mol.GetBonds()
    num_bonds = mol.GetNumBonds()
    
    if num_bonds == 0:
        return np.zeros((2, 0), dtype=np.int64), np.zeros((0, BOND_FEATURE_DIM), dtype=np.float32)
    
    edge_index = np.zeros((2, num_bonds), dtype=np.int64)
    edge_features = np.zeros((num_bonds, BOND_FEATURE_DIM), dtype=np.float32)
    
    for i, bond in enumerate(bonds):
        edge_index[0, i] = bond.GetBeginAtomIdx()
        edge_index[1, i] = bond.GetEndAtomIdx()
        edge_features[i] = get_bond_feature(bond)
    
    return edge_index, edge_features

def smiles_to_graph(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert a SMILES string to a graph representation.
    
    Args:
        smiles: SMILES string
        
    Returns:
        Dictionary with keys:
            - 'smiles': original SMILES string
            - 'num_nodes': number of atoms
            - 'num_edges': number of bonds
            - 'node_features': 2D numpy array (num_nodes, ATOM_FEATURE_DIM)
            - 'edge_index': 2D numpy array (2, num_edges)
            - 'edge_features': 2D numpy array (num_edges, BOND_FEATURE_DIM)
            - 'is_valid': boolean flag
        Returns None if SMILES parsing fails.
    """
    mol = smiles_to_molecule(smiles)
    if mol is None:
        return None
    
    node_features = get_node_features(mol)
    edge_index, edge_features = get_edge_features(mol)
    
    graph = {
        'smiles': smiles,
        'num_nodes': mol.GetNumAtoms(),
        'num_edges': mol.GetNumBonds(),
        'node_features': node_features,
        'edge_index': edge_index,
        'edge_features': edge_features,
        'is_valid': True
    }
    
    return graph

def batch_smiles_to_graphs(smiles_list: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Convert a batch of SMILES strings to graph representations.
    
    Args:
        smiles_list: List of SMILES strings
        
    Returns:
        Tuple of (valid_graphs, invalid_smiles)
        - valid_graphs: List of graph dictionaries
        - invalid_smiles: List of SMILES strings that failed to parse
    """
    valid_graphs = []
    invalid_smiles = []
    
    for smiles in smiles_list:
        graph = smiles_to_graph(smiles)
        if graph is not None:
            valid_graphs.append(graph)
        else:
            invalid_smiles.append(smiles)
    
    return valid_graphs, invalid_smiles

def validate_graph(graph: Dict[str, Any]) -> bool:
    """
    Validate that a graph dictionary has all required fields and correct shapes.
    
    Args:
        graph: Graph dictionary as produced by smiles_to_graph
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['smiles', 'num_nodes', 'num_edges', 'node_features', 
                    'edge_index', 'edge_features', 'is_valid']
    
    for key in required_keys:
        if key not in graph:
            logger.error(f"Missing required key: {key}")
            return False
    
    # Validate shapes
    if graph['num_nodes'] != graph['node_features'].shape[0]:
        logger.error(f"Node count mismatch: {graph['num_nodes']} vs {graph['node_features'].shape[0]}")
        return False
    
    if graph['node_features'].shape[1] != ATOM_FEATURE_DIM:
        logger.error(f"Node feature dimension mismatch: {graph['node_features'].shape[1]} vs {ATOM_FEATURE_DIM}")
        return False
    
    if graph['num_edges'] != graph['edge_index'].shape[1]:
        logger.error(f"Edge count mismatch: {graph['num_edges']} vs {graph['edge_index'].shape[1]}")
        return False
    
    if graph['edge_features'].shape[0] != graph['num_edges']:
        logger.error(f"Edge feature count mismatch: {graph['edge_features'].shape[0]} vs {graph['num_edges']}")
        return False
    
    if graph['edge_features'].shape[1] != BOND_FEATURE_DIM:
        logger.error(f"Edge feature dimension mismatch: {graph['edge_features'].shape[1]} vs {BOND_FEATURE_DIM}")
        return False
    
    return True

def get_feature_dimensions() -> Dict[str, int]:
    """
    Return the expected feature dimensions for the graph representation.
    
    Returns:
        Dictionary with feature dimension information
    """
    return {
        'node_feature_dim': ATOM_FEATURE_DIM,
        'edge_feature_dim': BOND_FEATURE_DIM,
        'atom_types': len(ATOM_TYPES),
        'bond_types': len(BOND_TYPES),
        'hybridization_types': len(HYBRIDIZATION_TYPES)
    }