import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np

# Import project utilities using the exact API surface provided
from utils.config import get_processed_dir, get_raw_data_dir
from utils.provenance import generate_provenance_record, save_provenance_record

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(get_processed_dir()) / 'aggregate.log')
    ]
)
logger = logging.getLogger(__name__)


def load_merged_observations() -> pd.DataFrame:
    """
    Load the merged observations CSV from the processed directory.
    Expects 'merged_observations.csv' created by T013.
    """
    input_path = Path(get_processed_dir()) / 'merged_observations.csv'
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T013 (merge_and_buffer.py) has been run successfully."
        )
    
    logger.info(f"Loading merged observations from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate expected columns exist
    required_cols = ['species_id', 'foraging_guild', 'land_cover_proportions']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def parse_land_cover_proportions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the 'land_cover_proportions' column which is stored as a stringified list or JSON.
    Converts it into separate columns for each land cover type.
    """
    logger.info("Parsing land cover proportions...")
    
    # Handle case where column might be a string representation of a list/dict
    # or already a list of dicts if read with specific engine
    def safe_parse(val):
        if isinstance(val, dict):
            return val
        if isinstance(val, list):
            # If it's a list of values, we need to know the order. 
            # Assuming T013 stored it as a dict string or list of dicts.
            # If it's a raw string like "[0.1, 0.2...]", we can't infer keys.
            # Assuming T013 output a JSON string or dict.
            try:
                import json
                return json.loads(val) if isinstance(val, str) else val
            except:
                return {}
        if isinstance(val, str):
            try:
                import json
                return json.loads(val)
            except:
                # Fallback for malformed strings
                return {}
        return {}

    parsed_records = []
    for idx, row in df.iterrows():
        props = safe_parse(row['land_cover_proportions'])
        row_dict = row.to_dict()
        # Flatten the proportions into the row
        for lc_key, lc_val in props.items():
            row_dict[f'lc_{lc_key}'] = lc_val
        parsed_records.append(row_dict)
    
    parsed_df = pd.DataFrame(parsed_records)
    
    # Identify new land cover columns
    lc_cols = [c for c in parsed_df.columns if c.startswith('lc_')]
    if not lc_cols:
        logger.warning("No land cover columns found after parsing. Check input format.")
    
    return parsed_df, lc_cols


def aggregate_species_profiles(df: pd.DataFrame, lc_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate observations to the species level.
    Calculates mean land cover proportions per species and drops rows with missing data.
    
    Returns:
        Tuple of (aggregated_df, drop_log) where drop_log contains counts and reasons.
    """
    logger.info(f"Aggregating {len(df)} observations to species level...")
    
    # Group by species_id and foraging_guild (should be constant per species_id in this context)
    # We assume foraging_guild is constant for a species_id based on T008a logic
    group_cols = ['species_id', 'foraging_guild']
    
    # Check for missing values in land cover columns
    initial_count = len(df)
    missing_mask = df[lc_cols].isnull().any(axis=1)
    missing_count = missing_mask.sum()
    
    drop_reasons = []
    if missing_count > 0:
        reason = f"{missing_count} observations dropped due to missing land cover data in one or more categories."
        drop_reasons.append(reason)
        logger.warning(reason)
        df = df[~missing_mask]
    
    # Check for empty rows (NaN in any LC column)
    # Also check for rows where all LC values are 0 or sum to 0 (invalid proportion)
    invalid_sum_mask = df[lc_cols].sum(axis=1) == 0
    invalid_sum_count = invalid_sum_mask.sum()
    if invalid_sum_count > 0:
        reason = f"{invalid_sum_count} observations dropped due to zero-sum land cover proportions."
        drop_reasons.append(reason)
        logger.warning(reason)
        df = df[~invalid_sum_mask]
    
    # Perform aggregation
    # Mean for proportions
    agg_dict = {col: 'mean' for col in lc_cols}
    # Count observations per species
    agg_dict['observation_count'] = 'count'
    
    # Group by species_id (guild is redundant if 1:1, but keep for schema)
    aggregated = df.groupby(group_cols).agg(agg_dict).reset_index()
    
    # Round proportions for cleanliness
    for col in lc_cols:
        aggregated[col] = aggregated[col].round(4)
    
    final_count = len(aggregated)
    total_dropped = initial_count - final_count
    
    log_entry = {
        "initial_observations": initial_count,
        "final_species_profiles": final_count,
        "observations_dropped": total_dropped,
        "reasons": drop_reasons
    }
    
    logger.info(f"Aggregation complete. Dropped {total_dropped} observations. Final species profiles: {final_count}")
    return aggregated, log_entry


def save_species_profiles(df: pd.DataFrame, log_entry: Dict[str, Any]) -> str:
    """
    Save the aggregated species profiles to CSV and log the drop reasons.
    """
    output_path = Path(get_processed_dir()) / 'species_profiles.csv'
    log_path = Path(get_processed_dir()) / 'aggregate_dropped_log.json'
    
    logger.info(f"Saving species profiles to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saving drop log to {log_path}")
    with open(log_path, 'w') as f:
        import json
        json.dump(log_entry, f, indent=2)
    
    # Record provenance
    provenance = generate_provenance_record(
        step="T016_aggregate",
        input_file="merged_observations.csv",
        output_file="species_profiles.csv",
        metrics=log_entry
    )
    save_provenance_record(provenance, Path(get_processed_dir()) / 'provenance_T016.json')
    
    return str(output_path)


def main():
    """
    Main entry point for the aggregation step.
    """
    logger.info("Starting T016: Aggregate Species Profiles")
    
    try:
        # 1. Load merged data
        merged_df = load_merged_observations()
        
        # 2. Parse land cover proportions
        parsed_df, lc_cols = parse_land_cover_proportions(merged_df)
        
        if not lc_cols:
            raise ValueError("Could not identify land cover columns. Input data format may be incorrect.")
        
        # 3. Aggregate to species level
        profiles_df, drop_log = aggregate_species_profiles(parsed_df, lc_cols)
        
        if profiles_df.empty:
            raise ValueError("Aggregation resulted in an empty DataFrame. No valid species profiles found.")
        
        # 4. Save results
        output_path = save_species_profiles(profiles_df, drop_log)
        
        logger.info(f"T016 completed successfully. Output: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during aggregation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
