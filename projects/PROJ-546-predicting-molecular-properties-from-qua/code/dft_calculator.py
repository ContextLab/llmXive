import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import logging utility from the established API
from utils.logging_utils import setup_logger

# Constants
LOG_FILE = "logs/dft_execution.log"
SUBSET_SIZE = 50
MIN_REQUIRED_GEOMETRIES = 50

def log_setup() -> logging.Logger:
    """
    Initialize the logger for the DFT calculator.
    Ensures the logs directory exists before creating the file handler.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / LOG_FILE
    
    logger = setup_logger("dft_calculator", str(log_path))
    return logger

def load_raw_dataset(input_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load the raw barrier dataset from CSV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw dataset not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded raw dataset with {len(df)} rows from {input_path}")
    return df

def load_confounds(confounds_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load confounds data to verify T011 completion.
    """
    if not os.path.exists(confounds_path):
        raise FileNotFoundError(f"Confounds file missing (T011 dependency): {confounds_path}")
    
    df = pd.read_csv(confounds_path)
    logger.info(f"Loaded confounds with {len(df)} rows from {confounds_path}")
    return df

def get_valid_geometry_indices(raw_df: pd.DataFrame, logger: logging.Logger) -> List[int]:
    """
    Identify indices of molecules that have corresponding optimized geometry files.
    This implements the requirement: 'If a geometry file is missing (due to T013c failure),
    exclude that molecule from the subset selection.'
    """
    valid_indices = []
    geometry_dir = Path("data/optimized_geometries")
    
    if not geometry_dir.exists():
        raise FileNotFoundError(f"Optimized geometries directory missing (T013c dependency): {geometry_dir}")
    
    # Iterate through the raw dataframe to check for geometry files
    for idx, row in raw_df.iterrows():
        molecule_id = row['molecule_id']
        geom_file = geometry_dir / f"{molecule_id}.xyz"
        
        if geom_file.exists():
            valid_indices.append(idx)
        else:
            logger.debug(f"Geometry missing for molecule {molecule_id}, excluding from subset.")
    
    logger.info(f"Found {len(valid_indices)} valid optimized geometries out of {len(raw_df)} raw samples.")
    return valid_indices

def stratified_subset_selection(
    raw_df: pd.DataFrame,
    valid_indices: List[int],
    target_size: int,
    logger: logging.Logger
) -> List[int]:
    """
    Select a stratified subset of molecules based on experimental_barrier.
    
    Logic:
    1. Filter raw_df to only include molecules with valid geometries (valid_indices).
    2. If count < MIN_REQUIRED_GEOMETRIES, raise RuntimeError.
    3. If count >= target_size, select exactly target_size rows using stratified sampling.
    4. If count < target_size, select all valid rows.
    
    Stratification uses pd.qcut on 'experimental_barrier'.
    """
    subset_df = raw_df.loc[valid_indices].copy()
    n_valid = len(subset_df)
    
    logger.info(f"Attempting to select subset from {n_valid} valid samples.")
    
    if n_valid < MIN_REQUIRED_GEOMETRIES:
        raise RuntimeError(
            f"Insufficient optimized geometries for stratified subset (N={n_valid} < {MIN_REQUIRED_GEOMETRIES}). "
            "Pipeline halted."
        )
    
    final_size = min(n_valid, target_size)
    
    # Prepare data for stratification
    # Ensure experimental_barrier is numeric
    if not pd.api.types.is_numeric_dtype(subset_df['experimental_barrier']):
        raise ValueError("experimental_barrier column must be numeric for stratification.")
    
    # Determine number of bins. 
    # Strategy: Use min(final_size, 10) bins to ensure enough samples per bin if possible,
    # but not more bins than samples.
    n_bins = min(final_size, 10)
    
    # Use qcut to create bins. Handle cases with too few unique values by dropping duplicates if necessary,
    # but qcut usually handles ties by assigning same bin or raising error if not enough unique values.
    # We catch the exception and fallback to a smaller number of bins if needed.
    try:
        subset_df['bin'] = pd.qcut(subset_df['experimental_barrier'], q=n_bins, duplicates='drop')
    except ValueError as e:
        # If qcut fails (e.g., not enough unique values for n_bins), reduce bins
        logger.warning(f"qcut failed with {n_bins} bins: {e}. Retrying with fewer bins.")
        unique_vals = subset_df['experimental_barrier'].nunique()
        if unique_vals < 2:
            logger.warning("Only 1 unique value in experimental_barrier. Cannot stratify. Selecting random subset.")
            subset_df['bin'] = 0 # All in one bin
        else:
            subset_df['bin'] = pd.qcut(subset_df['experimental_barrier'], q=unique_vals, duplicates='drop')

    # Perform stratified sampling
    # We need to sample from the indices of the original dataframe, not the subset indices directly,
    # but since we have the subset_df, we can sample indices from it and map back if needed.
    # However, the requirement is to return indices from the original dataframe (valid_indices are original indices).
    # subset_df is a view/copy of raw_df[valid_indices], so its index is the original index.
    
    sampled_indices = subset_df.groupby('bin', group_keys=False).apply(
        lambda x: x.sample(n=min(int(np.ceil(len(x) * final_size / n_valid)), len(x)), random_state=42)
    ).index.tolist()
    
    # Fallback if sampling logic fails to pick enough (rare edge case)
    if len(sampled_indices) < final_size:
        logger.warning("Stratified sampling did not reach target size. Filling with random samples.")
        remaining = final_size - len(sampled_indices)
        available = [i for i in valid_indices if i not in sampled_indices]
        if available:
            extra = np.random.choice(available, size=min(remaining, len(available)), replace=False).tolist()
            sampled_indices.extend(extra)
    
    logger.info(f"Selected {len(sampled_indices)} molecules for DFT calculation.")
    return sampled_indices

