import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
import json
import os

from constants import SMARTS_PATTERN
from utils import setup_logging, init_random_seed, get_logger

# Ensure random seed is set for reproducibility
init_random_seed(42)
logger = get_logger(__name__)

def load_compounds(input_path: str) -> pd.DataFrame:
    """
    Load the raw dataset from the previous step (download.py).
    Expects a CSV with 'smiles' and at least one toxicity endpoint column.
    """
    logger.info(f"Loading compounds from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['smiles']
    # Check if required columns exist
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter out rows with invalid or empty SMILES
    valid_indices = []
    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is not None:
            valid_indices.append(idx)
    
    logger.info(f"Loaded {len(df)} rows, {len(valid_indices)} valid SMILES")
    return df.loc[valid_indices].reset_index(drop=True)

def apply_smarts_filter(df: pd.DataFrame, pattern: str = SMARTS_PATTERN) -> pd.DataFrame:
    """
    Apply the SMARTS pattern to filter for organophosphates.
    Returns a dataframe containing only compounds matching the pattern.
    """
    logger.info(f"Applying SMARTS filter: {pattern}")
    mol_pattern = Chem.MolFromSmarts(pattern)
    if mol_pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {pattern}")
    
    filtered_indices = []
    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is not None:
            if mol.HasSubstructMatch(mol_pattern):
                filtered_indices.append(idx)
    
    logger.info(f"Filter matched {len(filtered_indices)} compounds")
    return df.loc[filtered_indices].reset_index(drop=True)

def validate_endpoints(df: pd.DataFrame) -> dict:
    """
    Count rows per toxicity endpoint to ensure data quality.
    Returns a dictionary of endpoint counts.
    """
    counts = {}
    for col in df.columns:
        if col != 'smiles':
            # Count non-null entries
            counts[col] = int(df[col].notna().sum())
    return counts

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """
    Save the filtered dataframe to CSV.
    """
    logger.info(f"Saving filtered data to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def write_filter_log(output_dir: str, total_input: int, filtered_count: int, endpoint_counts: dict):
    """
    Write the filter log to data/processed/filter_log.txt.
    Handles the sample size warning logic.
    """
    log_path = Path(output_dir) / "filter_log.txt"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Filter Log - {datetime.now().isoformat()}\n")
        f.write(f"Total input compounds: {total_input}\n")
        f.write(f"Filtered (organophosphates): {filtered_count}\n")
        f.write("Endpoint Distribution:\n")
        for endpoint, count in endpoint_counts.items():
            f.write(f"  {endpoint}: {count}\n")
        
        # Check sample size
        if filtered_count < 50:
            f.write("\nWARNING: Low Sample Size (n < 50)\n")
            logger.warning(f"Low sample size detected: {filtered_count} < 50")
        else:
            f.write("\nstatus: OK\n")
            logger.info(f"Sample size OK: {filtered_count} >= 50")

def write_sample_size_status(output_dir: str, count: int):
    """
    Write sample_size_status.json based on the filtered count.
    """
    status_path = Path(output_dir) / "sample_size_status.json"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    status = "SKIP_STATS" if count < 50 else "OK"
    data = {"status": status}
    
    with open(status_path, 'w') as f:
        json.dump(data, f)
    
    logger.info(f"Wrote sample size status: {status} to {status_path}")

def main():
    """
    Main entry point for the filtering pipeline.
    """
    setup_logging()
    input_path = "data/raw/tox21_raw.csv"
    output_dir = "data/processed"
    output_path = Path(output_dir) / "organophosphates_filtered.csv"
    
    # Ensure directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Load compounds
    df = load_compounds(input_path)
    total_input = len(df)
    
    # 2. Apply SMARTS filter
    filtered_df = apply_smarts_filter(df)
    filtered_count = len(filtered_df)
    
    # 3. Validate endpoints
    endpoint_counts = validate_endpoints(filtered_df)
    
    # 4. Save filtered data
    save_filtered_data(filtered_df, str(output_path))
    
    # 5. Write logs and status
    write_filter_log(output_dir, total_input, filtered_count, endpoint_counts)
    write_sample_size_status(output_dir, filtered_count)
    
    logger.info("Filtering complete.")

if __name__ == "__main__":
    main()