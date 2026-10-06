import os
import sys
import logging
import json
from typing import Dict, List, Tuple, Any, Optional

import torch
from torch_geometric.data import Data
from torch_geometric.utils import to_networkx
import networkx as nx
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
import numpy as np

# Project local imports (matching API surface)
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, log_execution_summary

def setup_script_logging():
    """Initialize logging for the split data script."""
    logger = setup_logging("03_split_data")
    return logger

def load_intermediate_graphs(file_path: str) -> List[Tuple[int, Data]]:
    """
    Load the intermediate graphs from the PyTorch Geometric format file.
    
    Args:
        file_path: Path to the .pt file containing graphs.
        
    Returns:
        List of tuples (index, graph_data).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Intermediate graphs file not found: {file_path}")
    
    try:
        # Load the entire list of Data objects
        data_list = torch.load(file_path, weights_only=False)
        if not isinstance(data_list, list):
            raise ValueError(f"Expected a list of Data objects, got {type(data_list)}")
        
        logger = logging.getLogger("03_split_data")
        logger.info(f"Loaded {len(data_list)} graphs from {file_path}")
        
        return [(i, data) for i, data in enumerate(data_list)]
    except Exception as e:
        raise RuntimeError(f"Failed to load intermediate graphs: {e}")

def smiles_to_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Convert a SMILES string to its Murcko Scaffold.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Canonical SMILES of the Murcko scaffold, or None if conversion fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None:
            return None
        
        # Convert back to SMILES
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger = logging.getLogger("03_split_data")
        logger.warning(f"Failed to generate scaffold for SMILES: {smiles}, Error: {e}")
        return None

def get_scaffold_from_graph(data: Data, smiles_key: str = "smiles") -> Optional[str]:
    """
    Extract the scaffold from a PyTorch Geometric Data object.
    
    This assumes the Data object contains a 'smiles' attribute or can be
    converted back to a molecule. If 'smiles' is not present, we try to
    infer from node features or raise an error if not possible.
    
    For this implementation, we assume the 'smiles' string is stored in
    data.smiles or data.y (if y is a string) or we need to reconstruct.
    However, typically in T014a, the SMILES is preserved.
    
    Strategy: Check for 'smiles' attribute. If not, try to reconstruct from
    graph structure if node features allow, but primarily rely on stored SMILES.
    """
    if hasattr(data, 'smiles'):
        return smiles_to_murcko_scaffold(data.smiles)
    
    # Fallback: Check if SMILES is stored in a different attribute
    if hasattr(data, 'y') and isinstance(data.y, str):
        return smiles_to_murcko_scaffold(data.y)
        
    # If we cannot find the SMILES, we cannot compute the scaffold reliably.
    # In a robust pipeline, T014a should ensure SMILES is attached to the graph.
    logger = logging.getLogger("03_split_data")
    logger.error("Could not find SMILES in graph data. Cannot compute scaffold.")
    return None

def murcko_scaffold_split(
    data_list: List[Tuple[int, Data]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[int], List[int], List[int]]:
    """
    Perform a Murcko Scaffold split on the dataset.
    
    Args:
        data_list: List of (index, Data) tuples.
        train_ratio: Fraction of data for training.
        val_ratio: Fraction of data for validation.
        test_ratio: Fraction of data for testing.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_indices, val_indices, test_indices).
    """
    if not (abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6):
        raise ValueError("Ratios must sum to 1.0")
    
    np.random.seed(seed)
    
    # Map scaffold -> list of indices
    scaffold_to_indices: Dict[str, List[int]] = {}
    invalid_indices: List[int] = []
    
    logger = logging.getLogger("03_split_data")
    logger.info("Computing Murcko scaffolds for all molecules...")
    
    for idx, data in data_list:
        scaffold = get_scaffold_from_graph(data)
        if scaffold is None:
            invalid_indices.append(idx)
        else:
            if scaffold not in scaffold_to_indices:
                scaffold_to_indices[scaffold] = []
            scaffold_to_indices[scaffold].append(idx)
    
    if invalid_indices:
        logger.warning(f"Skipping {len(invalid_indices)} molecules with invalid scaffolds.")
    
    if not scaffold_to_indices:
        raise ValueError("No valid scaffolds found to split.")
    
    # Sort scaffolds by size (descending) to ensure larger scaffolds are distributed first
    sorted_scaffolds = sorted(scaffold_to_indices.keys(), key=lambda k: len(scaffold_to_indices[k]), reverse=True)
    
    train_indices: List[int] = []
    val_indices: List[int] = []
    test_indices: List[int] = []
    
    # Shuffle the list of scaffolds to randomize distribution
    np.random.shuffle(sorted_scaffolds)
    
    # Simple greedy assignment: assign each scaffold entirely to train, val, or test
    # based on the current accumulated counts to maintain ratios as close as possible.
    current_train = 0
    current_val = 0
    current_test = 0
    total_molecules = sum(len(indices) for indices in scaffold_to_indices.values())
    
    target_train = int(total_molecules * train_ratio)
    target_val = int(total_molecules * val_ratio)
    target_test = total_molecules - target_train - target_val  # Ensure sum matches total
    
    for scaffold in sorted_scaffolds:
        indices = scaffold_to_indices[scaffold]
        n = len(indices)
        
        # Determine which set this scaffold should go to
        # Priority: Fill Train -> Fill Val -> Fill Test
        if current_train + n <= target_train:
            train_indices.extend(indices)
            current_train += n
        elif current_val + n <= target_val:
            val_indices.extend(indices)
            current_val += n
        else:
            test_indices.extend(indices)
            current_test += n
    
    # Shuffle the indices within each set to randomize order
    np.random.shuffle(train_indices)
    np.random.shuffle(val_indices)
    np.random.shuffle(test_indices)
    
    logger.info(f"Split complete: Train={len(train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")
    return train_indices, val_indices, test_indices

def save_indices_to_pt(indices: List[int], file_path: str):
    """
    Save a list of indices to a PyTorch .pt file.
    
    Args:
        indices: List of integer indices.
        file_path: Output path.
    """
    try:
        torch.save(indices, file_path)
        logger = logging.getLogger("03_split_data")
        logger.info(f"Saved indices to {file_path} (count: {len(indices)})")
    except Exception as e:
        raise RuntimeError(f"Failed to save indices to {file_path}: {e}")

def main():
    """Main entry point for the script."""
    logger = setup_script_logging()
    log_execution_summary(logger, "Starting Murcko Scaffold Split")
    
    config = get_config()
    ensure_directories(config)
    
    # Paths
    intermediate_path = config.get('paths', {}).get('intermediate_graphs', 'data/processed/graphs_intermediate.pt')
    splits_dir = config.get('paths', {}).get('splits_dir', 'data/processed/splits')
    
    # Ensure splits directory exists
    os.makedirs(splits_dir, exist_ok=True)
    
    train_file = os.path.join(splits_dir, 'train_indices.pt')
    val_file = os.path.join(splits_dir, 'val_indices.pt')
    test_file = os.path.join(splits_dir, 'test_indices.pt')
    
    try:
        # Load graphs
        data_list = load_intermediate_graphs(intermediate_path)
        
        # Perform split
        train_indices, val_indices, test_indices = murcko_scaffold_split(data_list)
        
        # Save results
        save_indices_to_pt(train_indices, train_file)
        save_indices_to_pt(val_indices, val_file)
        save_indices_to_pt(test_indices, test_file)
        
        # Log metrics
        log_metric("split_train_count", len(train_indices))
        log_metric("split_val_count", len(val_indices))
        log_metric("split_test_count", len(test_indices))
        
        log_execution_summary(logger, "Murcko Scaffold Split completed successfully")
        
    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        log_execution_summary(logger, "Murcko Scaffold Split failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