def write_subset_indices(indices: List[int], output_path: str, logger: logging.Logger):
    """
    Write the selected subset indices to a CSV file for downstream tasks (T020b).
    """
    Path(output_path).parent.mkdir(exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['molecule_id', 'original_index'])
        # We need to map back to molecule_id if possible, but the requirement says 'indices'.
        # The task description says 'Write split indices to state/splits.json' in T020b,
        # but T020a specifically says 'Write subset indices'. 
        # Let's write a CSV with the indices and the corresponding molecule_id for clarity.
        # Since we don't have the full dataframe here, we assume the caller passes the df or we re-read.
        # Actually, the function signature above doesn't have df. Let's adjust logic to return indices.
        # The caller (main) will have the df.
        pass 
    # Correction: The task says 'write subset indices'. Let's write a simple list or CSV.
    # T020b expects to read this. Let's write a CSV with indices.
    # Since we are in T020a, we will write the list of indices.
    # But to be safe for T020b which needs to map to molecules, let's write the molecule_ids too.
    # However, the prompt says 'write subset indices'.
    # Let's write a JSON file as it's easier for T020b to parse, or a simple CSV.
    # The task description for T020b says 'Read data/raw/barrier_dataset.csv...'.
    # So T020b will likely re-load the CSV and filter by these indices.
    # Let's write a CSV of indices.
    
    # Re-implementing write logic here to be self-contained in the artifact
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index'])
        for idx in indices:
            writer.writerow([idx])
    
    logger.info(f"Wrote {len(indices)} subset indices to {output_path}")

def main():
    logger = log_setup()
    logger.info("Starting T020a: Subset Selection Logic")
    
    try:
        # 1. Dependency Check: data/raw/barrier_dataset.csv
        raw_csv_path = "data/raw/barrier_dataset.csv"
        if not os.path.exists(raw_csv_path):
            raise FileNotFoundError(f"Raw dataset missing (T004b dependency): {raw_csv_path}")
        
        raw_df = load_raw_dataset(raw_csv_path, logger)
        
        # 2. Dependency Check: data/confounds.csv
        confounds_path = "data/confounds.csv"
        load_confounds(confounds_path, logger) # Just verify it exists and loads
        
        # 3. Dependency Check: data/optimized_geometries/
        # This is implicitly checked in get_valid_geometry_indices, but we check dir existence here too
        geom_dir = Path("data/optimized_geometries")
        if not geom_dir.exists():
            raise FileNotFoundError(f"Optimized geometries directory missing (T013c dependency): {geom_dir}")
        
        # 4. Identify valid geometries
        valid_indices = get_valid_geometry_indices(raw_df, logger)
        
        # 5. Select subset
        selected_indices = stratified_subset_selection(raw_df, valid_indices, SUBSET_SIZE, logger)
        
        # 6. Write output
        output_path = "data/subset_indices.csv"
        write_subset_indices(selected_indices, output_path, logger)
        
        logger.info("T020a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Dependency missing: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()