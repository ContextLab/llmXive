import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Import from existing project modules
from utils import get_logger, parse_smiles

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "split.log"

# Ensure log directory exists
(PROJECT_ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)

logger = get_logger("split", log_file=str(LOG_FILE))

def generate_bemis_murcko_scaffold(smi: str) -> str:
    """
    Generate Bemis-Murcko scaffold for a given SMILES string.
    Returns the scaffold SMILES or None if generation fails.
    """
    mol = parse_smiles(smi)
    if mol is None:
        return None
    
    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for {smi}: {e}")
        return None

def assign_scaffolds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign scaffold IDs to each molecule in the dataframe.
    """
    logger.info("Assigning Bemis-Murcko scaffolds...")
    scaffold_map = {}
    scaffold_counter = 0
    failed_count = 0

    scaffolds = []
    for idx, row in df.iterrows():
        smi = row["smi"]
        scaffold_smi = generate_bemis_murcko_scaffold(smi)
        
        if scaffold_smi is None:
            failed_count += 1
            scaffolds.append(None)
            continue

        if scaffold_smi not in scaffold_map:
            scaffold_map[scaffold_smi] = f"scaffold_{scaffold_counter}"
            scaffold_counter += 1
        
        scaffolds.append(scaffold_map[scaffold_smi])

    df["scaffold_id"] = scaffolds
    logger.info(f"Total unique scaffolds: {len(scaffold_map)}")
    logger.info(f"Failed scaffold generations: {failed_count}")
    return df

def scaffold_split(df: pd.DataFrame, 
                   train_ratio: float = 0.8, 
                   val_ratio: float = 0.1, 
                   test_ratio: float = 0.1) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data by scaffold to ensure no scaffold appears in multiple splits.
    """
    logger.info("Performing scaffold-based split...")
    
    # Get unique scaffolds
    unique_scaffolds = df["scaffold_id"].unique()
    np.random.shuffle(unique_scaffolds)
    
    n_total = len(unique_scaffolds)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    train_scaffolds = set(unique_scaffolds[:n_train])
    val_scaffolds = set(unique_scaffolds[n_train:n_train + n_val])
    test_scaffolds = set(unique_scaffolds[n_train + n_val:])
    
    logger.info(f"Scaffold counts -> Train: {len(train_scaffolds)}, Val: {len(val_scaffolds)}, Test: {len(test_scaffolds)}")
    
    train_df = df[df["scaffold_id"].isin(train_scaffolds)].reset_index(drop=True)
    val_df = df[df["scaffold_id"].isin(val_scaffolds)].reset_index(drop=True)
    test_df = df[df["scaffold_id"].isin(test_scaffolds)].reset_index(drop=True)
    
    logger.info(f"Sample counts -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    # Log overlap check
    train_scaff = set(train_df["scaffold_id"].unique())
    val_scaff = set(val_df["scaffold_id"].unique())
    test_scaff = set(test_df["scaffold_id"].unique())
    
    if train_scaff & val_scaff or train_scaff & test_scaff or val_scaff & test_scaff:
        logger.error("ERROR: Scaffold overlap detected between splits!")
    else:
        logger.info("SUCCESS: No scaffold overlap between splits.")
    
    return train_df, val_df, test_df

def main():
    """
    Main entry point for data splitting.
    """
    logger.info("Starting data split pipeline...")
    
    input_path = DATA_PROCESSED_DIR / "processed.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} molecules from {input_path}")
    
    # Assign scaffolds
    df_with_scaffolds = assign_scaffolds(df)
    
    # Split data
    train_df, val_df, test_df = scaffold_split(df_with_scaffolds)
    
    # Save splits
    train_path = DATA_PROCESSED_DIR / "train.csv"
    val_path = DATA_PROCESSED_DIR / "val.csv"
    test_path = DATA_PROCESSED_DIR / "test.csv"
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved train ({len(train_df)}), val ({len(val_df)}), test ({len(test_df)}) splits.")
    
    # Log split statistics
    logger.info("Split Statistics:")
    logger.info(f"  Train size: {len(train_df)} ({len(train_df)/len(df):.2%})")
    logger.info(f"  Val size: {len(val_df)} ({len(val_df)/len(df):.2%})")
    logger.info(f"  Test size: {len(test_df)} ({len(test_df)/len(df):.2%})")
    logger.info("Data split pipeline completed.")

if __name__ == "__main__":
    main()