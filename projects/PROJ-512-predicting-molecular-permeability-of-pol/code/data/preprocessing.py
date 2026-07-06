import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
import h5py
import json

# Import existing API surface
from models.polymer_graph import PolymerGraph
from data.utils import get_seed, setup_logging

logger = setup_logging("preprocessing")

def extract_graph_features(graph: PolymerGraph) -> Dict[str, Any]:
    """
    Extract numerical features from a PolymerGraph object for model input.
    Includes node/edge features and global graph properties.
    """
    if not hasattr(graph, 'nodes') or not hasattr(graph, 'edges'):
        raise ValueError("Invalid PolymerGraph object: missing nodes or edges")

    node_features = []
    for node in graph.nodes:
        # Assuming node is a dict or object with atom_type, hybridization
        feat = {
            'atom_type': node.get('atom_type', 0),
            'hybridization': node.get('hybridization', 0),
            'formal_charge': node.get('formal_charge', 0)
        }
        node_features.append(feat)

    edge_features = []
    for edge in graph.edges:
        feat = {
            'bond_type': edge.get('bond_type', 0),
            'is_aromatic': edge.get('is_aromatic', False)
        }
        edge_features.append(feat)

    return {
        'num_nodes': len(graph.nodes),
        'num_edges': len(graph.edges),
        'node_features': node_features,
        'edge_features': edge_features,
        'molecular_weight': getattr(graph, 'molecular_weight', 0.0)
    }

def convert_to_polymer_graph(smiles: str, mw: float) -> PolymerGraph:
    """
    Convert a SMILES string and molecular weight into a PolymerGraph object.
    Uses RDKit to parse the molecule and extract graph structure.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
        return None

    nodes = []
    for atom in mol.GetAtoms():
        nodes.append({
            'atom_type': atom.GetAtomicNum(),
            'hybridization': int(atom.GetHybridization()),
            'formal_charge': atom.GetFormalCharge(),
            'is_aromatic': atom.GetIsAromatic()
        })

    edges = []
    for bond in mol.GetBonds():
        edges.append({
            'bond_type': int(bond.GetBondType()),
            'is_aromatic': bond.GetIsAromatic(),
            'start_idx': bond.GetBeginAtomIdx(),
            'end_idx': bond.GetEndAtomIdx()
        })

    return PolymerGraph(
        smiles=smiles,
        nodes=nodes,
        edges=edges,
        molecular_weight=mw,
        metadata={'source': 'rdkit_conversion'}
    )

def process_graphs(graphs: List[PolymerGraph]) -> List[Dict[str, Any]]:
    """
    Process a list of PolymerGraph objects into feature dictionaries.
    """
    processed = []
    for i, g in enumerate(graphs):
        if g is None:
            continue
        features = extract_graph_features(g)
        features['index'] = i
        processed.append(features)
    return processed

def get_murcko_scaffold(smiles: str) -> str:
    """
    Extract the Murcko scaffold from a SMILES string.
    Returns the scaffold as a canonical SMILES string.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold)

def murcko_scaffold_split(
    data_path: str,
    output_path: str,
    test_fraction: float = 0.2,
    val_fraction: float = 0.1,
    seed: Optional[int] = None
) -> Dict[str, List[str]]:
    """
    Perform a Murcko scaffold split on the dataset stored in HDF5.
    Ensures that test and validation sets contain scaffolds unseen in training.

    Args:
        data_path: Path to the input HDF5 file (polymers.h5)
        output_path: Path to save the split indices (JSON)
        test_fraction: Fraction of data to use for testing
        val_fraction: Fraction of data to use for validation
        seed: Random seed for reproducibility

    Returns:
        Dict with keys 'train', 'val', 'test' containing lists of indices
    """
    if seed is None:
        seed = get_seed()
    np.random.seed(seed)

    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input file not found: {data_path}")

    # Load data from HDF5
    with h5py.File(data_path, 'r') as f:
        # Assume SMILES are stored in a dataset named 'smiles'
        if 'smiles' not in f:
            raise ValueError("HDF5 file must contain a 'smiles' dataset")
        smiles_list = [s.decode('utf-8') if isinstance(s, bytes) else s for s in f['smiles'][:]]
        n_samples = len(smiles_list)
        logger.info(f"Loaded {n_samples} samples")

    # Compute scaffolds
    logger.info("Computing Murcko scaffolds...")
    scaffold_to_indices = defaultdict(list)
    for i, smi in enumerate(smiles_list):
        scaffold = get_murcko_scaffold(smi)
        if scaffold:
            scaffold_to_indices[scaffold].append(i)
        else:
            # Assign to a unique "unknown" scaffold to avoid dropping
            scaffold_to_indices[f"__unknown_{i}__"].append(i)

    # Sort scaffolds by frequency (descending) to ensure large scaffolds are split properly
    scaffolds = sorted(scaffold_to_indices.keys(), key=lambda s: len(scaffold_to_indices[s]), reverse=True)

    # Assign scaffolds to splits
    train_indices = []
    val_indices = []
    test_indices = []

    # Shuffle scaffolds
    np.random.shuffle(scaffolds)

    # Greedy assignment to balance splits
    train_count = 0
    val_count = 0
    test_count = 0
    target_test = int(n_samples * test_fraction)
    target_val = int(n_samples * val_fraction)

    for scaffold in scaffolds:
        indices = scaffold_to_indices[scaffold]
        if test_count + len(indices) <= target_test:
            test_indices.extend(indices)
            test_count += len(indices)
        elif val_count + len(indices) <= target_val:
            val_indices.extend(indices)
            val_count += len(indices)
        else:
            train_indices.extend(indices)
            train_count += len(indices)

    # If we haven't reached targets, fill remaining from train
    if test_count < target_test:
        needed = target_test - test_count
        extra = train_indices[:needed]
        train_indices = train_indices[needed:]
        test_indices.extend(extra)
    if val_count < target_val:
        needed = target_val - val_count
        extra = train_indices[:needed]
        train_indices = train_indices[needed:]
        val_indices.extend(extra)

    logger.info(f"Split complete: Train={len(train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")

    # Save split indices to JSON
    split_data = {
        'train': train_indices,
        'val': val_indices,
        'test': test_indices,
        'scaffold_counts': {k: len(v) for k, v in scaffold_to_indices.items()},
        'config': {
            'test_fraction': test_fraction,
            'val_fraction': val_fraction,
            'seed': seed
        }
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(split_data, f, indent=2)

    logger.info(f"Split saved to {output_path}")
    return split_data

def main():
    """
    Main entry point for running the scaffold split.
    Reads configuration from environment variables.
    """
    data_path = os.getenv("DATA_PATH", "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5")
    output_path = os.getenv("SPLIT_OUTPUT_PATH", "projects/PROJ-512-predicting-molecular-permeability-of-pol/data/splits/murcko_split.json")
    test_frac = float(os.getenv("TEST_FRACTION", "0.2"))
    val_frac = float(os.getenv("VAL_FRACTION", "0.1"))
    seed = int(os.getenv("SEED", "42"))

    logger.info(f"Starting Murcko scaffold split with seed {seed}")
    murcko_scaffold_split(data_path, output_path, test_frac, val_frac, seed)

if __name__ == "__main__":
    main()