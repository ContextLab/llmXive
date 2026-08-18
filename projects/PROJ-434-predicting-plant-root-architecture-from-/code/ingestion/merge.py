import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import logging

# Ensure we can import sibling modules if run as script
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.logging_utils import (
    log_excluded_record,
    log_species_exclusion_summary,
    setup_logging,
    get_logger
)
from utils.exceptions import DataQualityError

def load_soil_data(filepath: str) -> pd.DataFrame:
    """
    Load soil data from a CSV file.
    
    Args:
        filepath: Path to the soil data CSV.
    
    Returns:
        DataFrame with soil data.
    """
    logger = get_logger(__name__)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Soil data file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded soil data: {len(df)} rows from {filepath}")
    return df

def load_trait_data(filepath: str) -> pd.DataFrame:
    """
    Load trait data from a CSV file.
    
    Args:
        filepath: Path to the trait data CSV.
    
    Returns:
        DataFrame with trait data.
    """
    logger = get_logger(__name__)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Trait data file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded trait data: {len(df)} rows from {filepath}")
    return df

def merge_datasets(
    soil_df: pd.DataFrame,
    trait_df: pd.DataFrame,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Merge soil and trait data on coordinates (latitude, longitude).
    
    Args:
        soil_df: DataFrame with soil data.
        trait_df: DataFrame with trait data.
        logger: Optional logger instance.
    
    Returns:
        Merged DataFrame.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    # Determine join keys (assuming common columns exist)
    join_keys = ['latitude', 'longitude']
    
    # Log missing keys if any
    for key in join_keys:
        if key not in soil_df.columns:
            logger.warning(f"Key '{key}' missing in soil data")
        if key not in trait_df.columns:
            logger.warning(f"Key '{key}' missing in trait data")
    
    merged = pd.merge(
        trait_df,
        soil_df,
        on=join_keys,
        how='left',
        suffixes=('', '_soil')
    )
    
    total_rows = len(trait_df)
    merged_rows = len(merged)
    matched = merged_rows - merged['soil_n'].isna().sum() # Approximate match count
    
    logger.info(f"Merged datasets: {total_rows} trait rows -> {merged_rows} total, ~{matched} matched soil data")
    
    return merged

def apply_species_filter(
    df: pd.DataFrame,
    min_observations: int = 10,
    logger: Optional[logging.Logger] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter species with fewer than min_observations valid rows.
    
    Args:
        df: Merged DataFrame.
        min_observations: Minimum number of valid observations required per species.
        logger: Optional logger instance.
    
    Returns:
        Tuple of (filtered DataFrame, list of exclusion reasons).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if 'species_name' not in df.columns:
        raise ValueError("DataFrame must contain 'species_name' column")
    
    # Count valid observations (non-null predictors)
    # Assuming predictors are soil_n, soil_p, soil_k, soil_ph
    predictors = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
    valid_cols = [col for col in predictors if col in df.columns]
    
    if not valid_cols:
        logger.warning("No soil predictor columns found; cannot filter by valid observations")
        return df, []
    
    df['is_valid'] = df[valid_cols].notna().all(axis=1)
    species_counts = df.groupby('species_name')['is_valid'].sum().reset_index()
    species_counts.columns = ['species_name', 'valid_count']
    
    excluded_species = []
    filtered_rows = []
    
    # Log exclusions
    for _, row in species_counts.iterrows():
        species = row['species_name']
        count = row['valid_count']
        
        if count < min_observations:
            reason = f'observation_count < {min_observations}'
            excluded_species.append({
                'species_name': species,
                'observation_count': count,
                'reason': reason
            })
            log_species_exclusion_summary(
                logger,
                species_name=species,
                observation_count=count,
                threshold=min_observations,
                reason=reason
            )
            # Filter out this species from the main dataframe
            filtered_rows.append(species)
    
    if filtered_rows:
        filtered_df = df[~df['species_name'].isin(filtered_rows)].copy()
        logger.info(f"Filtered out {len(filtered_rows)} species. Final rows: {len(filtered_df)}")
    else:
        filtered_df = df.copy()
    
    # Clean up helper column
    if 'is_valid' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['is_valid'])
    
    return filtered_df, excluded_species

def main():
    """
    Main execution flow for merging and filtering.
    """
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "merge_process.log"
    setup_logging(str(log_file))
    logger = get_logger(__name__)
    
    # Paths (adjust based on actual project structure if needed)
    soil_path = "data/raw/soil_data.csv" # Placeholder, should be real path or generated
    trait_path = "data/raw/trait_data.csv" # Placeholder
    
    # Check if files exist, if not, skip or error (real implementation would fetch)
    if not os.path.exists(soil_path) or not os.path.exists(trait_path):
        logger.error("Input data files not found. Ensure T012/T013 have run.")
        return
    
    soil_df = load_soil_data(soil_path)
    trait_df = load_trait_data(trait_path)
    
    merged_df = merge_datasets(soil_df, trait_df, logger)
    
    # Apply species filter
    filtered_df, exclusion_reasons = apply_species_filter(merged_df, min_observations=10, logger=logger)
    
    # Log individual excluded records (missing soil data)
    # Identify rows where soil data is missing
    soil_cols = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
    missing_soil_mask = merged_df[soil_cols].isna().any(axis=1)
    missing_soil_rows = merged_df[missing_soil_mask]
    
    for idx, row in missing_soil_rows.iterrows():
        # Determine specific reason
        missing_fields = [col for col in soil_cols if pd.isna(row.get(col))]
        reason = f"missing soil data: {', '.join(missing_fields)}"
        log_excluded_record(
            logger,
            record_id=str(idx),
            reason=reason,
            details={'lat': row.get('latitude'), 'lon': row.get('longitude')}
        )
    
    logger.info("Merge and filter process completed.")

if __name__ == "__main__":
    main()
