import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd

# Import from utils.config to get project paths
from utils.config import get_project_root, get_processed_dir, get_raw_data_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_observations(file_path: str) -> pd.DataFrame:
    """
    Load the merged observations CSV file.
    
    Args:
        file_path: Path to the merged observations CSV.
        
    Returns:
        DataFrame with merged observations.
    """
    logger.info(f"Loading merged observations from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} observations")
    return df

def parse_land_cover_proportions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure land cover proportion columns are numeric and handle missing values.
    
    Args:
        df: DataFrame with land cover proportion columns.
        
    Returns:
        DataFrame with cleaned land cover proportions.
    """
    # Identify land cover proportion columns (columns ending with '_prop')
    prop_cols = [col for col in df.columns if col.endswith('_prop')]
    
    if not prop_cols:
        logger.warning("No land cover proportion columns found (columns ending with '_prop').")
        return df
    
    logger.info(f"Found {len(prop_cols)} land cover proportion columns: {prop_cols}")
    
    # Convert to numeric, coercing errors to NaN
    for col in prop_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def aggregate_species_profiles(
    df: pd.DataFrame,
    output_log_path: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate observations to species-level profiles.
    
    This function:
    1. Identifies observations with valid land cover data.
    2. Aggregates valid observations by species_id and foraging_guild.
    3. Calculates mean land cover proportions and observation counts.
    4. Logs dropped observations with specific reason codes.
    
    Args:
        df: DataFrame with merged observations.
        output_log_path: Path to write the drop log JSON.
        
    Returns:
        Tuple of (aggregated DataFrame, drop statistics dict).
    """
    # Identify land cover proportion columns
    prop_cols = [col for col in df.columns if col.endswith('_prop')]
    
    if not prop_cols:
        raise ValueError("No land cover proportion columns found to aggregate.")
    
    # Create a mask for valid land cover data (no NaN in any prop column)
    valid_mask = df[prop_cols].notna().all(axis=1)
    
    # Identify dropped rows
    dropped_mask = ~valid_mask
    dropped_df = df[dropped_mask]
    
    # Log dropped observations with reasons
    drop_log = []
    for idx, row in dropped_df.iterrows():
        # Determine specific reason (simplified check for this task)
        # In a full implementation, we'd check specific tile existence or bounds
        reason_code = 'missing_value'
        details = f"Missing land cover data for observation {row.get('observation_id', idx)}"
        
        drop_log.append({
            'observation_id': row.get('observation_id', idx),
            'species_id': row.get('species_id', 'unknown'),
            'reason_code': reason_code,
            'details': details
        })
    
    # Write drop log
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, 'w') as f:
        json.dump(drop_log, f, indent=2)
    
    logger.info(f"Dropped {len(drop_log)} observations due to missing land cover data.")
    logger.info(f"Drop log written to {output_log_path}")
    
    # Filter to valid observations
    valid_df = df[valid_mask].copy()
    
    if valid_df.empty:
        logger.error("No valid observations remaining after filtering.")
        # Create empty profile with correct schema
        profile_cols = ['species_id', 'foraging_guild', 'observation_count'] + prop_cols
        empty_profile = pd.DataFrame(columns=profile_cols)
        return empty_profile, {'dropped_count': len(dropped_df), 'valid_count': 0}
    
    # Aggregate by species_id and foraging_guild
    agg_dict = {col: 'mean' for col in prop_cols}
    agg_dict['observation_id'] = 'count'  # Count observations
    
    # Rename the count column for clarity
    aggregated = valid_df.groupby(['species_id', 'foraging_guild']).agg(
        observation_count=('observation_id', 'count'),
        **agg_dict
    ).reset_index()
    
    # Rename the count column to match expected schema if needed
    # (Already named observation_count via agg_dict)
    
    logger.info(f"Aggregated {len(valid_df)} observations into {len(aggregated)} species profiles.")
    
    stats = {
        'dropped_count': len(dropped_df),
        'valid_count': len(valid_df),
        'profile_count': len(aggregated)
    }
    
    return aggregated, stats

def save_species_profiles(
    df: pd.DataFrame,
    output_path: str,
    stats: Dict[str, Any]
) -> None:
    """
    Save the species profiles to CSV and log statistics.
    
    Args:
        df: Aggregated species profiles DataFrame.
        output_path: Path to save the CSV.
        stats: Statistics about the aggregation process.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved species profiles to {output_path}")
    
    # Save aggregation stats
    stats_path = output_path.replace('.csv', '_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved aggregation statistics to {stats_path}")

def main():
    """
    Main entry point for the aggregation pipeline step.
    """
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    
    input_file = processed_dir / "merged_observations.csv"
    output_file = processed_dir / "species_profiles.csv"
    drop_log_file = processed_dir / "aggregation_drop_log.json"
    
    logger.info(f"Starting aggregation pipeline step.")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    try:
        # Load merged observations
        df = load_merged_observations(str(input_file))
        
        # Parse and clean land cover proportions
        df = parse_land_cover_proportions(df)
        
        # Aggregate to species profiles
        profiles, stats = aggregate_species_profiles(df, str(drop_log_file))
        
        # Save results
        save_species_profiles(profiles, str(output_file), stats)
        
        logger.info("Aggregation step completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
