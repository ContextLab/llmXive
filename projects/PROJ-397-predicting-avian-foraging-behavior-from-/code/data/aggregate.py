"""
Aggregate filtered observations into species-level profiles.

This script loads the merged and filtered dataset from `data/processed/merged_observations.csv`,
groups by species, calculates mean land cover proportions, observation counts, and standard deviations,
and saves the result to `data/processed/species_profiles.csv`.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

# Add project root to path to allow imports from utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.provenance import compute_file_hash, generate_provenance_record, save_provenance_record

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'aggregate.log')
    ]
)
logger = logging.getLogger(__name__)

def load_merged_observations(input_path: Path) -> pd.DataFrame:
    """Load the merged and filtered observations dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading merged observations from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['species_id', 'foraging_guild', 'land_cover_proportions']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records")
    return df

def parse_land_cover_proportions(series: pd.Series) -> pd.DataFrame:
    """
    Parse the 'land_cover_proportions' column which contains JSON strings or dictionaries.
    Returns a DataFrame with one column per land cover class.
    """
    # If the column contains dictionaries, convert directly
    if series.dtype == object:
        # Try to convert strings to dicts if necessary
        try:
            parsed = series.apply(lambda x: x if isinstance(x, dict) else eval(str(x)) if isinstance(x, str) else x)
        except Exception:
            # Fallback: assume it's already a dict or handle gracefully
            parsed = series
    else:
        parsed = series

    # Convert to DataFrame
    lc_df = pd.DataFrame(parsed.tolist(), index=parsed.index)
    
    # Ensure all expected columns exist (fill NaN with 0 if some species lack certain classes)
    all_lc_cols = [col for col in lc_df.columns if col not in ['species_id', 'foraging_guild', 'geometry']]
    lc_df = lc_df.fillna(0)
    
    return lc_df

def aggregate_species_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate observations to species level.
    
    Calculates:
    - Mean land cover proportions
    - Standard deviation of land cover proportions
    - Total observation count
    - Foraging guild (should be constant per species)
    """
    logger.info("Aggregating species profiles...")
    
    # Parse land cover proportions
    lc_df = parse_land_cover_proportions(df['land_cover_proportions'])
    
    # Combine with species_id and foraging_guild
    df_expanded = df[['species_id', 'foraging_guild']].copy()
    df_expanded = pd.concat([df_expanded, lc_df], axis=1)
    
    # Group by species_id
    agg_dict = {}
    numeric_cols = df_expanded.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        agg_dict[col] = ['mean', 'std', 'count']
    
    # For non-numeric columns (like foraging_guild), take the first value
    non_numeric_cols = df_expanded.select_dtypes(exclude=[np.number]).columns
    for col in non_numeric_cols:
        if col != 'species_id':
            agg_dict[col] = 'first'
    
    # Perform aggregation
    grouped = df_expanded.groupby('species_id', as_index=False).agg(agg_dict)
    
    # Flatten column names
    grouped.columns = ['_'.join(col).strip() if col[1] else col[0] for col in grouped.columns]
    
    # Rename count column to observation_count
    grouped = grouped.rename(columns={'count': 'observation_count'})
    
    # Ensure observation_count is integer
    grouped['observation_count'] = grouped['observation_count'].astype(int)
    
    # Filter out the 'std' and 'count' suffixes for land cover columns to keep only mean and std
    # Actually, let's keep both mean and std for analysis
    # Rename for clarity
    final_df = grouped.rename(columns={
        'foraging_guild_first': 'foraging_guild'
    })
    
    # Sort by observation count descending
    final_df = final_df.sort_values('observation_count', ascending=False).reset_index(drop=True)
    
    logger.info(f"Aggregated into {len(final_df)} species profiles")
    return final_df

def save_species_profiles(df: pd.DataFrame, output_path: Path) -> None:
    """Save the aggregated species profiles to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved species profiles to {output_path}")
    
    # Compute and log file hash
    file_hash = compute_file_hash(output_path)
    logger.info(f"Output file hash: {file_hash}")

def main() -> int:
    """Main entry point for the aggregation script."""
    config = get_config()
    
    # Define paths
    input_path = config['paths']['data_processed'] / 'merged_observations.csv'
    output_path = config['paths']['data_processed'] / 'species_profiles.csv'
    
    try:
        # Load data
        df = load_merged_observations(input_path)
        
        # Aggregate
        profiles = aggregate_species_profiles(df)
        
        # Save
        save_species_profiles(profiles, output_path)
        
        # Generate provenance record
        provenance = generate_provenance_record(
            step='aggregate',
            input_files=[str(input_path)],
            output_files=[str(output_path)],
            parameters={'config': config}
        )
        save_provenance_record(provenance, config['paths']['provenance'])
        
        logger.info("Aggregation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
