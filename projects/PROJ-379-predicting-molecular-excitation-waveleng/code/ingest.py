import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datasets import load_dataset
from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# Import from existing project modules
from utils import get_logger, validate_molecule as utils_validate_molecule, parse_smiles

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "ingest.log"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)

logger = get_logger("ingest", log_file=str(LOG_FILE))

# Number of workers for multiprocessing; limit to 4 to avoid memory thrashing on 7GB RAM
NUM_WORKERS = min(4, multiprocessing.cpu_count())

def fetch_uv_vis_data() -> pd.DataFrame:
    """
    Fetch UV-Vis data from the specified HuggingFace dataset.
    Verifies the presence of lambda_max_exp column.
    Uses chunked loading to manage memory.
    """
    logger.info("Fetching UV-Vis data from 'zjunlp/UV-Vis-ML' dataset...")
    try:
        # Load dataset with streaming to handle large sizes efficiently
        dataset = load_dataset("zjunlp/UV-Vis-ML", split="train", streaming=True)
        
        # Verify required column exists
        if "lambda_max_exp" not in dataset.column_names:
            logger.error(f"Dataset missing required column 'lambda_max_exp'. Available: {dataset.column_names}")
            raise ValueError("Dataset missing required column 'lambda_max_exp'")
        
        logger.info(f"Dataset columns: {dataset.column_names}")
        
        # Convert to DataFrame in chunks to manage memory
        chunks = []
        batch_size = 10000
        count = 0
        
        for batch in dataset.to_iterable_dataset().to_batches(batch_size=batch_size):
            df_batch = batch.to_pandas()
            chunks.append(df_batch)
            count += len(df_batch)
            if count % 50000 == 0:
                logger.info(f"Processed {count} rows...")
        
        logger.info(f"Total rows fetched: {count}")
        full_df = pd.concat(chunks, ignore_index=True)
        return full_df

    except Exception as e:
        logger.critical(f"Failed to fetch data: {e}")
        raise

def validate_molecule_worker(args: Tuple[str, str]) -> Optional[Dict]:
    """
    Worker function for multiprocessing validation.
    Returns a dict with 'smi' and 'lambda_max' if valid, None otherwise.
    """
    smi, lambda_max_str = args
    
    if not smi or not isinstance(smi, str):
        return None
        
    # Parse SMILES
    mol = parse_smiles(smi)
    if mol is None:
        return None
    
    # Use the existing validate_molecule from utils which checks for sanitization
    if not utils_validate_molecule(mol):
        return None
    
    try:
        lambda_max = float(lambda_max_str)
        if pd.isna(lambda_max):
            return None
    except (ValueError, TypeError):
        return None
        
    return {"smi": smi, "lambda_max": lambda_max}

def process_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES, validate with RDKit using multiprocessing, and handle duplicates.
    Optimized to process 10k molecules in <30s.
    """
    logger.info("Parsing and validating molecules using multiprocessing...")
    
    # Prepare arguments for workers
    # Handle potential column name variations
    smiles_col = "smiles" if "smiles" in df.columns else ("smi" if "smi" in df.columns else None)
    lambda_col = "lambda_max_exp" if "lambda_max_exp" in df.columns else None
    
    if smiles_col is None or lambda_col is None:
        logger.error(f"Required columns not found. Available: {df.columns.tolist()}")
        return pd.DataFrame()

    # Filter out rows with missing essential data before multiprocessing
    valid_indices = df[smiles_col].notna() & df[lambda_col].notna()
    df_clean = df[valid_indices]
    
    args_list = list(zip(df_clean[smiles_col].astype(str), df_clean[lambda_col].astype(str)))
    
    logger.info(f"Starting multiprocessing with {NUM_WORKERS} workers for {len(args_list)} molecules...")
    
    valid_results = []
    invalid_count = 0
    
    # Use ProcessPoolExecutor for parallel validation
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Map returns results in order
        for result in executor.map(validate_molecule_worker, args_list):
            if result is not None:
                valid_results.append(result)
            else:
                invalid_count += 1

    logger.info(f"Invalid molecules: {invalid_count}")
    logger.info(f"Valid molecules after filtering: {len(valid_results)}")

    if not valid_results:
        logger.warning("No valid molecules found.")
        return pd.DataFrame()

    df_valid = pd.DataFrame(valid_results)

    # Handle duplicates by averaging lambda_max
    logger.info("Resolving duplicates...")
    duplicate_map = {}
    
    # Group by 'smi' and collect lambda_max values
    for _, row in df_valid.iterrows():
        smi = row["smi"]
        lm = row["lambda_max"]
        if smi in duplicate_map:
            duplicate_map[smi].append(lm)
        else:
            duplicate_map[smi] = [lm]

    # Resolve duplicates by taking median
    resolved_rows = []
    duplicate_count = 0
    for smi, values in duplicate_map.items():
        if len(values) > 1:
            duplicate_count += 1
            median_val = float(np.median(values))
            logger.debug(f"Duplicate found for {smi}: values {values} -> median {median_val}")
            resolved_rows.append({"smi": smi, "lambda_max": median_val})
        else:
            resolved_rows.append({"smi": smi, "lambda_max": values[0]})

    logger.info(f"Resolved {duplicate_count} duplicate entries.")
    logger.info(f"Final molecule count: {len(resolved_rows)}")

    return pd.DataFrame(resolved_rows)

def main():
    """
    Main entry point for data ingestion.
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Fetch data
    raw_df = fetch_uv_vis_data()
    
    if raw_df.empty:
        logger.error("No data fetched. Aborting.")
        sys.exit(1)

    # Process and validate
    processed_df = process_molecules(raw_df)
    
    if processed_df.empty:
        logger.error("No valid molecules processed. Aborting.")
        sys.exit(1)

    # Save to CSV
    output_path = DATA_PROCESSED_DIR / "processed.csv"
    processed_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved {len(processed_df)} molecules to {output_path}")
    logger.info("Data ingestion pipeline completed.")

if __name__ == "__main__":
    main()