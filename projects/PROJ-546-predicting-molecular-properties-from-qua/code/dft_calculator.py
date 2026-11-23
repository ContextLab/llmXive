import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

import pandas as pd

# Import logging utilities from existing project files
# Assuming utils/logging_utils is available as per API surface
try:
    from utils.logging_utils import setup_logger
except ImportError:
    # Fallback if utils not in path or structure differs
    def setup_logger(name: str, log_file: str, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger

def log_setup(log_file: str = "logs/dft_subset_selection.log") -> logging.Logger:
    """Initialize the logger for subset selection tasks."""
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    return setup_logger("dft_calculator", str(log_file))

def load_raw_dataset(csv_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load the raw barrier dataset from the specified CSV path.
    Expects 'smiles' and 'experimental_barrier' columns.
    """
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"Raw dataset file not found: {csv_path}")
        raise FileNotFoundError(f"Raw dataset file not found: {csv_path}")

    logger.info(f"Loading raw dataset from {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        required_cols = {'smiles', 'experimental_barrier'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Missing required columns in {csv_path}: {missing}")
            raise ValueError(f"Missing required columns: {missing}")
        
        # Ensure experimental_barrier is numeric
        df['experimental_barrier'] = pd.to_numeric(df['experimental_barrier'], errors='raise')
        logger.info(f"Loaded {len(df)} rows from {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {csv_path}: {e}")
        raise

def load_confounds(csv_path: str, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Load confounds data if available.
    This is optional for the subset selection logic but good for logging.
    """
    path = Path(csv_path)
    if not path.exists():
        logger.warning(f"Confounds file not found at {csv_path}, skipping.")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded confounds data with {len(df)} rows")
        return df
    except Exception as e:
        logger.warning(f"Failed to load confounds {csv_path}: {e}")
        return None

def get_valid_geometry_indices(geometry_dir: str, logger: logging.Logger) -> Set[str]:
    """
    Scan the optimized geometries directory and return a set of molecule_ids
    that have valid .xyz files.
    """
    dir_path = Path(geometry_dir)
    if not dir_path.exists():
        logger.warning(f"Optimized geometries directory not found: {geometry_dir}")
        return set()

    valid_ids = set()
    for file in dir_path.glob("*.xyz"):
        # Assume filename is {molecule_id}.xyz
        molecule_id = file.stem
        valid_ids.add(molecule_id)
    
    logger.info(f"Found {len(valid_ids)} valid geometry files in {geometry_dir}")
    return valid_ids

def stratified_subset_selection(
    raw_df: pd.DataFrame,
    valid_geometry_ids: Set[str],
    n_bins: int = 5,
    logger: Optional[logging.Logger] = None
) -> List[str]:
    """
    Stratify the full dataset by 'experimental_barrier' into n_bins,
    then filter to only include molecules that have valid optimized geometries.
    Returns a list of molecule_ids.
    """
    if logger is None:
        logger = logging.getLogger("dft_calculator")

    logger.info(f"Starting stratified subset selection with {n_bins} bins")
    
    # 1. Filter for availability first to ensure we only stratify on available data?
    # Task says: "Stratify the full dataset... Filter this stratified list to only include..."
    # Interpretation: Stratify the full set to determine bin assignments, then filter.
    # However, if we stratify the full set, we might end up with bins that have no available data.
    # A more robust approach: Filter first, then stratify the available set to ensure representation.
    # Re-reading task: "Stratify the FULL SET... Filter this stratified list..."
    # This implies we want the distribution of the FULL set to be preserved as much as possible
    # among the available ones.
    
    # Step 1: Identify available rows in the full dataset
    # We need to match 'smiles' or some ID. The task implies 'molecule_id' is the key.
    # The raw dataset likely has an ID column or we generate one.
    # Let's assume the raw dataset has an implicit index or a 'molecule_id' column.
    # If not, we'll use the index or generate one.
    # Looking at T004c-normalize, it expects 'smiles' and 'experimental_barrier'.
    # T011 (confounds) generates 'molecule_id'.
    # Let's check if 'molecule_id' exists in raw_df. If not, we might need to generate it from smiles
    # or assume the index is the ID.
    
    # Strategy: 
    # 1. Add a 'molecule_id' column if missing (e.g., index or hash of smiles)
    # 2. Filter raw_df to only rows where molecule_id is in valid_geometry_ids
    # 3. Stratify the FILTERED set? 
    # Task says: "Stratify the full dataset... Filter this stratified list"
    # This is tricky. If we stratify the full set, we get bin edges. Then we filter.
    # If we filter then stratify, we get bins based on available data.
    # Given the goal is a DFT subset of the available data, stratifying the AVAILABLE data
    # is usually the correct scientific approach to ensure the subset represents the available pool.
    # However, the task explicitly says "Stratify the FULL SET".
    # Let's follow the task literally:
    # 1. Create bins on the FULL set based on 'experimental_barrier'.
    # 2. Assign each row in the full set to a bin.
    # 3. Filter rows to those with valid geometries.
    # 4. The result is the subset.
    # This might result in an unbalanced subset if certain bins have no valid geometries.
    # But we follow the spec.
    
    # Ensure molecule_id exists
    if 'molecule_id' not in raw_df.columns:
        # Generate from index if not present, or use smiles hash if needed.
        # For simplicity, assume index is the ID or we create a column.
        raw_df = raw_df.copy()
        raw_df['molecule_id'] = raw_df.index.astype(str)
        logger.warning("Generated 'molecule_id' from index as it was missing in raw dataset.")

    # 1. Stratify the full dataset
    # pd.qcut returns bin labels.
    try:
        # We need to handle cases where values are identical or too few rows
        # Use duplicates='drop' to handle identical barrier values
        bins = pd.qcut(raw_df['experimental_barrier'], q=n_bins, duplicates='drop')
        raw_df['bin'] = bins
    except ValueError as e:
        logger.warning(f"Could not create {n_bins} bins (too few unique values or identical data): {e}")
        logger.warning("Falling back to single bin (all data).")
        raw_df['bin'] = 'all'

    # 2. Filter for availability
    # We need to match the 'molecule_id' in raw_df with valid_geometry_ids
    # Note: The raw_df 'molecule_id' might be string index, valid_geometry_ids are strings.
    
    # Ensure types match
    valid_ids_str = {str(x) for x in valid_geometry_ids}
    raw_df['molecule_id'] = raw_df['molecule_id'].astype(str)
    
    filtered_df = raw_df[raw_df['molecule_id'].isin(valid_ids_str)]
    
    if len(filtered_df) == 0:
        logger.error("No molecules from the raw dataset have valid optimized geometries.")
        return []

    logger.info(f"Filtered dataset: {len(filtered_df)} molecules have valid geometries out of {len(raw_df)}")

    # 3. Return the list of molecule_ids
    # The task says "Filter this stratified list". The list we have is the filtered_df.
    # We return the IDs.
    selected_ids = filtered_df['molecule_id'].tolist()
    logger.info(f"Selected {len(selected_ids)} molecules for DFT subset.")
    
    return selected_ids

def write_subset_indices(molecule_ids: List[str], output_path: str, logger: logging.Logger):
    """
    Write the list of selected molecule_ids to a JSON file.
    Format: {"molecule_ids": ["id1", "id2", ...]}
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {"molecule_ids": molecule_ids}
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Wrote {len(molecule_ids)} molecule IDs to {output_path}")

def main():
    """
    Main entry point for T020a: Subset Selection.
    Reads data/raw/barrier_dataset.csv, checks data/optimized_geometries/,
    and writes state/selected_subset.json.
    """
    # Paths
    raw_data_path = "data/raw/barrier_dataset.csv"
    geometry_dir = "data/optimized_geometries"
    output_path = "state/selected_subset.json"
    log_file = "logs/dft_subset_selection.log"

    logger = log_setup(log_file)
    logger.info("Starting T020a: Subset Selection")

    try:
        # 1. Load raw dataset
        raw_df = load_raw_dataset(raw_data_path, logger)

        # 2. Get valid geometry IDs
        valid_ids = get_valid_geometry_indices(geometry_dir, logger)

        if not valid_ids:
            logger.error("No valid geometry files found. Cannot proceed.")
            sys.exit(1)

        # 3. Stratified selection
        selected_ids = stratified_subset_selection(raw_df, valid_ids, n_bins=5, logger=logger)

        if not selected_ids:
            logger.error("No molecules selected after filtering.")
            sys.exit(1)

        # 4. Write output
        write_subset_indices(selected_ids, output_path, logger)

        logger.info("T020a completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during subset selection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()