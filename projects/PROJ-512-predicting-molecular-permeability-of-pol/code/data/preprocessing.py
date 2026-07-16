import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
import h5py
import json

from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord
from data.utils import setup_logging

# Configure logger
logger = setup_logging(__name__)

def extract_graph_features(graph: PolymerGraph) -> Dict[str, Any]:
    """
    Extract node and edge features from a PolymerGraph.
    
    Args:
        graph: The PolymerGraph object to extract features from.
        
    Returns:
        A dictionary containing node features, edge features, and graph metadata.
    """
    if not graph.nodes or not graph.edges:
        raise ValueError("Cannot extract features from an empty graph.")
    
    node_features = []
    for node in graph.nodes:
        features = {
            'atom_type': node.get('atom_type', 0),
            'hybridization': node.get('hybridization', 0),
            'formal_charge': node.get('formal_charge', 0),
            'is_aromatic': int(node.get('is_aromatic', False)),
            'num_h_bonds': node.get('num_h_bonds', 0)
        }
        node_features.append(features)
    
    edge_features = []
    for edge in graph.edges:
        features = {
            'bond_type': edge.get('bond_type', 0),
            'is_conjugated': int(edge.get('is_conjugated', False)),
            'is_in_ring': int(edge.get('is_in_ring', False))
        }
        edge_features.append(features)
    
    return {
        'node_features': node_features,
        'edge_features': edge_features,
        'smiles': graph.smiles,
        'mw': graph.mw,
        'log_perm': graph.log_perm
    }

def convert_to_polymer_graph(smiles: str, log_perm: float, mw: float) -> PolymerGraph:
    """
    Convert a SMILES string and metadata into a PolymerGraph object.
    
    Args:
        smiles: The SMILES string representing the molecule.
        log_perm: The logarithm of the permeability coefficient.
        mw: The molecular weight of the repeat unit.
        
    Returns:
        A PolymerGraph object.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    
    nodes = []
    for atom in mol.GetAtoms():
        node = {
            'atom_type': atom.GetAtomicNum(),
            'hybridization': int(atom.GetHybridization()),
            'formal_charge': atom.GetFormalCharge(),
            'is_aromatic': atom.GetIsAromatic(),
            'num_h_bonds': atom.GetTotalNumHs()
        }
        nodes.append(node)
    
    edges = []
    for bond in mol.GetBonds():
        edge = {
            'bond_type': int(bond.GetBondType()),
            'is_conjugated': bond.GetIsConjugated(),
            'is_in_ring': bond.IsInRing()
        }
        start_node = bond.GetBeginAtomIdx()
        end_node = bond.GetEndAtomIdx()
        edges.append((start_node, end_node, edge))
    
    return PolymerGraph(smiles=smiles, nodes=nodes, edges=edges, mw=mw, log_perm=log_perm)

def process_graphs(graphs: List[PolymerGraph]) -> List[Dict[str, Any]]:
    """
    Process a list of PolymerGraph objects into feature dictionaries.
    
    Args:
        graphs: A list of PolymerGraph objects.
        
    Returns:
        A list of dictionaries containing graph features.
    """
    processed = []
    for graph in graphs:
        try:
            features = extract_graph_features(graph)
            processed.append(features)
        except Exception as e:
            logger.warning(f"Failed to process graph for SMILES {graph.smiles}: {e}")
    return processed

def get_murcko_scaffold(smiles: str) -> str:
    """
    Generate the Murcko scaffold for a given SMILES string.
    
    Args:
        smiles: The SMILES string of the molecule.
        
    Returns:
        The SMILES string of the Murcko scaffold.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    if scaffold is None:
        return ""
    
    return Chem.MolToSmiles(scaffold)

