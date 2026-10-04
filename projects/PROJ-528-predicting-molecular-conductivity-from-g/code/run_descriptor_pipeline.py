import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from code.logging_config import setup_logging
from code.config import DATA_PATH
from code.descriptors import compute_all_descriptors

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """
    Loads SMILES from a CSV file.
    Expects a column named 'smiles'.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        raise ValueError("CSV must contain a 'smiles' column.")
    
    logging.info(f"Loaded {len(df)} SMILES from {path}")
    return df

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows with missing or invalid SMILES.
    """
    # Drop rows with missing SMILES
    initial_count = len(df)
    df = df.dropna(subset=['smiles'])
    dropped = initial_count - len(df)
    if dropped > 0:
        logging.warning(f"Dropped {dropped} rows with missing SMILES.")
    
    # Basic validation: check if SMILES is a string
    df = df[df['smiles'].apply(lambda x: isinstance(x, str) and len(x) > 0)]
    return df

def compute_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all descriptors for the given DataFrame.
    Returns a DataFrame with descriptors added.
    """
    logging.info("Computing descriptors...")
    # Assuming compute_all_descriptors handles the SMILES column and returns a DF with descriptors
    # The function signature in descriptors.py is expected to match this usage
    result_df = compute_all_descriptors(df)
    logging.info(f"Computed descriptors for {len(result_df)} molecules.")
    return result_df

def main():
    """
    CLI entry point for the descriptor pipeline.
    Loads data, computes descriptors, and saves to data/processed/descriptors_base.csv and descriptors.csv.
    """
    parser = argparse.ArgumentParser(description="Run the descriptor computation pipeline.")
    parser.add_argument("--input", type=str, default=None, help="Path to input SMILES CSV.")
    parser.add_argument("--output-base", type=str, default=None, help="Path to output base descriptors CSV.")
    parser.add_argument("--output-full", type=str, default=None, help="Path to output full descriptors CSV.")
    args = parser.parse_args()

    setup_logging()
    
    # Default paths
    if args.input is None:
        args.input = os.path.join(DATA_PATH, "raw", "smiles.csv")
    
    if args.output_base is None:
        args.output_base = os.path.join(DATA_PATH, "processed", "descriptors_base.csv")
    
    if args.output_full is None:
        args.output_full = os.path.join(DATA_PATH, "processed", "descriptors.csv")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.output_base), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_full), exist_ok=True)
    
    # 1. Load Data
    df = load_smiles_from_file(args.input)
    
    # 2. Clean Data
    df = clean_dataframe(df)
    
    if len(df) == 0:
        logging.error("No valid SMILES found after cleaning.")
        return
    
    # 3. Compute Descriptors
    df_descriptors = compute_all_descriptors(df)
    
    # 4. Save Base Descriptors
    df_descriptors.to_csv(args.output_base, index=False)
    logging.info(f"Saved base descriptors to {args.output_base}")
    
    # 5. Save Full Descriptors (same as base for now, schema compliant)
    df_descriptors.to_csv(args.output_full, index=False)
    logging.info(f"Saved full descriptors to {args.output_full}")

if __name__ == "__main__":
    main()
