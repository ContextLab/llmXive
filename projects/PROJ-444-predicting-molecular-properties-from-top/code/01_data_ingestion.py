"""
Data Ingestion Module for Molecular Property Prediction.

This module handles fetching the ESOL dataset, validating schema,
performing power analysis, enforcing scaffold constraints, and
generating scaffold-based train/test splits.
"""
import os
import sys
import logging
import random
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Constants
MIN_SAMPLES = 128
MIN_SCAFFOLDS = 100
SPLIT_FOLDS = 5
SEED = 42
DATA_PROCESSED_DIR = Path("data/processed")
DATA_RAW_DIR = Path("data/raw")
LOGS_DIR = Path("data/logs")

def setup_logging() -> logging.Logger:
    """Configure logging for the ingestion pipeline."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "ingestion.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def pin_random_seed(seed: int = SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def fetch_esol_dataset(logger: logging.Logger) -> pd.DataFrame:
    """
    Fetch the ESOL dataset from a real source.
    
    Uses the MoleculeNet dataset via the `moleculenet` package or direct URL.
    If `moleculenet` is not available, falls back to the direct CSV URL from
    the MoleculeNet repository.
    """
    logger.info("Fetching ESOL dataset...")
    
    # Attempt to use the openml/moleculenet source if available, otherwise direct fetch
    # Direct URL from MoleculeNet GitHub
    esol_url = "https://raw.githubusercontent.com/bp-kelley/datasets-csv/master/esol.csv"
    
    try:
        # Try fetching directly
        df = pd.read_csv(esol_url)
        if df.empty:
            raise ValueError("Downloaded dataset is empty")
        logger.info(f"Successfully fetched {len(df)} rows from ESOL dataset.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch ESOL dataset: {e}")
        raise SystemExit(1) from e

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate that the dataframe contains required columns: 'smiles' and 'logP'.
    """
    required_cols = {'smiles', 'logP'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    return True

def perform_power_analysis(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Perform a priori power analysis.
    Requires N >= MIN_SAMPLES (128).
    """
    n = len(df)
    logger.info(f"Power Analysis: Sample size N = {n}")
    if n < MIN_SAMPLES:
        logger.error(f"Power Insufficient: N={n} < {MIN_SAMPLES}")
        return False
    logger.info("Power analysis passed.")
    return True

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold for a given SMILES string.
    Returns the scaffold SMILES or None if invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None:
            return None
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None

def enforce_scaffold_check(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Enforce the minimum scaffold count constraint.
    Computes unique scaffolds for all valid molecules.
    Requires unique scaffolds >= MIN_SCAFFOLDS (100).
    """
    logger.info("Computing unique scaffolds...")
    scaffolds = []
    valid_count = 0
    
    for smiles in df['smiles']:
        scaffold = get_bemis_murcko_scaffold(smiles)
        if scaffold:
            scaffolds.append(scaffold)
            valid_count += 1
    
    unique_scaffolds = set(scaffolds)
    count = len(unique_scaffolds)
    logger.info(f"Unique scaffolds found: {count} (from {valid_count} valid molecules)")
    
    if count < MIN_SCAFFOLDS:
        logger.error(f"Scaffold Insufficient: {count} < {MIN_SCAFFOLDS}")
        return False
    
    logger.info("Scaffold validation passed.")
    return True

def scaffold_split(df: pd.DataFrame, n_folds: int = SPLIT_FOLDS, seed: int = SEED) -> Dict[str, List[int]]:
    """
    Perform a scaffold-based split of the dataset.
    
    1. Compute scaffolds for all molecules.
    2. Group molecules by scaffold.
    3. Shuffle scaffold groups.
    4. Distribute scaffold groups into n_folds buckets.
    5. Return indices for each fold.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Performing scaffold split with {n_folds} folds (seed={seed})")
    
    # Compute scaffolds
    df['scaffold'] = df['smiles'].apply(get_bemis_murcko_scaffold)
    df = df.dropna(subset=['scaffold']).reset_index(drop=True)
    
    # Group by scaffold
    scaffold_groups = df.groupby('scaffold').indices
    
    # Get list of scaffolds and shuffle them
    scaffold_list = list(scaffold_groups.keys())
    rng = np.random.RandomState(seed)
    rng.shuffle(scaffold_list)
    
    # Initialize folds
    folds = [[] for _ in range(n_folds)]
    
    # Distribute scaffold groups into folds (round-robin)
    for i, scaffold in enumerate(scaffold_list):
        fold_idx = i % n_folds
        molecule_indices = scaffold_groups[scaffold].tolist()
        folds[fold_idx].extend(molecule_indices)
    
    # Convert to dictionary
    split_indices = {f"fold_{i}": indices for i, indices in enumerate(folds)}
    
    logger.info(f"Split complete. Fold sizes: {[len(v) for v in split_indices.values()]}")
    return split_indices

def save_splits(split_indices: Dict[str, List[int]], logger: logging.Logger) -> None:
    """
    Save split indices to data/processed/splits.json.
    """
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_PROCESSED_DIR / "splits.json"
    
    with open(output_path, 'w') as f:
        json.dump(split_indices, f, indent=2)
    
    logger.info(f"Saved split indices to {output_path}")

def main() -> None:
    """Main entry point for data ingestion and splitting."""
    logger = setup_logging()
    pin_random_seed()
    
    try:
        # 1. Fetch Data
        df = fetch_esol_dataset(logger)
        
        # 2. Validate Schema
        if not validate_schema(df, logger):
            raise SystemExit(1)
        
        # 3. Power Analysis
        if not perform_power_analysis(df, logger):
            raise SystemExit(1)
        
        # 4. Scaffold Validation
        if not enforce_scaffold_check(df, logger):
            raise SystemExit(1)
        
        # 5. Perform Split
        split_indices = scaffold_split(df)
        
        # 6. Save Splits
        save_splits(split_indices, logger)
        
        logger.info("Data ingestion and splitting completed successfully.")
        
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()