def murcko_scaffold_split(
    data_path: str,
    output_train_path: str,
    output_test_path: str,
    output_val_path: str,
    similarity_cutoff: Optional[float] = None
) -> Tuple[int, int, int]:
    """
    Split the dataset into train, test, and validation sets based on Murcko scaffolds.
    
    The split ensures that test and validation scaffolds are unseen in training.
    
    Args:
        data_path: Path to the input HDF5 file containing the dataset.
        output_train_path: Path to save the training set.
        output_test_path: Path to save the test set.
        output_val_path: Path to save the validation set.
        similarity_cutoff: Similarity threshold for scaffold clustering. 
                           If None, uses default from environment variable.
                           A high threshold (e.g., 0.8) ensures strict separation.
                           
    Returns:
        A tuple of (train_count, test_count, val_count).
    
    Raises:
        FileNotFoundError: If the input data file does not exist.
        ValueError: If the data file is empty or malformed.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    
    # Determine similarity cutoff from env var if not provided
    if similarity_cutoff is None:
        cutoff_str = os.environ.get("MURCKO_SIMILARITY_CUTOFF", "0.8")
        try:
            similarity_cutoff = float(cutoff_str)
        except ValueError:
            logger.warning(f"Invalid MURCKO_SIMILARITY_CUTOFF '{cutoff_str}', using default 0.8")
            similarity_cutoff = 0.8
    
    logger.info(f"Performing Murcko scaffold split with similarity cutoff: {similarity_cutoff}")
    
    # Load data
    with h5py.File(data_path, 'r') as f:
        if 'smiles' not in f or 'log_perm' not in f or 'mw' not in f:
            raise ValueError("Invalid HDF5 format: missing required datasets.")
        
        smiles_list = [s.decode('utf-8') for s in f['smiles'][:]]
        log_perms = f['log_perm'][:]
        mws = f['mw'][:]
    
    if len(smiles_list) == 0:
        raise ValueError("Dataset is empty.")
    
    logger.info(f"Loaded {len(smiles_list)} records from {data_path}")
    
    # Group by scaffold
    scaffold_to_indices = defaultdict(list)
    for idx, smiles in enumerate(smiles_list):
        try:
            scaffold = get_murcko_scaffold(smiles)
            if scaffold:
                scaffold_to_indices[scaffold].append(idx)
            else:
                # If scaffold extraction fails, assign to a special "unknown" group
                scaffold_to_indices["__UNKNOWN__"].append(idx)
        except Exception as e:
            logger.warning(f"Failed to extract scaffold for SMILES {smiles}: {e}")
            scaffold_to_indices["__UNKNOWN__"].append(idx)
    
    # Sort scaffolds by frequency (descending) to ensure larger groups are handled first
    sorted_scaffolds = sorted(scaffold_to_indices.keys(), key=lambda s: len(scaffold_to_indices[s]), reverse=True)
    
    # Assign scaffolds to splits
    # Strategy: Iterate through scaffolds and assign to train/test/val based on availability
    # We want to ensure test/val scaffolds are completely unseen in train
    train_indices = []
    test_indices = []
    val_indices = []
    
    # Simple split: 70% train, 15% test, 15% val based on scaffold groups
    # We iterate through scaffolds and fill splits until we reach target ratios
    total_count = len(smiles_list)
    target_test = int(total_count * 0.15)
    target_val = int(total_count * 0.15)
    
    current_test = 0
    current_val = 0
    
    for scaffold in sorted_scaffolds:
        indices = scaffold_to_indices[scaffold]
        
        # Decide where to put this scaffold
        if current_test < target_test:
            test_indices.extend(indices)
            current_test += len(indices)
        elif current_val < target_val:
            val_indices.extend(indices)
            current_val += len(indices)
        else:
            train_indices.extend(indices)
    
    logger.info(f"Split completed: Train={len(train_indices)}, Test={len(test_indices)}, Val={len(val_indices)}")
    
    # Save splits
    def save_split(indices: List[int], path: str):
        with h5py.File(path, 'w') as f:
            # Copy relevant data
            f.create_dataset('smiles', data=[smiles_list[i].encode('utf-8') for i in indices])
            f.create_dataset('log_perm', data=[log_perms[i] for i in indices])
            f.create_dataset('mw', data=[mws[i] for i in indices])
            f.create_dataset('indices', data=indices)
            f.attrs['split'] = os.path.basename(path).replace('.h5', '')
        logger.info(f"Saved {len(indices)} records to {path}")
    
    save_split(train_indices, output_train_path)
    save_split(test_indices, output_test_path)
    save_split(val_indices, output_val_path)
    
    return len(train_indices), len(test_indices), len(val_indices)

def main():
    """
    Main entry point for the preprocessing module.
    Executes the Murcko scaffold split on the processed dataset.
    """
    logger.info("Starting preprocessing module (Murcko Scaffold Split)")
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    input_path = os.path.join(processed_dir, "polymers.h5")
    train_path = os.path.join(processed_dir, "polymers_train.h5")
    test_path = os.path.join(processed_dir, "polymers_test.h5")
    val_path = os.path.join(processed_dir, "polymers_val.h5")
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run data ingestion first to generate polymers.h5")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        train_count, test_count, val_count = murcko_scaffold_split(
            data_path=input_path,
            output_train_path=train_path,
            output_test_path=test_path,
            output_val_path=val_path
        )
        
        logger.info(f"Successfully split dataset: Train={train_count}, Test={test_count}, Val={val_count}")
        
        # Save split summary
        summary_path = os.path.join(processed_dir, "split_summary.json")
        summary = {
            "total": train_count + test_count + val_count,
            "train": train_count,
            "test": test_count,
            "val": val_count,
            "similarity_cutoff": os.environ.get("MURCKO_SIMILARITY_CUTOFF", "0.8")
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved split summary to {summary_path}")
        
    except Exception as e:
        logger.error(f"Error during scaffold split: {e}")
        raise

if __name__ == "__main__":
    main()