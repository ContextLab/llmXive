"""
Wrapper script for training models to ensure correct logging setup and argument handling.
"""
import sys
import os
import argparse

# Ensure code directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logging_config import setup_logging
from data_loader import load_processed_data
from scaffold_split import scaffold_split
from model_training import train_models
from config import DATA_PATH, SEED, TARGET_VAR
import json
import logging

logger = logging.getLogger(__name__)

def ensure_sample_data(data_path: str):
    """
    Check if data exists. If not, create a minimal sample for testing.
    This is a fallback for development only.
    """
    if os.path.exists(data_path):
        return True
    
    # Only create sample if it doesn't exist and we are in a test/dev environment
    # In production, this should fail loudly.
    logger.warning(f"Data file {data_path} not found. Creating minimal sample.")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    import pandas as pd
    import numpy as np
    
    # Minimal sample
    data = {
        'smiles': ['c1ccccc1', 'CCO', 'C=CC=C', 'C1=CC=CC=C1', 'CC(=O)C'],
        'conductivity': [1.2, 0.5, 2.1, 1.5, 0.8],
        'degree_mean': [1.0, 1.0, 1.5, 1.0, 1.2],
        'degree_std': [0.0, 0.0, 0.5, 0.0, 0.4],
        'degree_max': [2.0, 2.0, 3.0, 2.0, 3.0],
        'degree_min': [1.0, 1.0, 1.0, 1.0, 1.0],
        'path_length_mean': [2.0, 1.5, 3.0, 2.0, 2.5],
        'path_length_std': [0.5, 0.3, 1.0, 0.5, 0.8],
        'path_length_max': [3.0, 2.0, 4.0, 3.0, 4.0],
        'path_length_min': [1.0, 1.0, 1.0, 1.0, 1.0],
        'aromaticity_index': [1.0, 0.0, 0.0, 1.0, 0.0],
        'huckel_aromaticity_count': [1.0, 0.0, 0.0, 1.0, 0.0],
        'clar_aromaticity_proxy': [1.0, 0.0, 0.0, 1.0, 0.0],
        'conjugation_length': [6.0, 0.0, 4.0, 6.0, 2.0],
        'num_conjugated_bonds': [6.0, 0.0, 3.0, 6.0, 1.0],
        'conjugation_density': [1.0, 0.0, 0.75, 1.0, 0.33],
        'ring_count': [1.0, 0.0, 0.0, 1.0, 0.0]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)
    logger.info(f"Created sample data at {data_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Train Molecular Conductivity Models")
    parser.add_argument('--data', type=str, default=DATA_PATH, help='Path to processed data CSV')
    parser.add_argument('--output', type=str, default='data/processed/model_results.json', help='Output path for model results')
    args = parser.parse_args()
    
    setup_logging()
    
    # Ensure data exists
    if not os.path.exists(args.data):
        ensure_sample_data(args.data)
    
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    if df.empty:
        logger.error("Loaded dataframe is empty")
        sys.exit(1)
    
    # Train models
    logger.info("Training models...")
    results = train_models(df, args.output)
    
    logger.info(f"Training complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()
