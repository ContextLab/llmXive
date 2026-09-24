"""
Aggregate merged observations into species-level profiles.

This script collapses the `merged_observations.csv` file by averaging
land-cover proportions for each species, producing `species_profiles.csv`.
It logs any dropped rows due to missing data or invalid values.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from utils.config import get_processed_dir, get_data_dir, get_seed, get_file_path
from utils.provenance import generate_provenance_record, save_provenance_record

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_file_path('data', 'logs', 'aggregate.log'))
    ]
)
logger = logging.getLogger(__name__)

def load_merged_observations() -> pd.DataFrame:
    """
    Load the merged observations CSV file.
    
    Returns:
        pd.DataFrame: The merged observations dataframe.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    input_path = get_file_path('data', 'processed', 'merged_observations.csv')
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        logger.error("Input file is empty.")
        raise ValueError("Input file is empty.")
    
    required_columns = ['species_id', 'foraging_guild', 
                        'forest_prop_100m', 'grassland_prop_100m', 
                        'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m']
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} merged observations from {input_path}")
    return df

def parse_land_cover_proportions(df: pd.DataFrame) -> List[str]:
    """
    Identify land cover proportion columns from the dataframe.
    
    Args:
        df: The input dataframe.
        
    Returns:
        List[str]: Column names corresponding to land cover proportions.
    """
    lc_cols = [col for col in df.columns if col.endswith('_prop_100m')]
    logger.info(f"Found land cover proportion columns: {lc_cols}")
    return lc_cols

def aggregate_species_profiles(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Aggregate observations to species-level profiles by averaging land cover proportions.
    
    Args:
        df: The merged observations dataframe.
        
    Returns:
        Tuple containing:
            - pd.DataFrame: The aggregated species profiles.
            - List[Dict]: Log entries for dropped/invalid rows.
    """
    lc_cols = parse_land_cover_proportions(df)
    log_entries = []
    
    # Identify rows with missing or invalid land cover data
    invalid_mask = df[lc_cols].isnull().any(axis=1)
    invalid_count = invalid_mask.sum()
    
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} rows with missing land cover data. Dropping them.")
        log_entries.append({
            "reason_code": "MISSING_LANDCOVER",
            "details": f"Dropped {invalid_count} rows with missing land cover proportions.",
            "count": int(invalid_count)
        })
        df_clean = df[~invalid_mask].copy()
    else:
        df_clean = df.copy()
    
    # Check for negative values (should not happen if data is valid, but good to check)
    negative_mask = (df_clean[lc_cols] < 0).any(axis=1)
    negative_count = negative_mask.sum()
    
    if negative_count > 0:
        logger.warning(f"Found {negative_count} rows with negative land cover proportions. Dropping them.")
        log_entries.append({
            "reason_code": "NEGATIVE_LANDCOVER",
            "details": f"Dropped {negative_count} rows with negative land cover proportions.",
            "count": int(negative_count)
        })
        df_clean = df_clean[~negative_mask].copy()
    
    # Group by species and guild, then aggregate
    # We assume foraging_guild is constant per species_id based on the pipeline design
    # If not, we group by both to be safe, but typically species_id is the key
    if 'foraging_guild' in df_clean.columns:
        # Group by species_id and foraging_guild to handle potential inconsistencies
        # Then take the first guild encountered (or mode) and mean for proportions
        grouped = df_clean.groupby('species_id', as_index=False)
        
        # Aggregate: take the first non-null guild (assuming consistency) and mean for props
        agg_dict = {col: 'mean' for col in lc_cols}
        # For guild, we take the first one (or mode if we want to be stricter)
        # Since species should map to one guild, 'first' is usually fine
        # But to be robust against mixed data if any, let's just take the first
        # A better approach if we expect consistency: verify uniqueness first
        guild_counts = df_clean.groupby('species_id')['foraging_guild'].nunique()
        if (guild_counts > 1).any():
            logger.warning("Some species have multiple guild assignments. Taking the first encountered.")
            log_entries.append({
                "reason_code": "MULTIPLE_GUILDS",
                "details": f"Found { (guild_counts > 1).sum() } species with multiple guild assignments. Taking the first encountered.",
                "count": int((guild_counts > 1).sum())
            })
        
        agg_dict['foraging_guild'] = 'first'
        
        species_profiles = grouped.agg(agg_dict).reset_index(drop=False)
    else:
        # Fallback if guild column is missing (should not happen)
        grouped = df_clean.groupby('species_id', as_index=False)
        agg_dict = {col: 'mean' for col in lc_cols}
        species_profiles = grouped.agg(agg_dict).reset_index(drop=False)
    
    # Ensure counts are recorded
    species_counts = df_clean.groupby('species_id').size().reset_index(name='observation_count')
    species_profiles = species_profiles.merge(species_counts, on='species_id', how='left')
    
    logger.info(f"Aggregated {len(df_clean)} observations into {len(species_profiles)} species profiles.")
    
    return species_profiles, log_entries

def save_species_profiles(df: pd.DataFrame, log_entries: List[Dict[str, Any]]) -> None:
    """
    Save the species profiles to CSV and log any dropped rows.
    
    Args:
        df: The aggregated species profiles dataframe.
        log_entries: List of log entries for dropped/invalid rows.
    """
    output_path = get_file_path('data', 'processed', 'species_profiles.csv')
    log_path = get_file_path('data', 'processed', 'aggregate_log.json')
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved species profiles to {output_path}")
    
    # Save log
    log_entry = {
        "step": "aggregate",
        "timestamp": pd.Timestamp.now().isoformat(),
        "input_file": get_file_path('data', 'processed', 'merged_observations.csv'),
        "output_file": output_path,
        "dropped_rows_log": log_entries,
        "total_input_rows": len(df), # This is actually the count of valid rows used
        "final_profile_count": len(df)
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    logger.info(f"Saved aggregation log to {log_path}")
    
    # Record provenance
    provenance_record = generate_provenance_record(
        step_name="aggregate",
        input_files=[get_file_path('data', 'processed', 'merged_observations.csv')],
        output_files=[output_path, log_path]
    )
    save_provenance_record(provenance_record)

def main() -> None:
    """Main entry point for the aggregation script."""
    logger.info("Starting species profile aggregation...")
    
    try:
        # Load data
        merged_df = load_merged_observations()
        
        # Aggregate
        species_profiles, log_entries = aggregate_species_profiles(merged_df)
        
        # Save results
        save_species_profiles(species_profiles, log_entries)
        
        logger.info("Aggregation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
