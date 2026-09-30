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
from sklearn.model_selection import GroupKFold

# Configuration
MIN_SCAFFOLDS = 100
MIN_SAMPLES_POWER = 128
NUM_FOLDS = 5
RANDOM_SEED = 42
ESOL_DATASET_URL = "https://raw.githubusercontent.com/bp-kelley/datasets-csv/master/ESOL.csv"
# Using a verified source path if available, otherwise fetch URL
# The task requires fetching from a real source. We will use the URL directly.

def setup_logging(log_file: str = "data/logs/ingestion.log") -> logging.Logger:
    """Setup logging configuration."""
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def pin_random_seed(seed: int = RANDOM_SEED) -> None:
    """Pin random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def fetch_esol_dataset(logger: logging.Logger) -> pd.DataFrame:
    """Fetch the ESOL dataset from the real source."""
    logger.info(f"Fetching ESOL dataset from {ESOL_DATASET_URL}...")
    try:
        # Attempt to read directly from URL
        df = pd.read_csv(ESOL_DATASET_URL)
        logger.info(f"Successfully fetched dataset. Shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        # Fail loudly as per constraints
        raise SystemExit(1)

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """Validate required columns exist."""
    required_cols = ["smiles", "logP"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def perform_power_analysis(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Perform a priori power analysis check."""
    n = len(df)
    if n < MIN_SAMPLES_POWER:
        logger.error(f"Power Insufficient: N={n} < {MIN_SAMPLES_POWER}")
        raise SystemExit(1)
    logger.info(f"Power analysis passed: N={n} >= {MIN_SAMPLES_POWER}")

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

def enforce_scaffold_check(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Enforce minimum unique scaffolds requirement."""
    logger.info("Computing unique scaffolds...")
    scaffolds = []
    for smiles in df["smiles"]:
        scaffold = get_bemis_murcko_scaffold(smiles)
        if scaffold:
            scaffolds.append(scaffold)
        else:
            scaffolds.append(None)
    
    df_with_scaffolds = df.copy()
    df_with_scaffolds["_scaffold"] = scaffolds
    
    unique_scaffolds = df_with_scaffolds["_scaffold"].dropna().unique()
    count = len(unique_scaffolds)
    
    if count < MIN_SCAFFOLDS:
        logger.error(f"Scaffold Insufficient: {count} < {MIN_SCAFFOLDS}")
        raise SystemExit(1)
    
    logger.info(f"Scaffold check passed: {count} unique scaffolds >= {MIN_SCAFFOLDS}")
    return df_with_scaffolds

def scaffold_split(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, List[int]]:
    """
    Perform a 5-fold scaffold split.
    Returns a dictionary mapping fold index (0-4) to list of row indices.
    """
    logger.info("Performing scaffold split...")
    
    # Ensure we have the scaffold column
    if "_scaffold" not in df.columns:
        df = enforce_scaffold_check(df, logger)
    
    # Map scaffolds to group IDs (integers)
    unique_scaffolds = df["_scaffold"].unique()
    scaffold_to_group = {s: i for i, s in enumerate(unique_scaffolds)}
    df["_group_id"] = df["_scaffold"].map(scaffold_to_group)
    
    # Use GroupKFold to ensure molecules with same scaffold stay together
    gkf = GroupKFold(n_splits=NUM_FOLDS)
    groups = df["_group_id"].values
    
    splits = {i: [] for i in range(NUM_FOLDS)}
    
    # GroupKFold returns indices for train and test. 
    # We need to assign each row to exactly one fold (the test fold for that iteration).
    # However, standard practice for "splits.json" in this context is often to define
    # the test set for each fold. Let's create a structure where each fold has its test indices.
    
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(df, groups=groups)):
        splits[fold_idx] = test_idx.tolist()
        
    logger.info(f"Split complete. Fold sizes: {[len(splits[i]) for i in range(NUM_FOLDS)]}")
    return splits

def main():
    """Main entry point for data ingestion (Part 2)."""
    logger = setup_logging()
    pin_random_seed()
    
    try:
        # 1. Fetch Data
        df = fetch_esol_dataset(logger)
        
        # 2. Validate Schema
        if not validate_schema(df, logger):
            raise SystemExit(1)
        
        # 3. Power Analysis
        perform_power_analysis(df, logger)
        
        # 4. Scaffold Check & Enforce
        df_with_scaffolds = enforce_scaffold_check(df, logger)
        
        # 5. Scaffold Split
        splits = scaffold_split(df_with_scaffolds, logger)
        
        # 6. Save Splits
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        output_path = "data/processed/splits.json"
        with open(output_path, "w") as f:
            json.dump(splits, f, indent=2)
        
        logger.info(f"Successfully saved splits to {output_path}")
        
    except SystemExit as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()