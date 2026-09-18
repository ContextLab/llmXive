"""
Descriptor Pipeline Runner (T019)

Computes all descriptors (T014a-d) and writes results to data/processed/descriptors.csv.
Loads raw SMILES directly from config.RAW_DATA_PATH.
"""
import sys
import os
import argparse
import logging
import pandas as pd
import numpy as np
from typing import Optional

# Import from local modules (matching API surface)
from code.config import RAW_DATA_PATH, DATA_PATH, SEED
from code.logging_config import setup_logging
from code.data_loader import load_smiles
from code.descriptors import compute_all_descriptors
from code.validators import validate_smiles

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """
    Load raw SMILES data directly from the configured path.
    Returns DataFrame with columns: ['smiles', 'valid', 'error_msg']
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found at: {path}")
    
    # Attempt to load as CSV
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV from {path}: {e}")
    
    # Ensure 'smiles' column exists
    if 'smiles' not in df.columns:
        # Try common aliases
        for alias in ['SMILES', 'smile', 'molecule']:
            if alias in df.columns:
                df = df.rename(columns={alias: 'smiles'})
                break
        else:
            raise ValueError(f"Column 'smiles' not found in {path}. Available columns: {list(df.columns)}")
    
    # Validate SMILES strings
    valid_mask = []
    error_msgs = []
    
    for smiles in df['smiles']:
        is_valid, error = validate_smiles(str(smiles))
        valid_mask.append(is_valid)
        error_msgs.append(error if not is_valid else "")
    
    df['valid'] = valid_mask
    df['error_msg'] = error_msgs
    
    return df

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove invalid rows and drop NaNs in required descriptor columns.
    """
    # Filter valid SMILES
    df_valid = df[df['valid']].copy()
    
    if len(df_valid) == 0:
        logging.warning("No valid SMILES found in input data.")
        return pd.DataFrame()
    
    # Drop error_msg column if present
    if 'error_msg' in df_valid.columns:
        df_valid = df_valid.drop(columns=['error_msg'])
    
    return df_valid

def compute_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all descriptors for valid molecules.
    Returns DataFrame with original columns + all descriptor columns.
    """
    if df.empty:
        return df
    
    # Extract SMILES column
    smiles_list = df['smiles'].tolist()
    
    # Compute descriptors in batches
    descriptor_results = compute_all_descriptors(smiles_list)
    
    # Create DataFrame from results
    desc_df = pd.DataFrame(descriptor_results)
    
    # Merge with original DataFrame (keep index alignment)
    # Ensure index matches
    desc_df.index = df.index
    
    # Concatenate
    final_df = pd.concat([df.drop(columns=['smiles']), desc_df], axis=1)
    
    # Log NaN handling
    nan_count = final_df.isna().sum().sum()
    if nan_count > 0:
        logging.warning(f"Found {nan_count} NaN values in computed descriptors. "
                      "Rows with NaN in required columns will be dropped.")
    
    # Drop rows with NaN in required descriptor columns
    # Required columns are all descriptor columns (non-smiles, non-target)
    required_cols = [col for col in desc_df.columns if not col.startswith('smiles')]
    final_df = final_df.dropna(subset=required_cols)
    
    logging.info(f"Dropped {len(df) - len(final_df)} rows due to NaN values in descriptors.")
    
    return final_df

def main():
    """Main entry point for descriptor computation pipeline."""
    # Setup logging
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(description="Compute molecular descriptors from SMILES.")
    parser.add_argument("--input", type=str, default=RAW_DATA_PATH,
                      help=f"Path to raw SMILES CSV (default: {RAW_DATA_PATH})")
    parser.add_argument("--output", type=str, default=os.path.join(DATA_PATH, "processed", "descriptors.csv"),
                      help="Path to output descriptors CSV")
    args = parser.parse_args()
    
    try:
        # 1. Load raw SMILES data
        logging.info(f"Loading raw SMILES from: {args.input}")
        raw_df = load_smiles_from_file(args.input)
        logging.info(f"Loaded {len(raw_df)} rows. {raw_df['valid'].sum()} valid.")
        
        # 2. Clean data
        clean_df = clean_dataframe(raw_df)
        if clean_df.empty:
            logging.error("No valid data to process. Exiting.")
            sys.exit(1)
        
        # 3. Compute all descriptors
        logging.info("Computing descriptors...")
        descriptor_df = compute_all_descriptors(clean_df)
        
        if descriptor_df.empty:
            logging.error("No descriptors computed. Exiting.")
            sys.exit(1)
        
        # 4. Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Created output directory: {output_dir}")
        
        # 5. Write to CSV
        descriptor_df.to_csv(args.output, index=False)
        logging.info(f"Successfully wrote {len(descriptor_df)} rows to {args.output}")
        
        # 6. Verify output schema (basic check)
        expected_cols = [
            'degree_mean', 'degree_std', 'degree_max', 'degree_min',
            'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
            'aromaticity_index', 'ring_count',
            'conjugation_length', 'num_conjugated_bonds', 'conjugation_density',
            'aromatic_ring_count', 'conjugated_ring_count'
        ]
        
        missing_cols = [col for col in expected_cols if col not in descriptor_df.columns]
        if missing_cols:
            logging.warning(f"Missing expected columns: {missing_cols}")
        else:
            logging.info("All expected descriptor columns present.")
            
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
