import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np

# Import from local utils
from utils.config import get_processed_dir, get_project_root, get_code_root
from utils.provenance import compute_file_hash, save_provenance_record, load_metadata_config, save_metadata_config, log_step

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_observations(input_path: str) -> pd.DataFrame:
    """
    Load the merged observations CSV.
    
    Args:
        input_path: Path to merged_observations.csv
        
    Returns:
        DataFrame with merged observations
    """
    logger.info(f"Loading merged observations from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def parse_land_cover_proportions(columns: List[str]) -> List[str]:
    """
    Identify land cover proportion columns from the DataFrame columns.
    Expected pattern: <landcover_type>_prop_100m (e.g., forest_prop_100m)
    
    Args:
        columns: List of column names
        
    Returns:
        List of land cover proportion column names
    """
    lc_cols = [col for col in columns if col.endswith('_prop_100m')]
    logger.info(f"Identified {len(lc_cols)} land cover proportion columns: {lc_cols}")
    return lc_cols

def aggregate_species_profiles(df: pd.DataFrame, log_path: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Collapse merged observations to species-level profiles by averaging land-cover proportions.
    
    Args:
        df: DataFrame with merged observations
        log_path: Path to write the selection log
        
    Returns:
        Tuple of (species_profiles_df, dropped_rows_log)
    """
    logger.info("Aggregating species profiles...")
    
    # Identify required columns
    required_cols = ['species_id', 'foraging_guild']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Identify land cover columns
    lc_cols = parse_land_cover_proportions(list(df.columns))
    if not lc_cols:
        raise ValueError("No land cover proportion columns found. Expected columns ending with '_prop_100m'.")
    
    # Check for missing values in land cover columns
    na_counts = df[lc_cols].isna().sum()
    if na_counts.any():
        logger.warning(f"Found NA values in land cover columns:\n{na_counts[na_counts > 0]}")
        # Drop rows with NA in land cover columns
        initial_count = len(df)
        df = df.dropna(subset=lc_cols)
        dropped_na = initial_count - len(df)
        if dropped_na > 0:
            logger.info(f"Dropped {dropped_na} rows due to NA values in land cover columns.")
    
    # Group by species and guild
    # Note: We assume foraging_guild is consistent per species_id. 
    # If not, we take the first non-null guild per species.
    group_cols = ['species_id']
    
    # Aggregate land cover proportions
    agg_dict = {col: 'mean' for col in lc_cols}
    
    # Handle guild column: take the first non-null value per species
    # We'll aggregate it separately or use a custom function
    def first_valid(x):
        valid_vals = x.dropna()
        return valid_vals.iloc[0] if len(valid_vals) > 0 else None
    
    agg_dict['foraging_guild'] = first_valid
    
    # Perform aggregation
    species_profiles = df.groupby(group_cols, as_index=False).agg(agg_dict)
    
    # Round proportions to 4 decimal places
    for col in lc_cols:
        species_profiles[col] = species_profiles[col].round(4)
    
    # Verify sum of proportions is ~1.0 for each species (allowing for rounding)
    species_profiles['prop_sum'] = species_profiles[lc_cols].sum(axis=1)
    sum_check = species_profiles['prop_sum'].between(0.99, 1.01)
    if not sum_check.all():
        logger.warning(f"Some species profiles have prop_sum outside [0.99, 1.01]: {species_profiles[~sum_check][['species_id', 'prop_sum']]}")
    species_profiles = species_profiles.drop(columns=['prop_sum'])
    
    # Log dropped species (if any were dropped due to NA or other reasons)
    dropped_log = []
    
    # Check for species with only 1 observation (might be statistically weak, but we keep them per task spec)
    # The task says "logging any dropped rows", so we log rows dropped due to NA above
    
    # Write log
    log_entries = []
    if dropped_na > 0:
        log_entries.append({
            "reason_code": "NA_IN_LANDCOVER",
            "details": f"Dropped {dropped_na} observations due to missing land cover proportion data.",
            "count": dropped_na
        })
    
    # Log the aggregation summary
    log_entries.append({
        "reason_code": "AGGREGATION_SUMMARY",
        "details": f"Aggregated {len(df)} observations into {len(species_profiles)} species profiles.",
        "count": len(species_profiles)
    })
    
    # Write log file
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    with open(log_path, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    logger.info(f"Aggregation complete. Wrote {len(species_profiles)} species profiles.")
    logger.info(f"Wrote log to {log_path}")
    
    return species_profiles, log_entries

def save_species_profiles(df: pd.DataFrame, output_path: str) -> str:
    """
    Save species profiles to CSV and record provenance.
    
    Args:
        df: Species profiles DataFrame
        output_path: Path to save the CSV
        
    Returns:
        SHA-256 hash of the output file
    """
    logger.info(f"Saving species profiles to {output_path}")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save CSV
    df.to_csv(output_path, index=False)
    
    # Compute hash
    file_hash = compute_file_hash(output_path)
    logger.info(f"Saved {len(df)} rows. File hash: {file_hash}")
    
    return file_hash

def main():
    """
    Main entry point for the aggregation step.
    """
    # Get paths
    code_root = get_code_root()
    processed_dir = get_processed_dir()
    
    input_path = os.path.join(processed_dir, "merged_observations.csv")
    output_path = os.path.join(processed_dir, "species_profiles.csv")
    log_path = os.path.join(processed_dir, "aggregation_log.json")
    
    # Log start
    log_step("aggregate", "start", {"input": input_path, "output": output_path})
    
    try:
        # Load data
        df = load_merged_observations(input_path)
        
        # Aggregate
        species_profiles, log_entries = aggregate_species_profiles(df, log_path)
        
        # Save
        file_hash = save_species_profiles(species_profiles, output_path)
        
        # Record provenance
        metadata = load_metadata_config()
        record = {
            "step": "aggregate",
            "input_file": input_path,
            "output_file": output_path,
            "output_hash": file_hash,
            "timestamp": log_entries[-1]["details"] if log_entries else "unknown",
            "log_file": log_path
        }
        save_provenance_record(metadata, record)
        save_metadata_config(metadata)
        
        log_step("aggregate", "success", {"output_hash": file_hash, "num_species": len(species_profiles)})
        logger.info("Aggregation step completed successfully.")
        
    except Exception as e:
        log_step("aggregate", "failed", {"error": str(e)})
        logger.error(f"Aggregation step failed: {e}")
        raise

if __name__ == "__main__":
    main()
