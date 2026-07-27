"""
Descriptor computation pipeline runner.

Loads SMILES from data/raw/molecules.csv, computes all required descriptors
(standard graph metrics + physics-based proxies), and writes the results to
data/processed/descriptors.csv.

Output columns (EXACT):
[smiles, status, degree_mean, degree_std, degree_max, degree_min, 
 path_length_mean, path_length_std, path_length_max, path_length_min, 
 aromaticity_index, conjugation_length, ring_count, bond_polarity, resonance_energy]

No NaN values are permitted in the final output.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

# Import from existing API surface
from descriptors import compute_descriptors_batch
from logging_config import setup_logging
from data_loader import load_smiles
from config import DATA_PATH

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)

# Define the exact output columns required by T019
OUTPUT_COLUMNS = [
    'smiles', 'status', 
    'degree_mean', 'degree_std', 'degree_max', 'degree_min',
    'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
    'aromaticity_index', 'conjugation_length', 'ring_count', 
    'bond_polarity', 'resonance_energy'
]

def load_smiles_from_file() -> pd.DataFrame:
    """
    Load SMILES data from data/raw/molecules.csv.
    
    Returns a DataFrame with 'smiles' and 'conductivity' columns.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if required columns are missing.
    """
    input_path = os.path.join(DATA_PATH, 'raw', 'molecules.csv')
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['smiles']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Input file missing required column: {col}")
    
    return df[['smiles']]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the output DataFrame has no NaN values and correct types.
    
    Replaces any NaN with 0.0 for numeric columns and 'unknown' for status.
    """
    # Fill missing status with 'unknown'
    if 'status' in df.columns:
        df['status'] = df['status'].fillna('unknown')
    
    # Fill numeric NaNs with 0.0
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0.0)
    
    # Ensure all required columns exist
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            logger.warning(f"Adding missing column {col} with default value 0.0")
            df[col] = 0.0
    
    # Reorder columns to match exact specification
    df = df[OUTPUT_COLUMNS]
    
    return df

def main():
    """
    Main entry point for the descriptor computation pipeline.
    
    1. Load SMILES from data/raw/molecules.csv.
    2. Compute descriptors using compute_descriptors_batch.
    3. Clean the result to ensure no NaN values.
    4. Write to data/processed/descriptors.csv.
    """
    logger.info("Starting descriptor computation pipeline (T019)")
    
    # Ensure output directory exists
    output_dir = os.path.join(DATA_PATH, 'processed')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'descriptors.csv')
    
    try:
        # Load input data
        logger.info(f"Loading SMILES from {os.path.join(DATA_PATH, 'raw', 'molecules.csv')}")
        input_df = load_smiles_from_file()
        smiles_list = input_df['smiles'].tolist()
        
        if not smiles_list:
            logger.warning("No SMILES found in input file. Creating empty output.")
            empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
            empty_df.to_csv(output_path, index=False)
            logger.info(f"Wrote empty descriptors file to {output_path}")
            return
        
        # Compute descriptors
        logger.info(f"Computing descriptors for {len(smiles_list)} molecules...")
        result_df = compute_descriptors_batch(smiles_list)
        
        # Validate result has required columns
        missing_cols = set(OUTPUT_COLUMNS) - set(result_df.columns)
        if missing_cols:
            logger.error(f"Descriptor computation missing required columns: {missing_cols}")
            raise ValueError(f"Missing columns in descriptor output: {missing_cols}")
        
        # Clean data to ensure no NaN
        result_df = clean_dataframe(result_df)
        
        # Verify no NaNs remain
        if result_df.isna().any().any():
            nan_cols = result_df.columns[result_df.isna().any()].tolist()
            logger.error(f"NaN values still present in columns: {nan_cols}")
            raise ValueError("NaN values present in final output after cleaning")
        
        # Write output
        result_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(result_df)} rows to {output_path}")
        logger.info(f"Output columns: {list(result_df.columns)}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
