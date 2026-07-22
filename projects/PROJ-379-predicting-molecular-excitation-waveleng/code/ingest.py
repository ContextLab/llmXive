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

# Import from existing project modules
from utils import get_logger, validate_molecule, parse_smiles

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

def process_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES, validate with RDKit, and handle duplicates.
    """
    logger.info("Parsing and validating molecules...")
    valid_rows = []
    invalid_count = 0
    duplicate_map = {}

    for idx, row in df.iterrows():
        smi = row.get("smiles") or row.get("smi")
        lambda_max = row.get("lambda_max_exp")

        if not smi or pd.isna(lambda_max):
            invalid_count += 1
            continue

        mol = parse_smiles(smi)
        if mol is None:
            invalid_count += 1
            continue

        if not validate_molecule(mol):
            invalid_count += 1
            continue

        # Handle duplicates by averaging lambda_max
        if smi in duplicate_map:
            duplicate_map[smi].append(lambda_max)
        else:
            duplicate_map[smi] = [lambda_max]
            valid_rows.append({"smi": smi, "lambda_max": lambda_max})

    # Resolve duplicates by taking median
    resolved_rows = []
    for smi, values in duplicate_map.items():
        if len(values) > 1:
            median_val = float(np.median(values))
            logger.info(f"Duplicate found for {smi}: values {values} -> median {median_val}")
            resolved_rows.append({"smi": smi, "lambda_max": median_val})
        else:
            resolved_rows.append({"smi": smi, "lambda_max": values[0]})

    logger.info(f"Invalid molecules: {invalid_count}")
    logger.info(f"Original valid rows: {len(valid_rows)}")
    logger.info(f"Resolved duplicate rows: {len(resolved_rows)}")

    return pd.DataFrame(resolved_rows)

def main():
    """
    Main entry point for data ingestion.
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Fetch data
    raw_df = fetch_uv_vis_data()
    
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
