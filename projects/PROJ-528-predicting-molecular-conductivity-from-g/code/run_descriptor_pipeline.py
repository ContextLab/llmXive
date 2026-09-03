import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np

from descriptors import (
    compute_degree_statistics,
    compute_path_length_statistics,
    compute_ring_count,
    compute_aromatic_ring_count,
    compute_conjugation_length,
    compute_standard_descriptors
)
from logging_config import setup_logging
from config import DATA_PATH

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """
    Load SMILES from a CSV file.
    Expects a CSV with at least a 'smiles' column.
    Returns a DataFrame with 'smiles' and 'status' columns.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        # Try to infer if the first column is SMILES
        if len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'smiles'})
        else:
            raise ValueError("Input CSV must contain a 'smiles' column")
    
    if 'status' not in df.columns:
        df['status'] = 'valid'
    
    return df[['smiles', 'status']]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with invalid status or missing SMILES.
    """
    initial_count = len(df)
    df = df[df['status'].str.lower() == 'valid']
    df = df[df['smiles'].notna()]
    df = df[df['smiles'].str.strip() != '']
    
    dropped = initial_count - len(df)
    if dropped > 0:
        logging.info(f"Dropped {dropped} rows due to invalid status or missing SMILES.")
    
    return df.reset_index(drop=True)

def compute_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all required descriptors for the dataframe.
    Returns a DataFrame with the exact columns required by T019.
    """
    required_columns = [
        'smiles', 'status',
        'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'conjugation_length', 'ring_count'
    ]
    
    results = []
    invalid_count = 0
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        try:
            # Compute descriptors
            degree_stats = compute_degree_statistics(smiles)
            path_stats = compute_path_length_statistics(smiles)
            ring_cnt = compute_ring_count(smiles)
            arom_cnt = compute_aromatic_ring_count(smiles)
            conj_len = compute_conjugation_length(smiles)
            
            # Check for NaN in any required descriptor
            if any(np.isnan([
                degree_stats['mean'], degree_stats['std'], degree_stats['max'], degree_stats['min'],
                path_stats['mean'], path_stats['std'], path_stats['max'], path_stats['min'],
                arom_cnt, conj_len, ring_cnt
            ])):
                invalid_count += 1
                continue
            
            results.append({
                'smiles': smiles,
                'status': row.get('status', 'valid'),
                'degree_mean': degree_stats['mean'],
                'degree_std': degree_stats['std'],
                'degree_max': degree_stats['max'],
                'degree_min': degree_stats['min'],
                'path_length_mean': path_stats['mean'],
                'path_length_std': path_stats['std'],
                'path_length_max': path_stats['max'],
                'path_length_min': path_stats['min'],
                'aromaticity_index': arom_cnt,
                'conjugation_length': conj_len,
                'ring_count': ring_cnt
            })
        except Exception as e:
            logging.warning(f"Failed to compute descriptors for {smiles}: {e}")
            invalid_count += 1
            continue
    
    if invalid_count > 0:
        logging.info(f"Dropped {invalid_count} rows due to NaN values in descriptors.")
    
    if not results:
        logging.error("No valid descriptors computed. Check input data.")
        return pd.DataFrame(columns=required_columns)
    
    output_df = pd.DataFrame(results)
    
    # Ensure column order
    output_df = output_df[required_columns]
    
    return output_df

def main():
    parser = argparse.ArgumentParser(description="Run descriptor computation pipeline.")
    parser.add_argument("--input", type=str, default=os.path.join(DATA_PATH, "raw", "combined_smiles.csv"),
                        help="Path to input SMILES CSV file.")
    parser.add_argument("--output", type=str, default=os.path.join(DATA_PATH, "processed", "descriptors.csv"),
                        help="Path to output descriptors CSV file.")
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Loading SMILES from {args.input}")
    try:
        df = load_smiles_from_file(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Cleaning dataframe...")
    df = clean_dataframe(df)

    logger.info(f"Computing descriptors for {len(df)} molecules...")
    result_df = compute_all_descriptors(df)

    if result_df.empty:
        logger.error("No descriptors computed. Exiting.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    logger.info(f"Saving results to {args.output}")
    result_df.to_csv(args.output, index=False)
    logger.info(f"Successfully wrote {len(result_df)} rows to {args.output}")

if __name__ == "__main__":
    main()