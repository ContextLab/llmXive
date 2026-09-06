"""
Script to finalize and save descriptor computation results to data/processed/descriptors.csv.

This task (T019) ensures that all computed descriptors are validated for NaN values
and saved to the correct output path with the exact required columns.

Dependencies:
- code/descriptors.py (for compute_descriptors_batch)
- code/data_loader.py (for load_processed_data or similar)
- code/logging_config.py (for setup_logging)

Usage:
python code/save_descriptors.py --input data/processed/descriptors_raw.csv --output data/processed/descriptors.csv
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np

# Add project root to path if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.logging_config import setup_logging
from code.descriptors import compute_descriptors_batch
from code.data_loader import load_processed_data

REQUIRED_COLUMNS = [
    'smiles', 'status', 'degree_mean', 'degree_std', 'degree_max', 'degree_min',
    'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
    'aromaticity_index', 'huckel_aromaticity_count', 'clar_aromaticity_proxy',
    'conjugation_length', 'num_conjugated_bonds', 'conjugation_density',
    'ring_count', 'weighted_path_length', 'electronegativity_polarity',
    'resonance_proxy'
]

def validate_and_save_descriptors(input_path: str, output_path: str):
    """
    Loads descriptor data, validates for NaN values in required columns,
    drops invalid rows, logs the count, and saves to output_path.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Loading descriptor data from {input_path}")
    
    # Attempt to load the data. 
    # If input_path is a raw SMILES file, we might need to run the batch computation.
    # However, T014 (compute_descriptors_batch) likely produced a dataframe.
    # We assume the input is a CSV with SMILES and potentially some computed columns,
    # or just SMILES if we need to recompute.
    # Given T014 is "Compute descriptors", it likely returns a DF.
    # Let's try to load as CSV first.
    
    if not os.path.exists(input_path):
        # Fallback: maybe we need to load raw SMILES and compute?
        # But T019 depends on T014. T014 should have produced data.
        # If the file doesn't exist, we might need to run the pipeline up to T014.
        # For this task, we assume the input file exists or we load raw SMILES.
        # Let's check if it's a raw SMILES file or a partial descriptor file.
        # If it's raw SMILES, we compute.
        logger.warning(f"Input file {input_path} not found. Attempting to load raw SMILES from {input_path.replace('descriptors_raw.csv', 'raw_smiles.csv')} or similar.")
        # This is a fallback strategy. Ideally, the input is the result of T014.
        # Let's assume the user provides the raw SMILES if descriptors aren't there yet.
        # But the task says "Write descriptor computation results".
        # We will assume the input is a CSV with SMILES and we need to compute descriptors if they are missing.
        
        # Let's try to load the raw SMILES file if the descriptor file doesn't exist.
        raw_smiles_path = input_path.replace("descriptors.csv", "raw_smiles.csv")
        if os.path.exists(raw_smiles_path):
            df = pd.read_csv(raw_smiles_path)
            if 'smiles' not in df.columns:
                raise ValueError(f"Raw SMILES file {raw_smiles_path} must contain 'smiles' column.")
            logger.info(f"Loaded raw SMILES from {raw_smiles_path}. Computing descriptors.")
            # Compute descriptors
            df = compute_descriptors_batch(df['smiles'].tolist())
        else:
            raise FileNotFoundError(f"Neither {input_path} nor raw SMILES file found.")
    else:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded descriptor data from {input_path}")

    # Ensure all required columns exist. If not, compute them.
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in input: {missing_cols}. Recomputing descriptors.")
        if 'smiles' not in df.columns:
            raise ValueError("Input file must have 'smiles' column to recompute descriptors.")
        # Recompute all descriptors
        df = compute_descriptors_batch(df['smiles'].tolist())
    
    # Filter to only required columns
    df = df[REQUIRED_COLUMNS]

    # Check for NaN values in required descriptor columns (excluding 'smiles' and 'status')
    descriptor_cols = [col for col in REQUIRED_COLUMNS if col not in ['smiles', 'status']]
    nan_mask = df[descriptor_cols].isna().any(axis=1)
    nan_count = nan_mask.sum()

    if nan_count > 0:
        logger.warning(f"Dropped {nan_count} rows due to NaN values in descriptors.")
        df = df[~nan_mask]

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} valid rows to {output_path}")

    return len(df)

def main():
    parser = argparse.ArgumentParser(description="Save validated descriptor results to CSV.")
    parser.add_argument("--input", type=str, default="data/processed/descriptors_raw.csv",
                        help="Path to input descriptor data or raw SMILES file.")
    parser.add_argument("--output", type=str, default="data/processed/descriptors.csv",
                        help="Path to save the final descriptors CSV.")
    args = parser.parse_args()

    count = validate_and_save_descriptors(args.input, args.output)
    print(f"Successfully saved {count} rows to {args.output}")

if __name__ == "__main__":
    main()