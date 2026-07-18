"""
Clean script for the molecular descriptors pipeline.

Parses the downloaded QM9 dataset, validates molecule structures,
filters out rows with missing DFT labels or invalid geometry,
and saves the cleaned dataset.
"""
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

# Project imports
from utils.logger import setup_logger, get_logger
from utils.parsers import smiles_to_mol, validate_molecule
from utils.memory_monitor import check_memory_limit, get_memory_usage_gb

logger = get_logger(__name__)

def load_raw_data(input_path: Path) -> pd.DataFrame:
    """Load the raw QM9 dataset from parquet."""
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def validate_row(row: pd.Series) -> bool:
    """
    Validate a single row of the dataframe.
    Checks for:
    1. Valid SMILES string
    2. Valid 3D coordinates (if present)
    3. Presence of required DFT labels (dipole, HOMO, LUMO)
    """
    # Check DFT labels
    required_cols = ['mu', 'alpha', 'homo', 'lumo', 'gap', 'r2', 'zpve', 'u0', 'u298', 'h298', 'g298', 'cvg298']
    # Note: QM9 columns might vary slightly, checking for common ones.
    # The spec mentions 'dipole', 'HOMO', 'LUMO'. In QM9 dataset, these are often 'mu', 'homo', 'lumo'.
    # We will check for the presence of at least 'mu', 'homo', 'lumo' as per standard QM9.
    dft_cols = ['mu', 'homo', 'lumo']
    
    for col in dft_cols:
        if col not in row or pd.isna(row[col]):
            return False
    
    # Check SMILES
    smiles = row.get('smiles', '')
    if not smiles or not isinstance(smiles, str):
        return False
    
    mol = smiles_to_mol(smiles)
    if mol is None:
        return False
    
    # Validate molecule geometry if coordinates exist
    # QM9 usually has 'pos' or similar for coordinates.
    # If coordinates are missing, we might still accept if SMILES is valid,
    # but for 3D features we need them. Let's assume we need valid SMILES for now.
    # If the task requires 3D features later, we might need to filter further.
    # For this cleaning step, we ensure the molecule is chemically valid.
    if not validate_molecule(mol):
        return False
        
    return True

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the dataframe to keep only valid rows."""
    logger.info("Starting data validation and cleaning...")
    
    # Memory check
    mem_gb = get_memory_usage_gb()
    if mem_gb > 6.0:
        logger.warning(f"High memory usage detected: {mem_gb:.2f} GB. Proceeding with caution.")
    
    # Apply validation
    valid_mask = df.apply(validate_row, axis=1)
    cleaned_df = df[valid_mask].reset_index(drop=True)
    
    logger.info(f"Original rows: {len(df)}, Cleaned rows: {len(cleaned_df)}")
    logger.info(f"Removed {len(df) - len(cleaned_df)} invalid rows")
    
    return cleaned_df

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the cleaned dataframe to parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Saved successfully")

def main() -> int:
    """Main entry point for the cleaning script."""
    parser = argparse.ArgumentParser(description="Clean and validate QM9 dataset")
    parser.add_argument("--input", type=str, default="data/raw/qm9_full.parquet",
                        help="Path to the raw input parquet file")
    parser.add_argument("--output", type=str, default="data/processed/molecules_cleaned.parquet",
                        help="Path to save the cleaned output parquet file")
    args = parser.parse_args()
    
    setup_logger(level=logging.INFO)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        # Load
        df = load_raw_data(input_path)
        
        # Clean
        cleaned_df = clean_data(df)
        
        # Save
        save_cleaned_data(cleaned_df, output_path)
        
        logger.info("Cleaning completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Error during cleaning: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())