import sys
import os
import argparse
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from code.logging_config import setup_logging
from code.data_loader import load_smiles
from code.descriptors import compute_standard_descriptors

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """
    Load SMILES from a CSV file.
    Expects a column named 'smiles'.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        # Try to find a column that looks like SMILES
        col = df.columns[0]
        logging.warning(f"Column 'smiles' not found. Using '{col}' as SMILES column.")
        df = df.rename(columns={col: 'smiles'})
    return df

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with invalid SMILES or missing data.
    """
    # Basic cleaning: drop rows where 'smiles' is null or empty
    df = df.dropna(subset=['smiles'])
    df = df[df['smiles'].str.strip() != '']
    return df

def compute_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptors for each molecule in the DataFrame.
    """
    results = []
    for idx, row in df.iterrows():
        smiles = row['smiles']
        try:
            desc = compute_standard_descriptors(smiles)
            desc['smiles'] = smiles
            desc['status'] = 'valid'
            results.append(desc)
        except Exception as e:
            logging.warning(f"Failed to compute descriptors for {smiles}: {e}")
            results.append({
                'smiles': smiles,
                'status': 'error',
                'error_msg': str(e)
            })
    
    result_df = pd.DataFrame(results)
    return result_df

def main():
    parser = argparse.ArgumentParser(description="Run descriptor computation pipeline.")
    parser.add_argument("--input", type=str, required=True, help="Path to input SMILES CSV.")
    parser.add_argument("--output", type=str, required=True, help="Path to output descriptors CSV.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Loading SMILES from {args.input}")
    df = load_smiles_from_file(args.input)
    df = clean_dataframe(df)
    
    logger.info(f"Computing descriptors for {len(df)} molecules.")
    result_df = compute_all_descriptors(df)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    result_df.to_csv(args.output, index=False)
    logger.info(f"Descriptors saved to {args.output}")

if __name__ == "__main__":
    main()
