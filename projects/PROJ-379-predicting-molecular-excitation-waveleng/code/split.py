import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import numpy as np

from utils import get_logger, parse_smiles, setup_logging

logger = get_logger(__name__)

def generate_bemis_murcko_scaffold(smiles: str) -> str:
    """
    Generate Bemis-Murcko scaffold for a given SMILES string.
    
    Args:
        smiles: Input SMILES string.
        
    Returns:
        Canonical SMILES of the scaffold.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    
    scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
    if scaffold is None:
        return None
    
    return Chem.MolToSmiles(scaffold)

def assign_scaffolds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign scaffold IDs to each molecule in the DataFrame.
    
    Args:
        df: DataFrame with 'smi' column.
        
    Returns:
        DataFrame with added 'scaffold_id' column.
    """
    logger.info("Assigning Bemis-Murcko scaffolds...")
    
    scaffolds = []
    for smi in df['smi']:
        scaffold_smi = generate_bemis_murcko_scaffold(smi)
        scaffolds.append(scaffold_smi)
    
    df['scaffold_id'] = scaffolds
    return df

def scaffold_split(df: pd.DataFrame, train_ratio: float = 0.7, val_ratio: float = 0.15, test_ratio: float = 0.15) -> Tuple[List[int], List[int], List[int]]:
    """
    Split data into train/val/test sets based on scaffolds.
    
    Args:
        df: DataFrame with 'scaffold_id'.
        train_ratio: Fraction for training.
        val_ratio: Fraction for validation.
        test_ratio: Fraction for testing.
        
    Returns:
        Tuple of (train_indices, val_indices, test_indices).
    """
    logger.info("Performing scaffold split...")
    
    # Group by scaffold
    scaffold_groups = df.groupby('scaffold_id').indices
    
    # Shuffle scaffold groups
    scaffold_ids = list(scaffold_groups.keys())
    np.random.shuffle(scaffold_ids)
    
    # Calculate split sizes
    n_scaffolds = len(scaffold_ids)
    n_train = int(n_scaffolds * train_ratio)
    n_val = int(n_scaffolds * val_ratio)
    
    train_scaffolds = set(scaffold_ids[:n_train])
    val_scaffolds = set(scaffold_ids[n_train:n_train + n_val])
    test_scaffolds = set(scaffold_ids[n_train + n_val:])
    
    # Explicitly verify no overlap
    if train_scaffolds & val_scaffolds:
        raise ValueError("Scaffold overlap detected between train and val splits!")
    if train_scaffolds & test_scaffolds:
        raise ValueError("Scaffold overlap detected between train and test splits!")
    if val_scaffolds & test_scaffolds:
        raise ValueError("Scaffold overlap detected between val and test splits!")
    
    # Assign indices
    train_indices = []
    val_indices = []
    test_indices = []
    
    for idx, row in df.iterrows():
        scaffold = row['scaffold_id']
        if scaffold in train_scaffolds:
            train_indices.append(idx)
        elif scaffold in val_scaffolds:
            val_indices.append(idx)
        else:
            test_indices.append(idx)
    
    logger.info(f"Split statistics:")
    logger.info(f"  Train: {len(train_indices)} molecules ({len(train_scaffolds)} scaffolds)")
    logger.info(f"  Val: {len(val_indices)} molecules ({len(val_scaffolds)} scaffolds)")
    logger.info(f"  Test: {len(test_indices)} molecules ({len(test_scaffolds)} scaffolds)")
    
    return train_indices, val_indices, test_indices

def main():
    """
    Main execution function for data splitting.
    """
    setup_logging()
    logger.info("Starting split pipeline...")
    
    try:
        # Load cleaned data
        input_path = Path("data/processed/cleaned.csv")
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        
        # Assign scaffolds
        df = assign_scaffolds(df)
        
        # Perform split
        train_idx, val_idx, test_idx = scaffold_split(df)
        
        # Save split indices
        output_path = Path("data/processed/split_indices.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        split_data = {
            "train_idx": train_idx,
            "val_idx": val_idx,
            "test_idx": test_idx
        }
        
        with open(output_path, 'w') as f:
            json.dump(split_data, f, indent=2)
        
        logger.info(f"Split indices saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Split pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()