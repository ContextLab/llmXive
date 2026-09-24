import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from sklearn.model_selection import train_test_split

# --- Logging Setup ---
def log_setup() -> logging.Logger:
    """Configure the logger for this module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

logger = log_setup()

# --- Helper Functions ---

def load_raw_dataset(filepath: Path) -> pd.DataFrame:
    """
    Load the raw barrier dataset from CSV.
    Expects columns: 'molecule_id', 'SMILES', 'experimental_barrier', etc.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Raw dataset not found at {filepath}. "
                                "Ensure T004c (normalize_data) has completed.")
    logger.info(f"Loading raw dataset from {filepath}")
    df = pd.read_csv(filepath)
    # Ensure molecule_id exists; if not, try to infer or raise
    if 'molecule_id' not in df.columns:
        # Fallback: assume index or SMILES if 'molecule_id' is missing but 'SMILES' exists
        # However, per spec T004c/T013c, molecule_id should be present.
        # We enforce strict schema compliance here.
        raise ValueError("Raw dataset missing required column 'molecule_id'")
    return df

def load_confounds(filepath: Path) -> Optional[pd.DataFrame]:
    """
    Load confounds analysis if available (optional for this task, 
    but good for future expansion).
    """
    if filepath.exists():
        logger.info(f"Loading confounds from {filepath}")
        return pd.read_csv(filepath)
    logger.warning(f"Confounds file not found at {filepath}. Proceeding without it.")
    return None

def get_valid_geometry_indices(geometries_dir: Path) -> List[str]:
    """
    Scan the optimized geometries directory and return a list of molecule IDs
    for which an .xyz file exists.
    """
    if not geometries_dir.exists():
        logger.warning(f"Optimized geometries directory not found: {geometries_dir}")
        return []

    valid_ids = []
    for file_path in geometries_dir.glob("*.xyz"):
        # Filename is {molecule_id}.xyz
        molecule_id = file_path.stem
        valid_ids.append(molecule_id)
    
    logger.info(f"Found {len(valid_ids)} valid optimized geometries.")
    return valid_ids

def stratified_subset_selection(
    df: pd.DataFrame, 
    target_column: str = 'experimental_barrier', 
    sample_size: int = 50,
    random_state: int = 42
) -> List[str]:
    """
    Perform stratified selection on the dataset based on the target column.
    If N >= 50, select 50 samples. Else select all.
    Uses qcut for binning if continuous, or simple split if categorical.
    """
    n_total = len(df)
    logger.info(f"Performing stratified selection on {n_total} samples.")

    if n_total < 50:
        logger.warning(f"Insufficient optimized geometries for full subset (N < 50), "
                       f"proceeding with {n_total} samples; statistical power of t-test is limited")
        return df['molecule_id'].tolist()

    # Determine bins for stratification
    # If target_column is numeric, use qcut to create bins
    if pd.api.types.is_numeric_dtype(df[target_column]):
        # Create 5 bins for stratification to ensure good coverage
        try:
            bins = pd.qcut(df[target_column], q=5, duplicates='drop')
        except ValueError:
            # Fallback if unique values < bins
            bins = df[target_column]
    else:
        bins = df[target_column]

    # Perform train_test_split with stratify, taking only the 'train' portion as our subset
    # We want a subset of size 50. 
    # Strategy: Split the full set into a subset of 50 and the rest.
    # We use train_test_split with train_size=50 and stratify.
    
    # Note: sklearn's train_test_split with train_size=int works for exact count.
    subset, _ = train_test_split(
        df, 
        train_size=sample_size, 
        stratify=bins, 
        random_state=random_state
    )
    
    logger.info(f"Selected {len(subset)} samples via stratification.")
    return subset['molecule_id'].tolist()

def write_subset_indices(molecule_ids: List[str], output_path: Path) -> None:
    """
    Write the list of selected molecule IDs to a JSON file.
    Format: {"molecule_ids": ["id1", "id2", ...]}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"molecule_ids": molecule_ids}
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Subset indices written to {output_path}")

def main() -> int:
    """
    Main entry point for T020a: Subset Selection.
    
    Logic:
    1. Load raw dataset (data/raw/barrier_dataset.csv)
    2. Load list of valid geometry IDs from data/optimized_geometries/
    3. Merge raw dataset with valid IDs to create filtered set
    4. Perform stratification on filtered set
    5. Write selected IDs to state/selected_subset.json
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "barrier_dataset.csv"
    geometries_dir = project_root / "data" / "optimized_geometries"
    output_path = project_root / "state" / "selected_subset.json"

    # Step 1: Load raw dataset
    try:
        df_raw = load_raw_dataset(raw_data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Step 2: Get valid geometry IDs
    valid_ids = get_valid_geometry_indices(geometries_dir)
    if not valid_ids:
        logger.error("No valid optimized geometries found. Cannot proceed with subset selection.")
        return 1

    # Step 3: Filter dataset to only include molecules with valid geometries
    # Ensure we are filtering by 'molecule_id'
    df_filtered = df_raw[df_raw['molecule_id'].isin(valid_ids)].copy()
    
    logger.info(f"Filtered dataset size: {len(df_filtered)} (from {len(df_raw)})")

    if df_filtered.empty:
        logger.error("No molecules in the raw dataset have corresponding optimized geometries.")
        return 1

    # Step 4: Stratified Selection
    selected_ids = stratified_subset_selection(
        df_filtered, 
        target_column='experimental_barrier',
        sample_size=50
    )

    # Step 5: Write output
    write_subset_indices(selected_ids, output_path)

    logger.info("T020a Subset Selection completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
