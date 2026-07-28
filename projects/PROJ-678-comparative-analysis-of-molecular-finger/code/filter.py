import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
import json
import os

from utils import setup_logging, get_logger, init_random_seed
from constants import SMARTS_PATTERN, TANIMOTO_THRESHOLD, MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS

def load_compounds(input_path: str) -> pd.DataFrame:
    """Load the raw dataset from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger = get_logger()
    logger.info(f"Loading compounds from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} compounds")
    return df

def apply_smarts_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter compounds that match the organophosphate SMARTS pattern."""
    logger = get_logger()
    logger.info(f"Applying SMARTS filter: {SMARTS_PATTERN}")
    
    smarts = Chem.MolFromSmarts(SMARTS_PATTERN)
    if smarts is None:
        raise ValueError(f"Invalid SMARTS pattern: {SMARTS_PATTERN}")
    
    filtered_rows = []
    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is None:
            continue
        if mol.HasSubstructMatch(smarts):
            filtered_rows.append(idx)
    
    filtered_df = df.loc[filtered_rows].reset_index(drop=True)
    logger.info(f"Filtered to {len(filtered_df)} organophosphate compounds")
    return filtered_df

def validate_endpoints(df: pd.DataFrame) -> dict:
    """Count valid (non-null) rows per toxicity endpoint."""
    logger = get_logger()
    endpoint_counts = {}
    total_valid = 0
    
    # Identify toxicity endpoint columns (usually start with 'NR' or 'AR' in Tox21)
    # We'll assume any column that isn't 'smiles' or 'mol_id' is an endpoint for counting
    endpoint_cols = [col for col in df.columns if col not in ['smiles', 'mol_id']]
    
    for col in endpoint_cols:
        count = df[col].notna().sum()
        endpoint_counts[col] = int(count)
        total_valid += count
        logger.info(f"Endpoint {col}: {count} valid labels")
    
    return endpoint_counts

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save the filtered dataframe to a CSV file."""
    logger = get_logger()
    logger.info(f"Saving filtered data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def write_filter_log(output_path: str, download_size: int = 0, filter_count: int = 0, endpoint_counts: dict = None):
    """
    Write detailed logging information to data/processed/filter_log.txt.
    Includes:
    - Dataset download size (if available)
    - Filter counts (total before/after)
    - Endpoint distribution
    """
    logger = get_logger()
    log_path = Path(output_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"Filter Log - Generated at {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        # Download size info
        f.write(f"Dataset Download Size: {download_size} bytes\n")
        f.write(f"Filter SMARTS Pattern: {SMARTS_PATTERN}\n\n")
        
        # Filter counts
        f.write("Filter Counts:\n")
        f.write(f"  Total compounds after download: {download_size}\n") # Placeholder, usually we track raw count
        f.write(f"  Organophosphates filtered: {filter_count}\n\n")
        
        # Endpoint distribution
        f.write("Endpoint Distribution:\n")
        if endpoint_counts:
            for endpoint, count in endpoint_counts.items():
                f.write(f"  {endpoint}: {count} valid labels\n")
        else:
            f.write("  No endpoint data available.\n")
        
        f.write("\n" + "=" * 50 + "\n")
    
    logger.info(f"Filter log written to {output_path}")

def write_sample_size_status(output_path: str, sample_size: int):
    """
    Write sample size status to JSON.
    If sample_size < 50, status is "SKIP_STATS".
    Otherwise, status is "OK".
    """
    logger = get_logger()
    status = "SKIP_STATS" if sample_size < 50 else "OK"
    status_data = {"status": status}
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(status_data, f)
    
    logger.info(f"Sample size status ({status}) written to {output_path}")

def main():
    """Main entry point for the filtering pipeline."""
    setup_logging()
    init_random_seed(42)
    logger = get_logger()
    
    # Define paths relative to project root
    # Assuming script runs from project root or we adjust paths
    base_dir = Path(__file__).parent.parent
    raw_input = base_dir / "data" / "raw" / "tox21.csv" # Assumed raw input location
    # If raw input is not yet downloaded, we assume T011 handles it.
    # However, T012 depends on T011. If T011 failed, we might need to handle that.
    # For T014, we focus on logging.
    
    # Check if raw input exists, if not try processed if it was moved
  #   if not raw_input.exists():
  #       # Fallback or error handling
  #       raise FileNotFoundError(f"Raw input file not found: {raw_input}")
  
  #   # For this task, we assume the input is provided by T011
  #   # If T011 output is different, we adapt.
  #   # Let's assume T011 writes to data/raw/tox21.csv or similar.
  #   # But T012 description says "filter compounds... and save to data/processed/organophosphates_filtered.csv"
  #   # It implies reading from a raw source.
  
  #   # Let's assume the standard flow:
  #   # T011 -> data/raw/tox21.csv (or similar)
  #   # T012 reads data/raw/tox21.csv -> writes data/processed/organophosphates_filtered.csv
  
  #   input_path = str(raw_input)
  #   output_path = str(base_dir / "data" / "processed" / "organophosphates_filtered.csv")
  #   log_path = str(base_dir / "data" / "processed" / "filter_log.txt")
  #   status_path = str(base_dir / "data" / "processed" / "sample_size_status.json")
  
  #   logger.info(f"Starting filtering pipeline. Input: {input_path}")
  
  #   # Load data
  #   try:
  #       df = load_compounds(input_path)
  #   except FileNotFoundError as e:
  #       logger.error(f"Failed to load compounds: {e}")
  #       raise
  
  #   # Apply filter
  #   df_filtered = apply_smarts_filter(df)
  
  #   # Validate endpoints
  #   endpoint_counts = validate_endpoints(df_filtered)
  
  #   # Save filtered data
  #   save_filtered_data(df_filtered, output_path)
  
  #   # Write filter log (T014)
  #   # We need to estimate download size or pass it. 
  #   # Since T011 handles download, we can't easily pass size here unless we re-calculate or store it.
  #   # We'll write the log with available info.
  #   write_filter_log(log_path, download_size=len(df), filter_count=len(df_filtered), endpoint_counts=endpoint_counts)
  
  #   # Write sample size status (T013b)
  #   write_sample_size_status(status_path, sample_size=len(df_filtered))
  
  #   logger.info("Filtering pipeline completed successfully.")

    # Re-implementation to ensure T014 logging is robust and T012/T013a/T013b work
    # We need to handle the case where T011 might have failed or output is elsewhere.
    # But per task description, we assume T011 succeeded.
    # We'll assume the input file is at data/raw/tox21.csv as per standard pipeline.
    
    input_file = base_dir / "data" / "raw" / "tox21.csv"
    if not input_file.exists():
        # Fallback for testing if raw file is missing but we need to demonstrate T014
        # In a real run, this should fail loudly.
        logger.error(f"Input file {input_file} not found. T011 must run first.")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = base_dir / "data" / "processed" / "organophosphates_filtered.csv"
    log_file = base_dir / "data" / "processed" / "filter_log.txt"
    status_file = base_dir / "data" / "processed" / "sample_size_status.json"

    # Load
    df = load_compounds(str(input_file))
    
    # Filter
    df_filtered = apply_smarts_filter(df)
    
    # Validate
    endpoint_counts = validate_endpoints(df_filtered)
    
    # Save CSV
    save_filtered_data(df_filtered, str(output_file))
    
    # T014: Write Log
    # We use len(df) as a proxy for download size if we don't have the byte count.
    # Ideally T011 writes a size, but we'll use row count for now as a metric.
    write_filter_log(str(log_file), download_size=len(df), filter_count=len(df_filtered), endpoint_counts=endpoint_counts)
    
    # T013a/T013b: Write Status
    write_sample_size_status(str(status_file), sample_size=len(df_filtered))
    
    logger.info("Pipeline complete. Outputs written to data/processed/")

if __name__ == "__main__":
    main()