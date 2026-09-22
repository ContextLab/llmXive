import os
import sys
import logging
import random
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Configuration
MIN_SCAFFOLDS = 100
MIN_SAMPLES = 128
SEED = 42
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Logging setup
def setup_logging() -> logging.Logger:
    """Configure logging for the data ingestion pipeline."""
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def pin_random_seed(seed: int = SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed pinned to {seed}")

def fetch_esol_dataset() -> pd.DataFrame:
    """
    Fetch the ESOL dataset from MoleculeNet via the datasets library.
    This function attempts to load the real dataset. If it fails, it raises an error.
    """
    try:
        from datasets import load_dataset
        logger.info("Attempting to load MoleculeNet ESOL dataset...")
        # The datasets library provides access to MoleculeNet datasets
        # 'molecule_net' is the dataset name, 'esol' is the subset
        ds = load_dataset("molecule_net", "esol", split="train")
        df = ds.to_pandas()
        
        # Ensure column names are lowercase for consistency
        df.columns = df.columns.str.lower()
        
        logger.info(f"Successfully loaded {len(df)} samples from ESOL dataset.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch ESOL dataset: {e}")
        # Fail loudly as per requirements
        raise RuntimeError(f"Data Gap: Could not fetch ESOL dataset. No synthetic fallback. Error: {e}")

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains required columns: 'smiles' and 'logP'.
    Exits with SystemExit(1) if columns are missing.
    """
    required_columns = ['smiles', 'logP']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        logger.error("Data Gap: Missing required columns. No synthetic fallback.")
        sys.exit(1)
    
    # Check for non-empty data
    if df.empty:
        logger.error("Schema validation failed. Dataset is empty.")
        sys.exit(1)

    logger.info("Schema validation passed.")
    return True

def perform_power_analysis(df: pd.DataFrame) -> None:
    """
    Perform a priori power analysis check.
    Requires N >= 128 samples.
    """
    n = len(df)
    if n < MIN_SAMPLES:
        logger.error(f"Power analysis failed. N={n} is less than required {MIN_SAMPLES}.")
        logger.error("Data Gap: Insufficient samples for statistical power. No synthetic fallback.")
        sys.exit(1)
    
    logger.info(f"Power analysis passed. N={n} >= {MIN_SAMPLES}.")

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold from a SMILES string.
    Returns the scaffold as a canonical SMILES string or None if invalid.
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

def enforce_scaffold_check(df: pd.DataFrame) -> None:
    """
    Enforce the minimum number of unique scaffolds (>= 100).
    Exits with SystemExit(1) if the check fails.
    """
    logger.info("Computing Bemis-Murcko scaffolds...")
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold)
    unique_scaffolds = scaffolds.dropna().unique()
    num_unique = len(unique_scaffolds)
    
    logger.info(f"Found {num_unique} unique scaffolds.")
    
    if num_unique < MIN_SCAFFOLDS:
        logger.error(f"Scaffold check failed. Unique scaffolds={num_unique} < {MIN_SCAFFOLDS}.")
        logger.error("Data Gap: Insufficient scaffold diversity for robust splitting. No synthetic fallback.")
        sys.exit(1)
    
    logger.info(f"Scaffold check passed. {num_unique} >= {MIN_SCAFFOLDS}.")
    return unique_scaffolds

def scaffold_split(df: pd.DataFrame, n_folds: int = 5, seed: int = SEED) -> Dict[str, List[int]]:
    """
    Perform a scaffold split using Bemis-Murcko scaffolds.
    Returns a dictionary mapping fold names to lists of indices.
    Uses StratifiedKFold logic on scaffold groups to ensure balanced splits.
    """
    from sklearn.model_selection import StratifiedKFold
    
    pin_random_seed(seed)
    
    # Get scaffolds
    df['scaffold'] = df['smiles'].apply(get_bemis_murcko_scaffold)
    df = df.dropna(subset=['scaffold']) # Remove molecules without valid scaffolds
    
    scaffold_groups = df['scaffold'].values
    indices = df.index.values
    
    # Use StratifiedKFold on the scaffold labels
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    
    splits = {f"fold_{i}": [] for i in range(n_folds)}
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(indices, scaffold_groups)):
        # Assign test indices to the current fold
        # In a multi-fold split, we usually want to save the test set for each fold
        # The standard format for splits.json is often:
        # { "train": [...], "test": [...] } for a single split, OR
        # { "fold_0": { "train": [...], "test": [...] }, ... } for k-fold
        # Given the task asks to "save split indices" and "multiple folds", we structure as k-fold metadata.
        
        # We will store the test indices for each fold, and the union of all other folds as train?
        # Actually, standard practice for "save splits" in this context is often to save the specific test set for each fold
        # and let the training logic handle the rest, OR save the train/test pairs.
        # Let's save the train and test indices for each fold to be explicit.
        
        train_indices = indices[train_idx].tolist()
        test_indices = indices[test_idx].tolist()
        
        splits[f"fold_{fold_idx}"] = {
            "train": train_indices,
            "test": test_indices
        }
    
    # Validate scaffold distribution per fold
    for fold_name, fold_data in splits.items():
        if isinstance(fold_data, dict):
            test_indices = fold_data["test"]
            test_scaffolds = set(df.loc[test_indices, 'scaffold'].unique())
            logger.info(f"Fold {fold_name}: {len(test_indices)} samples, {len(test_scaffolds)} unique scaffolds in test set.")
            if len(test_scaffolds) < 5: # Arbitrary low threshold for robustness check
                logger.warning(f"Fold {fold_name} has very few unique scaffolds in test set.")
    
    return splits

def main():
    """Main execution flow for T008b (Part 2)."""
    logger.info("Starting Data Ingestion (Part 2): Scaffold Split and Validation")
    
    # 1. Fetch Data
    df = fetch_esol_dataset()
    
    # 2. Validate Schema
    validate_schema(df)
    
    # 3. Power Analysis
    perform_power_analysis(df)
    
    # 4. Enforce Scaffold Check
    unique_scaffolds = enforce_scaffold_check(df)
    
    # 5. Perform Scaffold Split
    splits = scaffold_split(df, n_folds=5, seed=SEED)
    
    # 6. Save Splits
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    splits_path = PROCESSED_DIR / "splits.json"
    
    with open(splits_path, 'w') as f:
        json.dump(splits, f, indent=2)
    
    logger.info(f"Split indices saved to {splits_path}")
    
    # 7. Verify Output
    if not splits_path.exists():
        logger.error("Failed to write splits.json")
        sys.exit(1)
        
    logger.info("Data Ingestion (Part 2) completed successfully.")

if __name__ == "__main__":
    main()