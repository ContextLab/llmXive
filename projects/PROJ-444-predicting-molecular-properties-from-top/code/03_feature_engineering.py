"""
Feature Engineering Pipeline (T004)

Computes RDKit-based traditional descriptors (MW, atom counts, Morgan fingerprints)
and merges them with TDA persistence images to create the final combined feature matrix.

Requirements:
- Traditional descriptors: MW, atom counts (C, N, O, S, P, Halogens), 1024-bit Morgan Fingerprint.
- Merge on 'molecule_id'.
- Output: data/processed/traditional_descriptors.csv and data/processed/combined_features.csv.
- Ensure no missing values.
- Row counts of TDA, Traditional, and Combined matrices must match.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem

# Project-relative paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

def setup_logging():
    """Configure logging for the feature engineering pipeline."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("feature_engineering")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler
        fh = logging.FileHandler(LOGS_DIR / "feature_engineering.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger

def compute_traditional_descriptors(df_filtered: pd.DataFrame, valid_ids: List[str], logger: logging.Logger) -> pd.DataFrame:
    """
    Compute traditional molecular descriptors for a specific set of molecule IDs.
    
    Includes:
    - Molecular Weight
    - Atom counts (C, N, O, S, P, Halogens)
    - 1024-bit Morgan Fingerprint (radius 2)
    """
    logger.info(f"Computing traditional descriptors for {len(valid_ids)} molecules...")
    
    # Filter to only valid IDs to ensure row count match with TDA features
    df = df_filtered[df_filtered['molecule_id'].isin(valid_ids)].copy()
    
    records = []
    for idx, row in df.iterrows():
        mol_id = row['molecule_id']
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES for {mol_id}: {smiles}")
            continue
            
        # 1. Molecular Weight
        mw = Descriptors.MolWt(mol)
        
        # 2. Atom Counts
        # We count specific common elements
        counts = {}
        for symbol in ['C', 'N', 'O', 'S', 'P']:
            counts[f"atom_count_{symbol}"] = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() == symbol)
        
        # Halogens (F, Cl, Br, I)
        counts["atom_count_Hal"] = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() in ['F', 'Cl', 'Br', 'I'])
        
        # 3. Morgan Fingerprint (1024-bit)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=1024)
        fp_list = list(fp)
        fp_dict = {f"morgan_{i}": val for i, val in enumerate(fp_list)}
        
        # Combine all
        record = {"molecule_id": mol_id, "MW": mw}
        record.update(counts)
        record.update(fp_dict)
        records.append(record)
        
    return pd.DataFrame(records)

def load_tda_features(logger: logging.Logger) -> pd.DataFrame:
    """Load TDA feature vectors from data/processed/persistence_images_10x10.csv."""
    file_path = PROCESSED_DIR / "persistence_images_10x10.csv"
    if not file_path.exists():
        logger.error(f"TDA features missing at {file_path}. Run 02_tda_computation.py first.")
        raise SystemExit(1)
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded TDA features: {len(df)} molecules.")
    return df

def merge_features(traditional_df: pd.DataFrame, tda_df: pd.DataFrame, target_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Merge traditional descriptors, TDA features, and target values on 'molecule_id'.
    """
    logger.info("Merging feature sets...")
    
    # Merge Traditional and TDA
    merged = pd.merge(traditional_df, tda_df, on='molecule_id', how='inner')
    
    # Merge with targets (filtered_esol) to get logP
    merged = pd.merge(merged, target_df[['molecule_id', 'logP']], on='molecule_id', how='inner')
    
    # Reorder: molecule_id, logP, then features
    cols = ['molecule_id', 'logP'] + [c for c in merged.columns if c not in ['molecule_id', 'logP']]
    merged = merged[cols]
    
    logger.info(f"Final merged matrix shape: {merged.shape}")
    return merged

def run_feature_engineering():
    """Orchestration for T004."""
    logger = setup_logging()
    logger.info("Starting Feature Engineering (T004)...")
    
    # 1. Load inputs
    filtered_path = PROCESSED_DIR / "filtered_esol.csv"
    if not filtered_path.exists():
        logger.error(f"Filtered dataset missing at {filtered_path}. Run 01_data_ingestion.py first.")
        sys.exit(1)
    
    df_filtered = pd.read_csv(filtered_path)
    if 'molecule_id' not in df_filtered.columns:
        df_filtered['molecule_id'] = df_filtered.index.astype(str)
    
    # Load TDA features to determine the set of successfully processed molecules
    df_tda = load_tda_features(logger)
    valid_ids = df_tda['molecule_id'].tolist()
    
    # 2. Compute Traditional Descriptors for those valid IDs
    df_trad = compute_traditional_descriptors(df_filtered, valid_ids, logger)
    
    # Save traditional descriptors
    trad_output_path = PROCESSED_DIR / "traditional_descriptors.csv"
    df_trad.to_csv(trad_output_path, index=False)
    logger.info(f"Saved traditional descriptors to {trad_output_path} ({len(df_trad)} rows).")
    
    # 3. Merge into Combined Matrix
    df_combined = merge_features(df_trad, df_tda, df_filtered, logger)
    
    # 4. Validation: Check for NaNs and Row Counts
    nan_count = df_combined.isnull().sum().sum()
    if nan_count > 0:
        logger.error(f"Combined matrix contains {nan_count} NaNs!")
        sys.exit(1)
    
    # Verify row counts match
    if not (len(df_trad) == len(df_tda) == len(df_combined)):
        logger.error(f"Row count mismatch: Trad({len(df_trad)}), TDA({len(df_tda)}), Combined({len(df_combined)})")
        sys.exit(1)
    
    logger.info("Verification passed: Row counts match and no missing values.")
    
    # 5. Save Combined Features
    combined_output_path = PROCESSED_DIR / "combined_features.csv"
    df_combined.to_csv(combined_output_path, index=False)
    logger.info(f"Saved combined feature matrix to {combined_output_path}")
    
    logger.info("Feature Engineering (T004) completed successfully.")

def main():
    try:
        run_feature_engineering()
    except Exception as e:
        logging.getLogger("feature_engineering").exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()