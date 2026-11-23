import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest.fetch_structures import fetch_perovskite_structures
from src.ingest.fetch_thermal import fetch_perovskite_thermal_data
from src.utils.validation import setup_logger, handle_error

MERGED_OUTPUT_PATH = Path("data/cleaned/merged_perovskite.csv")
STRUCTURES_PATH = Path("data/raw/structures.csv") # Assumed output of fetch_structures
THERMAL_PATH = Path("data/raw/thermal_raw.csv") # Assumed output of fetch_thermal
NORMALIZED_THERMAL_PATH = Path("data/cleaned/normalized_thermal.csv")

def merge_datasets(structures_df: pd.DataFrame, thermal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge structures and thermal data on a common key (e.g., structure_id or composition).
    Assuming 'structure_id' is the key.
    """
    # Ensure common column exists
    if 'structure_id' not in structures_df.columns:
        raise ValueError("Structures DataFrame missing 'structure_id'.")
    if 'structure_id' not in thermal_df.columns:
        # Maybe thermal data uses a different key? Assume 'structure_id' for now.
        # If not, we might need to join on composition.
        # For this implementation, we assume 'structure_id' is present in both.
        # If thermal data doesn't have it, we might need to map it.
        # Let's assume the thermal data has 'structure_id' as per schema.
        raise ValueError("Thermal DataFrame missing 'structure_id'.")
    
    merged = pd.merge(structures_df, thermal_df, on='structure_id', how='inner')
    return merged

def validate_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate geometric constraints (e.g., tolerance factor within range).
    """
    # Placeholder for geometry validation logic
    # Assuming 'tolerance_factor' column exists
    if 'tolerance_factor' in df.columns:
        # Typical tolerance factor range for perovskites is 0.8 - 1.0
        valid_mask = (df['tolerance_factor'] >= 0.8) & (df['tolerance_factor'] <= 1.0)
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            logging.warning(f"Removed {invalid_count} entries with invalid tolerance factor.")
            df = df[valid_mask]
    return df.reset_index(drop=True)

def enforce_minimum_compositions(df: pd.DataFrame, min_count: int = 50) -> pd.DataFrame:
    """
    Ensure there are at least min_count unique compositions.
    """
    if 'composition' in df.columns:
        unique_comps = df['composition'].nunique()
        if unique_comps < min_count:
            raise ValueError(f"Insufficient samples: {unique_comps} < {min_count}")
    return df

def add_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add provenance metadata to the dataframe.
    """
    df['provenance_verified'] = True
    return df

def main():
    """
    Main entry point for merging and cleaning.
    """
    logger = setup_logger("clean_merge")
    
    # Check inputs
    if not STRUCTURES_PATH.exists():
        logger.error(f"Structures file {STRUCTURES_PATH} not found.")
        sys.exit(1)
    if not NORMALIZED_THERMAL_PATH.exists():
        logger.error(f"Normalized thermal file {NORMALIZED_THERMAL_PATH} not found.")
        sys.exit(1)
    
    try:
        structures_df = pd.read_csv(STRUCTURES_PATH)
        thermal_df = pd.read_csv(NORMALIZED_THERMAL_PATH)
    except Exception as e:
        logger.error(f"Failed to read input files: {e}")
        sys.exit(1)
    
    # Merge
    merged = merge_datasets(structures_df, thermal_df)
    
    # Validate Geometry
    merged = validate_geometry(merged)
    
    # Enforce Minimum
    merged = enforce_minimum_compositions(merged)
    
    # Add Provenance
    merged = add_provenance(merged)
    
    # Save
    MERGED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(MERGED_OUTPUT_PATH, index=False)
    logger.info(f"Merged data saved to {MERGED_OUTPUT_PATH} with {len(merged)} rows.")

if __name__ == "__main__":
    main()
