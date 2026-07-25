"""
code/filter.py
Filters the Tox21 dataset for organophosphates using a SMARTS pattern,
validates endpoints, logs statistics, and writes status files.
"""
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
import json
import os

# Import constants and utilities from project modules
from code.constants import SMARTS_PATTERN
from code.utils import setup_logging, get_logger, init_random_seed

# Initialize random seed for reproducibility
init_random_seed(42)

def load_compounds(input_path: str) -> pd.DataFrame:
    """Load the raw Tox21 dataset from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger = get_logger(__name__)
    logger.info(f"Loading compounds from {input_path}")
    return pd.read_csv(input_path)

def apply_smarts_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter compounds that match the SMARTS pattern for organophosphates.
    Uses the SMARTS_PATTERN constant from code/constants.py.
    """
    logger = get_logger(__name__)
    logger.info(f"Applying SMARTS filter: {SMARTS_PATTERN}")
    
    pattern = Chem.MolFromSmarts(SMARTS_PATTERN)
    if pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {SMARTS_PATTERN}")

    # Vectorize the matching logic for performance
    def matches_pattern(smiles):
        if pd.isna(smiles) or not isinstance(smiles, str):
            return False
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        return mol.HasSubstructMatch(pattern)

    mask = df['smiles'].apply(matches_pattern)
    filtered_df = df[mask].reset_index(drop=True)
    
    logger.info(f"Filtered {len(df)} -> {len(filtered_df)} compounds")
    return filtered_df

def validate_endpoints(df: pd.DataFrame) -> dict:
    """
    Count rows per toxicity endpoint.
    Returns a dictionary of endpoint -> count.
    """
    logger = get_logger(__name__)
    endpoint_counts = {}
    
    # Identify toxicity endpoints (columns that are not 'smiles' or 'compound_name')
    # Assuming standard Tox21 schema where endpoints are boolean/float columns
    endpoints = [col for col in df.columns if col not in ['smiles', 'compound_name']]
    
    for endpoint in endpoints:
        if endpoint in df.columns:
            # Count non-null entries
            count = df[endpoint].notna().sum()
            endpoint_counts[endpoint] = int(count)
            logger.debug(f"Endpoint {endpoint}: {count} valid rows")
        
    return endpoint_counts

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save the filtered dataframe to CSV."""
    logger = get_logger(__name__)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

def write_sample_size_status(total_count: int, output_path: str):
    """
    Write sample size status JSON.
    If n < 50, writes {"status": "SKIP_STATS"}.
    Otherwise, writes {"status": "OK"}.
    """
    logger = get_logger(__name__)
    status = "SKIP_STATS" if total_count < 50 else "OK"
    status_data = {"status": status}
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Wrote sample size status: {status} (n={total_count}) to {output_path}")

def write_filter_log(
    download_size: int,
    filter_count_before: int,
    filter_count_after: int,
    endpoint_distribution: dict,
    log_path: str
):
    """
    Write detailed logging for dataset download size, filter counts, and endpoint distribution.
    """
    logger = get_logger(__name__)
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_path, 'w') as f:
        f.write(f"=== Filter Log - {timestamp} ===\n\n")
        
        f.write("--- Dataset Statistics ---\n")
        f.write(f"Download Size (bytes): {download_size}\n")
        f.write(f"Total Compounds Before Filter: {filter_count_before}\n")
        f.write(f"Total Compounds After Filter: {filter_count_after}\n")
        f.write(f"Filter Retention Rate: {(filter_count_after / max(filter_count_before, 1)) * 100:.2f}%\n\n")
        
        f.write("--- Endpoint Distribution ---\n")
        for endpoint, count in sorted(endpoint_distribution.items()):
            f.write(f"{endpoint}: {count}\n")
        
        if filter_count_after < 50:
            f.write("\nWARNING: Low Sample Size (n < 50)\n")
        
        f.write("\n=== End Log ===\n")
    
    logger.info(f"Wrote filter log to {log_path}")

def main():
    """Main entry point for the filtering pipeline."""
    setup_logging()
    logger = get_logger(__name__)
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "tox21.csv"
    filtered_output_path = project_root / "data" / "processed" / "organophosphates_filtered.csv"
    log_output_path = project_root / "data" / "processed" / "filter_log.txt"
    status_output_path = project_root / "data" / "processed" / "sample_size_status.json"
    
    # Simulate download size if file exists (or use actual file size if needed)
    # For this task, we assume the download step has already written the file
    download_size = 0
    if raw_data_path.exists():
        download_size = raw_data_path.stat().st_size
        logger.info(f"Detected raw data size: {download_size} bytes")
    
    # 1. Load compounds
    df = load_compounds(str(raw_data_path))
    count_before = len(df)
    
    # 2. Apply SMARTS filter
    df_filtered = apply_smarts_filter(df)
    count_after = len(df_filtered)
    
    # 3. Validate endpoints
    endpoint_dist = validate_endpoints(df_filtered)
    
    # 4. Save filtered data
    save_filtered_data(df_filtered, str(filtered_output_path))
    
    # 5. Write sample size status
    write_sample_size_status(count_after, str(status_output_path))
    
    # 6. Write filter log with all required metrics
    write_filter_log(
        download_size=download_size,
        filter_count_before=count_before,
        filter_count_after=count_after,
        endpoint_distribution=endpoint_dist,
        log_path=str(log_output_path)
    )
    
    logger.info("Filtering pipeline completed successfully.")

if __name__ == "__main__":
    main()