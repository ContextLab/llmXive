"""
Scaffold-aware data splitting for DSSC molecular datasets.

Implements Bemis-Murcko scaffold extraction and 5-fold cross-validation
splitting to ensure no scaffold overlap between train and test sets.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from collections import defaultdict

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import MolToSmiles
    from rdkit.Chem.Scaffolds import MurckoScaffold
    from rdkit import RDLogger
except ImportError:
    raise ImportError(
        "RDKit is required for scaffold extraction. "
        "Please install it via `pip install rdkit`."
    )

# Disable RDKit warnings
RDLogger.DisableLog('rdApp.*')

# Import project utilities
from utils.config import get_config, ensure_dirs
from utils.logger import setup_logger
from utils.data_loader import load_csv

logger = setup_logger(__name__)

def extract_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold for a given SMILES string.

    Args:
        smiles: Input SMILES string.

    Returns:
        Canonical SMILES of the scaffold, or None if extraction fails.
    """
    try:
        mol = Chem.SmilesToMol(smiles)
        if mol is None:
            return None
        
        # Generate scaffold
        scaffold_mol = MurckoScaffold.MakeScaffoldGeneric(mol)
        if scaffold_mol is None:
            return None

        # Convert back to SMILES
        scaffold_smiles = MolToSmiles(scaffold_mol)
        return scaffold_smiles
    except Exception as e:
        logger.warning(f"Failed to extract scaffold for SMILES '{smiles}': {e}")
        return None

def get_scaffold_groups(df: pd.DataFrame, smiles_col: str = 'canonical_smiles') -> Dict[str, List[int]]:
    """
    Group molecule indices by their Bemis-Murcko scaffold.

    Args:
        df: DataFrame containing molecular data.
        smiles_col: Name of the column containing canonical SMILES.

    Returns:
        Dictionary mapping scaffold SMILES to list of molecule indices.
    """
    logger.info("Extracting Bemis-Murcko scaffolds...")
    scaffold_map = defaultdict(list)
    
    # Process in batches to avoid memory issues
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        scaffold = extract_bemis_murcko_scaffold(smiles)
        if scaffold:
            scaffold_map[scaffold].append(idx)
        else:
            logger.warning(f"Skipping molecule at index {idx} due to scaffold extraction failure.")
    
    logger.info(f"Extracted {len(scaffold_map)} unique scaffolds from {len(df)} molecules.")
    return dict(scaffold_map)

def scaffold_split(
    scaffold_groups: Dict[str, List[int]],
    n_folds: int = 5,
    seed: int = 42,
    min_scaffold_size: int = 1
) -> List[Tuple[List[int], List[int]]]:
    """
    Perform scaffold-aware stratified 5-fold cross-validation split.

    Ensures that no scaffold appears in both training and test sets.
    Splits are based on scaffolds, not individual molecules.

    Args:
        scaffold_groups: Dictionary mapping scaffold SMILES to molecule indices.
        n_folds: Number of folds (default 5).
        seed: Random seed for reproducibility.
        min_scaffold_size: Minimum number of molecules per scaffold to be considered.

    Returns:
        List of (train_indices, test_indices) tuples for each fold.
    """
    logger.info(f"Performing scaffold-aware split with {n_folds} folds...")
    
    # Filter scaffolds with sufficient size
    valid_scaffolds = [
        (scaffold, indices) 
        for scaffold, indices in scaffold_groups.items() 
        if len(indices) >= min_scaffold_size
    ]
    
    if len(valid_scaffolds) < n_folds:
        raise ValueError(
            f"Not enough scaffolds ({len(valid_scaffolds)}) to create {n_folds} folds "
            f"with minimum size {min_scaffold_size}."
        )
    
    # Extract scaffold indices
    scaffold_indices = [indices for _, indices in valid_scaffolds]
    
    # Shuffle scaffolds
    np.random.seed(seed)
    np.random.shuffle(scaffold_indices)
    
    splits = []
    total_scaffolds = len(scaffold_indices)
    
    for fold in range(n_folds):
        # Test scaffolds for this fold
        start_idx = fold * (total_scaffolds // n_folds)
        end_idx = start_idx + (total_scaffolds // n_folds)
        
        if fold == n_folds - 1:
            # Last fold takes remaining scaffolds
            end_idx = total_scaffolds

        test_scaffolds = scaffold_indices[start_idx:end_idx]
        train_scaffolds = scaffold_indices[:start_idx] + scaffold_indices[end_idx:]

        # Flatten indices
        test_indices = [idx for scaffold in test_scaffolds for idx in scaffold]
        train_indices = [idx for scaffold in train_scaffolds for idx in scaffold]

        splits.append((train_indices, test_indices))

    logger.info(f"Created {len(splits)} scaffold-aware splits.")
    return splits

def save_split_indices(
    splits: List[Tuple[List[int], List[int]]],
    output_path: Path,
    fold_size: int = 5
) -> None:
    """
    Save split indices to a JSON file.

    Args:
        splits: List of (train, test) index tuples.
        output_path: Path to save the JSON file.
        fold_size: Number of folds.
    """
    ensure_dirs([output_path.parent])
    
    data = {
        "n_folds": fold_size,
        "folds": []
    }
    
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        data["folds"].append({
            "fold_id": fold_idx,
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "train_indices": train_idx,
            "test_indices": test_idx
        })

    with open(output_path, 'w') as f:
        import json
        json.dump(data, f, indent=2)

    logger.info(f"Saved split indices to {output_path}")

def main():
    """
    Main entry point for scaffold-aware data splitting.

    Reads cleaned data from data/processed/cleaned_data.csv,
    extracts scaffolds, performs 5-fold split, and saves results.
    """
    config = get_config()
    data_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
    results_dir = Path(config.get('RESULTS_DIR', 'results'))
    
    input_file = data_dir / "cleaned_data.csv"
    output_file = results_dir / "scaffold_splits.json"
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}. "
            "Please run preprocess.py first to generate cleaned_data.csv."
        )

    # Load data
    df = load_csv(str(input_file))
    logger.info(f"Loaded {len(df)} molecules from {input_file}")

    # Verify required column
    if 'canonical_smiles' not in df.columns:
        raise ValueError(
            "Column 'canonical_smiles' not found in input data. "
            "Please ensure preprocess.py generated canonical SMILES."
        )

    # Extract scaffolds
    scaffold_groups = get_scaffold_groups(df, smiles_col='canonical_smiles')

    # Perform split
    splits = scaffold_split(scaffold_groups, n_folds=5, seed=config.get('SEED', 42))

    # Save results
    save_split_indices(splits, output_file, fold_size=5)

    # Log summary
    for i, (train_idx, test_idx) in enumerate(splits):
        logger.info(f"Fold {i}: Train={len(train_idx)}, Test={len(test_idx)}")

    logger.info("Scaffold-aware splitting completed successfully.")

if __name__ == "__main__":
    main()