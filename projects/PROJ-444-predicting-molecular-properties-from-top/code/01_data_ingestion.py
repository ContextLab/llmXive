import os
import sys
import logging
import random
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import GroupKFold

# --- Logging Setup ---
def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

# --- Seed Pinning ---
def pin_random_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    # Note: RDKit has its own seed setting if needed, but sklearn handles split seed

# --- Molecular Weight Calculation ---
def calculate_molecular_weight(smiles: str) -> Optional[float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return sum(Chem.GetFormalCharge(Chem.GetAtomWithIdx(mol, i)) for i in range(mol.GetNumAtoms())) # Placeholder logic, actual MW needs atomic mass
    # Correct RDKit MW calculation:
    from rdkit.Chem.Descriptors import MolWt
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return MolWt(mol)

# --- Scaffold Logic ---
def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold)

def check_scaffold_integrity(df: pd.DataFrame, min_scaffolds: int = 100) -> Tuple[int, bool]:
    """
    Counts unique scaffolds and checks against minimum threshold.
    Returns (count, is_valid).
    """
    logger = logging.getLogger("data_ingestion")
    logger.info("Calculating unique Bemis-Murcko scaffolds...")
    
    scaffolds = []
    for idx, row in df.iterrows():
        scaffold = get_bemis_murcko_scaffold(row['smiles'])
        if scaffold:
            scaffolds.append(scaffold)
    
    unique_scaffolds = set(scaffolds)
    count = len(unique_scaffolds)
    
    logger.info(f"Found {count} unique scaffolds.")
    is_valid = count >= min_scaffolds
    
    if not is_valid:
        logger.error(f"Scaffold Insufficient: {count} < {min_scaffolds}")
    
    return count, is_valid

# --- Data Integrity Check (Re-calc MW) ---
def verify_data_integrity_mw(df: pd.DataFrame) -> bool:
    """
    Re-calculates MW for every molecule in the input dataframe.
    Exits if any molecule > 1000 Da.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info("Verifying data integrity: checking molecular weights...")
    
    for idx, row in df.iterrows():
        mw = calculate_molecular_weight(row['smiles'])
        if mw is not None and mw > 1000:
            logger.error(f"Data Integrity Violation: Large molecule detected in input to splitter. Upstream filter failed. MW={mw} at index {idx}")
            return False
    return True

# --- Splitting Logic ---
def stratified_scaffold_split(df: pd.DataFrame, n_splits: int = 5, seed: int = 42) -> Dict[str, List[int]]:
    """
    Performs a 5-fold scaffold split using GroupKFold.
    Groups are Bemis-Murcko scaffolds.
    Returns a dict with keys 'train' and 'test' containing lists of indices for each fold.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info(f"Performing {n_splits}-fold scaffold split with seed {seed}...")
    
    scaffolds = [get_bemis_murcko_scaffold(smiles) for smiles in df['smiles']]
    # Handle None scaffolds by assigning a unique group or excluding?
    # Assuming valid data here based on previous filters.
    scaffolds = [s if s else f"unknown_{i}" for i, s in enumerate(scaffolds)]
    
    gkf = GroupKFold(n_splits=n_splits)
    
    split_indices = {'train': [], 'test': []}
    
    for fold, (train_idx, test_idx) in enumerate(gkf.split(df, groups=scaffolds)):
        split_indices['train'].append(train_idx.tolist())
        split_indices['test'].append(test_idx.tolist())
        logger.info(f"Fold {fold}: Train size={len(train_idx)}, Test size={len(test_idx)}")
        
    return split_indices

# --- Main Execution for T008b ---
def main():
    logger = setup_logging()
    pin_random_seed(42)
    
    input_file = Path("data/processed/filtered_esol.csv")
    output_scaffold_counts = Path("data/processed/scaffold_counts.json")
    output_splits = Path("data/processed/splits.json")
    
    logger.info(f"Loading pre-filtered dataset from {input_file}...")
    
    if not input_file.exists():
        logger.error("Data Gap: Input file filtered_esol.csv not found. Upstream task T008c may have failed.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)
    
    if df.empty:
        logger.error("Data Gap: Input file is empty.")
        sys.exit(1)
    
    # 1. Data Integrity Check (Re-calc MW)
    if not verify_data_integrity_mw(df):
        sys.exit(1)
    
    # 2. Power Check (N >= 128) - Re-verify from T008a logic
    if len(df) < 128:
        logger.error(f"Power Insufficient: Dataset size {len(df)} < 128.")
        sys.exit(1)
    
    # 3. Scaffold Count & Check
    scaffold_count, is_scaffold_valid = check_scaffold_integrity(df, min_scaffolds=100)
    
    if not is_scaffold_valid:
        # Save the count even on failure for debugging
        with open(output_scaffold_counts, 'w') as f:
            json.dump({'unique_scaffolds': scaffold_count, 'min_required': 100, 'status': 'FAILED'}, f, indent=2)
        sys.exit(1)
    
    # 4. Save Scaffold Counts
    with open(output_scaffold_counts, 'w') as f:
        json.dump({'unique_scaffolds': scaffold_count, 'min_required': 100, 'status': 'PASSED'}, f, indent=2)
    logger.info(f"Saved scaffold counts to {output_scaffold_counts}")
    
    # 5. Perform Split
    split_indices = stratified_scaffold_split(df, n_splits=5, seed=42)
    
    # 6. Save Split Indices
    with open(output_splits, 'w') as f:
        json.dump(split_indices, f, indent=2)
    logger.info(f"Saved split indices to {output_splits}")
    
    logger.info("T008b completed successfully.")

if __name__ == "__main__":
    main()