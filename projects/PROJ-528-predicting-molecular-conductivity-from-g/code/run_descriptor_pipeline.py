import sys
import os
import argparse
import logging
import pandas as pd
import numpy as np
from code.logging_config import setup_logging
from code.data_loader import load_smiles
from code.descriptors import compute_standard_descriptors
from code.config import TARGET_VAR

logger = setup_logging(__name__)

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """Load SMILES from CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        raise ValueError("Input CSV must contain 'smiles' column.")
    
    return df[['smiles']]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove invalid SMILES and duplicates."""
    valid_df = df[df['valid'] == True].copy()
    valid_df = valid_df.drop_duplicates(subset=['smiles'])
    return valid_df

def compute_all_descriptors(smiles_list: list) -> pd.DataFrame:
    """Compute descriptors for a list of SMILES."""
    results = []
    for smiles in smiles_list:
        try:
            desc = compute_standard_descriptors(smiles)
            if desc is not None:
                desc['smiles'] = smiles
                desc['status'] = 'valid'
                results.append(desc)
            else:
                logger.warning(f"Failed to compute descriptors for: {smiles}")
        except Exception as e:
            logger.error(f"Error computing descriptors for {smiles}: {e}")
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Run descriptor computation pipeline.")
    parser.add_argument('--input', type=str, required=True, help='Input CSV with SMILES')
    parser.add_argument('--output', type=str, required=True, help='Output CSV for descriptors')
    args = parser.parse_args()
    
    logger.info(f"Loading SMILES from {args.input}")
    df = load_smiles_from_file(args.input)
    
    logger.info("Validating SMILES...")
    df_valid = load_smiles(args.input)
    df_valid = clean_dataframe(df_valid)
    
    logger.info(f"Computing descriptors for {len(df_valid)} valid molecules...")
    descriptors_df = compute_all_descriptors(df_valid['smiles'].tolist())
    
    if len(descriptors_df) == 0:
        raise ValueError("No valid descriptors computed.")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    logger.info(f"Saving descriptors to {args.output}")
    descriptors_df.to_csv(args.output, index=False)
    
    print(f"Descriptor computation complete. {len(descriptors_df)} molecules processed.")

if __name__ == "__main__":
    main()
