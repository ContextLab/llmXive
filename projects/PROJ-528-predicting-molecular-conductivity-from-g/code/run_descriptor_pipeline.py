"""
Run the complete descriptor computation pipeline.
This script orchestrates the loading of SMILES, computation of all descriptors,
and saving the results to the appropriate output files.
"""
import sys
import os
import argparse
import logging
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.logging_config import setup_logging
from code.data_loader import load_smiles
from code.descriptors import compute_all_descriptors
from code.save_descriptors import validate_and_save_descriptors

def load_smiles_from_file(path: str) -> pd.DataFrame:
    """Load SMILES from a CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"SMILES file not found: {path}")
    
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        raise ValueError("CSV must contain a 'smiles' column")
    
    return df

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the dataframe by removing invalid SMILES and duplicates."""
    # Remove rows with empty or None SMILES
    df = df[df['smiles'].notna() & (df['smiles'].str.strip() != '')]
    
    # Remove duplicates based on SMILES
    df = df.drop_duplicates(subset=['smiles'])
    
    return df.reset_index(drop=True)

def compute_all_descriptors(smiles_df: pd.DataFrame) -> pd.DataFrame:
    """Compute all descriptors for the given SMILES dataframe."""
    # Use the compute_all_descriptors function from descriptors module
    return compute_all_descriptors(smiles_df)

def main():
    """Main entry point for the descriptor pipeline."""
    parser = argparse.ArgumentParser(description="Run the complete descriptor computation pipeline.")
    parser.add_argument("--input", type=str, default="data/raw/smiles.csv",
                      help="Path to input SMILES CSV file")
    parser.add_argument("--output-base", type=str, default="data/processed/descriptors_base.csv",
                      help="Path to output base descriptors CSV")
    parser.add_argument("--output-full", type=str, default="data/processed/descriptors.csv",
                      help="Path to output full descriptors CSV")
    parser.add_argument("--validate", action="store_true",
                      help="Validate output against schema")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        # Load SMILES
        logging.info(f"Loading SMILES from {args.input}")
        smiles_df = load_smiles_from_file(args.input)
        logging.info(f"Loaded {len(smiles_df)} SMILES entries")
        
        # Clean data
        logging.info("Cleaning data...")
        smiles_df = clean_dataframe(smiles_df)
        logging.info(f"Cleaned data: {len(smiles_df)} entries")
        
        # Compute all descriptors
        logging.info("Computing descriptors...")
        descriptor_df = compute_all_descriptors(smiles_df)
        logging.info(f"Computed descriptors for {len(descriptor_df)} molecules")
        
        # Save base descriptors (T019a)
        # For now, we save the full descriptor set as both base and full
        # In a more complex implementation, we might split them
        logging.info(f"Saving base descriptors to {args.output_base}")
        validate_and_save_descriptors(descriptor_df, args.output_base)
        
        # Save full descriptors (T019b)
        logging.info(f"Saving full descriptors to {args.output_full}")
        validate_and_save_descriptors(descriptor_df, args.output_full)
        
        logging.info("Descriptor pipeline completed successfully.")
        
    except Exception as e:
        logging.error(f"Error in descriptor pipeline: {e}")
        raise

if __name__ == "__main__":
    main()
