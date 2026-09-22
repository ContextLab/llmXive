import argparse
import csv
import json
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from config import ZENODO_ID

def log_setup() -> logging.Logger:
    """Setup logging for the DFT calculator."""
    logger = logging.getLogger("dft_calculator")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def load_raw_dataset(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load the raw barrier dataset from data/raw/barrier_dataset.csv.
    Raises FileNotFoundError if the file does not exist.
    """
    input_path = Path("data/raw/barrier_dataset.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {input_path}. Ensure T004b has completed.")
    
    logger.info(f"Loading raw dataset from {input_path}")
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from raw dataset")
    return data

def load_confounds(logger: logging.Logger) -> Dict[str, Dict[str, Any]]:
    """
    Load confounds data from data/confounds.csv to map molecule_id to properties.
    Returns a dict: {molecule_id: {mw, atom_count, functional_groups}}
    """
    confounds_path = Path("data/confounds.csv")
    if not confounds_path.exists():
        # Confounds are optional for this specific task logic (stratification is by barrier)
        # but we log if missing.
        logger.warning(f"Confounds file not found at {confounds_path}. Skipping confounds lookup.")
        return {}
    
    confounds_map = {}
    with open(confounds_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure numeric conversion if needed for later use, though not strictly used for stratification here
            confounds_map[row['molecule_id']] = {
                'mw': float(row['mw']),
                'atom_count': int(row['atom_count']),
                'functional_groups': row['functional_groups']
            }
    return confounds_map

def get_valid_geometry_indices(logger: logging.Logger, raw_data: List[Dict[str, Any]]) -> List[int]:
    """
    Filter the raw data to only include molecules that have an optimized geometry file.
    Returns a list of indices into raw_data that correspond to valid geometries.
    """
    valid_indices = []
    geometry_dir = Path("data/optimized_geometries")
    
    if not geometry_dir.exists():
        logger.warning(f"Optimized geometries directory not found at {geometry_dir}. No geometries available.")
        return []

    for idx, row in enumerate(raw_data):
        molecule_id = row.get('molecule_id', row.get('SMILES', f"mol_{idx}"))
        geom_file = geometry_dir / f"{molecule_id}.xyz"
        if geom_file.exists():
            valid_indices.append(idx)
        else:
            logger.debug(f"Geometry missing for {molecule_id}, skipping.")
    
    logger.info(f"Found {len(valid_indices)} valid geometries out of {len(raw_data)} total molecules.")
    return valid_indices

def stratified_subset_selection(
    raw_data: List[Dict[str, Any]], 
    valid_indices: List[int], 
    logger: logging.Logger
) -> List[int]:
    """
    Select a stratified subset of up to 50 molecules based on experimental_barrier.
    Logic:
    1. Filter to valid_indices.
    2. If count < 50, proceed with all valid.
    3. If count >= 50, use pd.qcut to stratify by 'experimental_barrier' and select 50.
    4. Log warning if proceeding with < 50.
    """
    if not valid_indices:
        logger.warning("No valid geometries found. Returning empty subset.")
        return []

    subset_candidates = [raw_data[i] for i in valid_indices]
    total_valid = len(subset_candidates)
    target_size = 50

    if total_valid < target_size:
        logger.warning(f"Insufficient optimized geometries for full subset (N < 50), proceeding with {total_valid} samples")
        return valid_indices

    # We need pandas for qcut
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for stratified selection. Install with 'pip install pandas'.")
        sys.exit(1)

    # Create a DataFrame for the candidates to facilitate stratification
    df_candidates = pd.DataFrame(subset_candidates)
    
    # Ensure experimental_barrier is numeric
    if 'experimental_barrier' not in df_candidates.columns:
        raise ValueError("Column 'experimental_barrier' not found in raw dataset.")
    
    df_candidates['experimental_barrier'] = pd.to_numeric(df_candidates['experimental_barrier'], errors='coerce')
    df_candidates = df_candidates.dropna(subset=['experimental_barrier'])
    
    # Re-map valid_indices based on the dropped rows (if any NaN in barrier)
    # We need to track which original indices correspond to the valid rows in df_candidates
    valid_indices_filtered = []
    for i, idx in enumerate(valid_indices):
        if pd.notna(raw_data[idx].get('experimental_barrier')):
            valid_indices_filtered.append(idx)
    
    # If filtering removed too many, adjust
    if len(valid_indices_filtered) < target_size:
         logger.warning(f"After filtering NaN barriers, count is {len(valid_indices_filtered)} < 50. Proceeding.")
         return valid_indices_filtered

    # Create a series of indices to sample from
    sample_indices = pd.Series(range(len(valid_indices_filtered)), index=valid_indices_filtered)
    barriers = pd.Series([raw_data[i]['experimental_barrier'] for i in valid_indices_filtered])
    
    # Use qcut to create bins. If unique values < 2, fallback to simple random sample
    try:
        # Ensure at least 2 bins if possible, otherwise use 1
        n_bins = min(10, len(barriers.unique()))
        if n_bins < 2:
            # If not enough variance, just take first 50
            selected_indices = sample_indices.head(target_size).tolist()
        else:
            # Create bins
            bins = pd.qcut(barriers, q=n_bins, duplicates='drop')
            # Stratified sampling: take proportional samples from each bin to reach total 50
            # Simplified: take equal number from each bin if possible, or proportional
            counts = bins.value_counts()
            target_per_bin = target_size // len(counts)
            remainder = target_size % len(counts)
            
            selected_indices = []
            bin_list = bins.tolist()
            current_idx = 0
            
            # Strategy: iterate through bins, take target_per_bin + (1 if remainder > 0)
            for bin_val in counts.index:
                bin_mask = bins == bin_val
                bin_indices = sample_indices[bin_mask].tolist()
                take_count = target_per_bin + (1 if remainder > 0 else 0)
                if remainder > 0:
                    remainder -= 1
                
                # Take up to take_count from this bin
                selected_indices.extend(bin_indices[:take_count])
    except ValueError:
        # Fallback if qcut fails (e.g., too few unique values)
        logger.warning("qcut failed (likely low variance in barriers). Using random sample.")
        selected_indices = sample_indices.sample(n=target_size, random_state=42).tolist()

    logger.info(f"Selected {len(selected_indices)} molecules for DFT subset via stratification.")
    return selected_indices

def write_subset_indices(indices: List[int], logger: logging.Logger):
    """Write the selected indices to state/splits.json for T021."""
    output_dir = Path("state")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "splits.json"
    
    data = {
        "train_indices": indices, # For T020a, the subset IS the training set for DFT baseline
        "test_indices": [],       # T021 will handle the train/test split logic using these indices
        "random_state": 42,
        "subset_size": len(indices)
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Wrote subset indices to {output_path}")

def main():
    """Main entry point for T020a: Subset selection logic."""
    logger = log_setup()
    logger.info("Starting T020a: Subset selection logic")

    try:
        # 1. Load raw dataset
        raw_data = load_raw_dataset(logger)
        
        # 2. Load confounds (optional for this logic but good practice)
        load_confounds(logger)
        
        # 3. Filter to valid geometries
        valid_indices = get_valid_geometry_indices(logger, raw_data)
        
        # 4. Select stratified subset
        selected_indices = stratified_subset_selection(raw_data, valid_indices, logger)
        
        # 5. Write output
        write_subset_indices(selected_indices, logger)
        
        logger.info("T020a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()