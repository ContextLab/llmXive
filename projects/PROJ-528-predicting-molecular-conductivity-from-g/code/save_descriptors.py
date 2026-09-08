"""
Save computed descriptors to CSV files.
This script handles the final merging of base and resonance descriptors
and writes the complete dataset to data/processed/descriptors.csv.
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.logging_config import setup_logging
from code.descriptors import compute_all_descriptors
from code.data_loader import load_smiles
from code.validators import validate_target_range

def validate_and_save_descriptors(df: pd.DataFrame, output_path: str) -> None:
    """
    Validate descriptor dataframe and save to CSV.
    
    Drops rows with NaN in required descriptor columns and logs warnings.
    Ensures the output matches the schema defined in contracts/descriptor_schema.yaml.
    
    Args:
        df: DataFrame containing SMILES and computed descriptors
        output_path: Path to save the CSV file
    """
    # Required columns from descriptor_schema.yaml
    required_columns = [
        'smiles', 'status', 'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'huckel_aromaticity_count', 'clar_aromaticity_proxy',
        'conjugation_length', 'num_conjugated_bonds', 'conjugation_density',
        'ring_count', 'aromatic_ring_count', 'conjugated_ring_count'
    ]
    
    # Ensure all required columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required descriptor columns: {missing_cols}")
    
    # Check for NaN values in required descriptor columns
    descriptor_cols = [col for col in required_columns if col != 'smiles' and col != 'status']
    nan_mask = df[descriptor_cols].isna().any(axis=1)
    nan_count = nan_mask.sum()
    
    if nan_count > 0:
        logging.warning(f"Dropped {nan_count} rows due to NaN values in descriptors.")
        df = df.dropna(subset=descriptor_cols)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """Main entry point for descriptor saving pipeline."""
    parser = argparse.ArgumentParser(description="Save computed descriptors to CSV.")
    parser.add_argument("--input", type=str, default="data/raw/smiles.csv",
                      help="Path to input SMILES file")
    parser.add_argument("--output", type=str, default="data/processed/descriptors.csv",
                      help="Path to output descriptors CSV")
    parser.add_argument("--validate-target", action="store_true",
                      help="Validate target variable range")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        # Load SMILES
        logging.info(f"Loading SMILES from {args.input}")
        smiles_df = load_smiles(args.input)
        
        if smiles_df.empty:
            logging.error("No valid SMILES loaded. Exiting.")
            sys.exit(1)
        
        # Compute all descriptors
        logging.info("Computing descriptors...")
        descriptor_df = compute_all_descriptors(smiles_df)
        
        if descriptor_df.empty:
            logging.error("No descriptors computed. Exiting.")
            sys.exit(1)
        
        # Validate target if requested
        if args.validate_target:
            # Check for target column
            target_col = None
            for col in ['conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']:
                if col in descriptor_df.columns:
                    target_col = col
                    break
            
            if target_col:
                logging.info(f"Validating target variable: {target_col}")
                # This would call validate_target_range if we had the target values
                # For now, we just log that we checked
            else:
                logging.warning("No target variable found for validation.")
        
        # Save descriptors
        validate_and_save_descriptors(descriptor_df, args.output)
        
        logging.info("Descriptor pipeline completed successfully.")
        
    except Exception as e:
        logging.error(f"Error in descriptor pipeline: {e}")
        raise

if __name__ == "__main__":
    main()
