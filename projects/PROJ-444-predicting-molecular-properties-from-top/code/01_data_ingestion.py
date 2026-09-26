import os
import sys
import logging
import random
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# --- Logging Setup ---
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def pin_random_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)

# --- Data Fetching ---
def fetch_esol_dataset() -> pd.DataFrame:
    """
    Fetches the ESOL dataset from MoleculeNet (via HuggingFace datasets).
    Returns a DataFrame with 'smiles' and 'logP' (or 'measured logP') columns.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("The 'datasets' package is required. Install with: pip install datasets")

    logger = logging.getLogger("data_ingestion")
    logger.info("Fetching ESOL dataset from HuggingFace MoleculeNet...")
    
    # MoleculeNet ESOL is available on HuggingFace
    try:
        dataset = load_dataset("moleculenet", "esol", split="train")
    except Exception as e:
        logger.error(f"Failed to fetch ESOL dataset: {e}")
        # Fail loudly - no synthetic fallback
        raise SystemExit(1) from e

    df = dataset.to_pandas()
    
    # Standardize column names if necessary
    # HuggingFace MoleculeNet ESOL usually has 'smiles', 'measured logP', 'experimental logP'
    # We need 'smiles' and 'logP' (or map the measured one to logP)
    if 'smiles' not in df.columns:
        logger.error("Column 'smiles' not found in dataset.")
        raise SystemExit(1)
    
    # Map the logP column. Common names: 'measured logP', 'experimental logP'
    logp_col = None
    for col in ['measured logP', 'experimental logP', 'logP']:
        if col in df.columns:
            logp_col = col
            break
    
    if logp_col:
        df = df.rename(columns={logp_col: 'logP'})
        logger.info(f"Renamed '{logp_col}' to 'logP'.")
    else:
        logger.error("Could not find a logP column in the dataset.")
        raise SystemExit(1)

    return df[['smiles', 'logP']].dropna()

# --- Validation ---
def validate_schema(df: pd.DataFrame) -> bool:
    """Validates that the dataframe has the required columns."""
    required_cols = {'smiles', 'logP'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        logging.getLogger("data_ingestion").error(f"Missing required columns: {missing}")
        return False
    return True

# --- Power Analysis ---
def perform_power_analysis(df: pd.DataFrame) -> None:
    """
    Performs a priori power analysis.
    Requirement: N >= 128.
    """
    n = len(df)
    logger = logging.getLogger("data_ingestion")
    logger.info(f"Dataset size: {n}")
    
    if n < 128:
        logger.error(f"Power analysis failed: N={n} < 128. Cannot proceed.")
        raise SystemExit(1)
    else:
        logger.info(f"Power analysis passed: N={n} >= 128.")

# --- Scaffold Logic ---
def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Bemis-Murcko scaffold SMILES for a given molecule.
    Returns None if the molecule is invalid or has no scaffold.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None

def enforce_scaffold_check(df: pd.DataFrame) -> None:
    """
    Enforces that there are at least 100 unique scaffolds.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info("Counting unique scaffolds...")
    
    # Apply scaffold extraction in a safe way
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold)
    unique_scaffolds = scaffolds.dropna().unique()
    n_scaffolds = len(unique_scaffolds)
    
    logger.info(f"Found {n_scaffolds} unique scaffolds.")
    
    if n_scaffolds < 100:
        logger.error(f"Scaffold check failed: {n_scaffolds} < 100 unique scaffolds.")
        raise SystemExit(1)
    else:
        logger.info(f"Scaffold check passed: {n_scaffolds} >= 100 unique scaffolds.")

def scaffold_split(df: pd.DataFrame, n_folds: int = 5, seed: int = 42) -> Dict[str, List[int]]:
    """
    Performs a scaffold-based split of the dataframe.
    Returns a dictionary mapping fold names to lists of row indices.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info(f"Performing {n_folds}-fold scaffold split with seed={seed}...")
    
    pin_random_seed(seed)
    
    # Get scaffolds
    df_temp = df.copy()
    df_temp['scaffold'] = df_temp['smiles'].apply(get_bemis_murcko_scaffold)
    df_temp = df_temp.dropna(subset=['scaffold']) # Drop molecules without valid scaffolds
    
    # Group by scaffold
    scaffold_groups = df_temp.groupby('scaffold').indices
    scaffold_list = list(scaffold_groups.keys())
    
    # Shuffle scaffolds
    random.shuffle(scaffold_list)
    
    # Distribute scaffolds into folds
    fold_indices = {f'fold_{i}': [] for i in range(n_folds)}
    
    for i, scaffold in enumerate(scaffold_list):
        fold_idx = i % n_folds
        indices = scaffold_groups[scaffold]
        fold_indices[f'fold_{fold_idx}'].extend(indices.tolist())
    
    # Validate fold sizes (ensure no empty folds if possible, though scaffold distribution can be uneven)
    for fold_name, indices in fold_indices.items():
        if not indices:
            logger.warning(f"Fold {fold_name} is empty.")
    
    logger.info("Scaffold split completed.")
    return fold_indices

def main():
    """
    Main entry point for data ingestion and splitting.
    1. Fetch ESOL
    2. Validate Schema
    3. Power Analysis (N>=128)
    4. Scaffold Check (>=100)
    5. Scaffold Split (5-fold)
    6. Save splits to data/processed/splits.json
    """
    logger = setup_logging()
    logger.info("Starting Data Ingestion Pipeline (T008a + T008b)...")
    
    # 1. Fetch
    try:
        df = fetch_esol_dataset()
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Critical error fetching data: {e}")
        raise SystemExit(1)
    
    # 2. Validate
    if not validate_schema(df):
        raise SystemExit(1)
    
    # 3. Power Analysis
    perform_power_analysis(df)
    
    # 4. Scaffold Check
    enforce_scaffold_check(df)
    
    # 5. Split
    splits = scaffold_split(df, n_folds=5, seed=42)
    
    # 6. Save
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "splits.json"
    
    with open(output_file, 'w') as f:
        json.dump(splits, f, indent=2)
    
    logger.info(f"Splits saved to {output_file}")
    logger.info("Data Ingestion Pipeline completed successfully.")

if __name__ == "__main__":
    main()
