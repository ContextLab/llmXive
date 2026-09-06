import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Import path utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_processed_dir, get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_observations(input_path: str) -> pd.DataFrame:
    """
    Load the merged observations CSV from T039.
    
    Args:
        input_path: Path to merged_observations.csv
        
    Returns:
        DataFrame with merged observation data
    """
    logger.info(f"Loading merged observations from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} observations with columns: {list(df.columns)}")
    return df

def parse_land_cover_proportions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse land cover proportion columns from the merged DataFrame.
    
    Expected columns: forest_prop_100m, grassland_prop_100m, 
    wetland_prop_100m, urban_prop_100m, other_prop_100m
    
    Args:
        df: DataFrame with merged observations
        
    Returns:
        DataFrame with parsed land cover columns
    """
    expected_cols = [
        'forest_prop_100m', 'grassland_prop_100m', 
        'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m'
    ]
    
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected land cover columns: {missing_cols}")
    
    # Ensure numeric types, coercing errors to NaN
    for col in expected_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def aggregate_species_profiles(
    df: pd.DataFrame,
    min_obs: int = 50
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Aggregate observations into species-level profiles.
    
    Calculates mean land cover proportions per species and counts
    observations. Logs dropped observations due to missing data.
    
    Args:
        df: DataFrame with parsed land cover proportions
        min_obs: Minimum observations required per species
        
    Returns:
        Tuple of (aggregated profiles DataFrame, list of drop logs)
    """
    logger.info(f"Aggregating species profiles with min_obs={min_obs}")
    
    # Identify land cover columns
    lc_cols = [
        'forest_prop_100m', 'grassland_prop_100m', 
        'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m'
    ]
    
    # Track dropped observations
    drop_logs = []
    
    # Check for missing land cover data
    missing_mask = df[lc_cols].isna().any(axis=1)
    if missing_mask.any():
        missing_count = missing_mask.sum()
        logger.warning(f"Found {missing_count} observations with missing land cover data")
        
        # Log details for dropped rows
        for idx in df[missing_mask].index:
            row = df.loc[idx]
            missing_cols = [col for col in lc_cols if pd.isna(row[col])]
            drop_logs.append({
                'row_index': int(idx),
                'reason_code': 'invalid_value',
                'details': f"Missing values in columns: {missing_cols}"
            })
        
        # Filter out rows with missing data
        df_clean = df.dropna(subset=lc_cols)
        logger.info(f"Filtered to {len(df_clean)} valid observations")
    else:
        df_clean = df.copy()
    
    # Check for out-of-bounds proportions (should be 0-1)
    out_of_bounds_mask = (
        (df_clean[lc_cols] < 0).any(axis=1) | 
        (df_clean[lc_cols] > 1).any(axis=1)
    )
    if out_of_bounds_mask.any():
        oob_count = out_of_bounds_mask.sum()
        logger.warning(f"Found {oob_count} observations with out-of-bounds proportions")
        
        for idx in df_clean[out_of_bounds_mask].index:
            row = df_clean.loc[idx]
            oob_cols = [col for col in lc_cols if row[col] < 0 or row[col] > 1]
            drop_logs.append({
                'row_index': int(idx),
                'reason_code': 'out_of_bounds',
                'details': f"Invalid proportions in columns: {oob_cols}"
            })
        
        df_clean = df_clean[~out_of_bounds_mask]
        logger.info(f"Filtered to {len(df_clean)} valid observations after OOB check")
    
    # Group by species and guild
    profile_cols = ['species_id', 'foraging_guild']
    agg_dict = {col: 'mean' for col in lc_cols}
    agg_dict['observation_count'] = 'size'
    
    profiles = df_clean.groupby(profile_cols, as_index=False).agg(agg_dict)
    
    # Filter species with insufficient observations
    valid_species = profiles[profiles['observation_count'] >= min_obs]
    dropped_species = profiles[profiles['observation_count'] < min_obs]
    
    if not dropped_species.empty:
        logger.warning(f"Excluded {len(dropped_species)} species with < {min_obs} observations")
        for _, row in dropped_species.iterrows():
            drop_logs.append({
                'species_id': row['species_id'],
                'reason_code': 'insufficient_observations',
                'details': f"Only {int(row['observation_count'])} observations (min: {min_obs})"
            })
    
    final_profiles = valid_species.copy()
    logger.info(f"Final species profiles: {len(final_profiles)} species")
    
    return final_profiles, drop_logs

def save_species_profiles(
    profiles: pd.DataFrame,
    output_path: str,
    drop_logs: List[Dict[str, Any]]
) -> None:
    """
    Save species profiles and drop logs to disk.
    
    Args:
        profiles: Aggregated species profiles DataFrame
        output_path: Path for species_profiles.csv
        drop_logs: List of dictionaries describing dropped observations
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save profiles
    profiles.to_csv(output_path, index=False)
    logger.info(f"Saved species profiles to {output_path}")
    
    # Save drop logs
    log_path = str(output_path).replace('.csv', '_drop_log.json')
    with open(log_path, 'w') as f:
        json.dump(drop_logs, f, indent=2)
    logger.info(f"Saved drop log to {log_path}")

def main():
    """Main entry point for the aggregation pipeline."""
    logger.info("Starting species aggregation pipeline (T040)")
    
    # Define paths
    project_root = get_project_root()
    input_path = str(project_root / "data" / "processed" / "merged_observations.csv")
    output_path = str(project_root / "data" / "processed" / "species_profiles.csv")
    
    try:
        # Load data
        df = load_merged_observations(input_path)
        
        # Parse land cover columns
        df = parse_land_cover_proportions(df)
        
        # Aggregate profiles
        profiles, drop_logs = aggregate_species_profiles(df)
        
        # Save results
        save_species_profiles(profiles, output_path, drop_logs)
        
        # Summary
        logger.info("Aggregation complete")
        logger.info(f"Output: {output_path}")
        logger.info(f"Dropped observations logged: {len(drop_logs)} entries")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
