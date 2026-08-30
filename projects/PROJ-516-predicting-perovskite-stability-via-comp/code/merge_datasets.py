import logging
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from utils.state_manager import compute_sha256, update_artifact_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_csv_safe(file_path: Path) -> pd.DataFrame:
    """
    Safely load a CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        DataFrame containing the CSV data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError(f"Source file is empty: {file_path}")
        logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        return df
    except pd.errors.EmptyDataError:
        raise ValueError(f"Source file is empty or invalid: {file_path}")

def merge_perovskite_datasets(nrel_path: Path, mp_path: Path, output_path: Path) -> Tuple[int, int]:
    """
    Merge NREL and Materials Project datasets.
    
    This function:
    1. Loads both source CSVs.
    2. Concatenates the DataFrames.
    3. Drops duplicates based on 'formula' and 'source'.
    4. Logs the count of removed duplicates.
    5. Writes the final merged dataset to the output path.
    6. Updates the state file with the new artifact hash.
    
    Args:
        nrel_path: Path to the NREL source CSV.
        mp_path: Path to the Materials Project source CSV.
        output_path: Path where the merged CSV will be written.
        
    Returns:
        A tuple (original_count, duplicate_count).
    """
    logger.info(f"Starting merge: {nrel_path.name} + {mp_path.name}")
    
    df_nrel = load_csv_safe(nrel_path)
    df_mp = load_csv_safe(mp_path)
    
    # Ensure both have a 'source' column to distinguish origin if not already present
    # The fetch tasks (T012a, T012b) should have added this, but we enforce it here for safety
    if 'source' not in df_nrel.columns:
        df_nrel['source'] = 'nrel'
    if 'source' not in df_mp.columns:
        df_mp['source'] = 'materials_project'
    
    original_count = len(df_nrel) + len(df_mp)
    
    # Concatenate
    merged_df = pd.concat([df_nrel, df_mp], ignore_index=True)
    
    # Drop duplicates based on 'formula' and 'source'
    # FR-001 requires fetching both sources, but we must avoid identical entries
    if 'formula' not in merged_df.columns:
        raise ValueError("Merged data must contain a 'formula' column for deduplication.")
        
    initial_len = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['formula', 'source'], keep='first')
    final_len = len(merged_df)
    duplicates_removed = initial_len - final_len
    
    logger.info(f"Merged dataset: {initial_len} -> {final_len} rows")
    logger.info(f"Removed {duplicates_removed} duplicate entries based on (formula, source).")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Written merged dataset to {output_path}")
    
    # Update state
    state_hash = compute_sha256(output_path)
    update_artifact_state(output_path, state_hash)
    logger.info(f"Updated state with hash: {state_hash}")
    
    return original_count, duplicates_removed

def main():
    """Main entry point for the merge task."""
    base_dir = Path(__file__).resolve().parent.parent
    nrel_path = base_dir / "data" / "raw" / "nrel_perovskites.csv"
    mp_path = base_dir / "data" / "raw" / "mp_perovskites.csv"
    output_path = base_dir / "data" / "raw" / "perovskites_merged.csv"
    
    if not nrel_path.exists():
        logger.error(f"Required input missing: {nrel_path}. Run T012a first.")
        sys.exit(1)
    if not mp_path.exists():
        logger.error(f"Required input missing: {mp_path}. Run T012b first.")
        sys.exit(1)
        
    try:
        total_rows, dups = merge_perovskite_datasets(nrel_path, mp_path, output_path)
        logger.info(f"Merge complete. Total rows processed: {total_rows}, Duplicates removed: {dups}")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()