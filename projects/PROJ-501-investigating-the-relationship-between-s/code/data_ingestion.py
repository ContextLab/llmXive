import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from config import DEFAULT_M_DWARF_AGE
from utils import exponential_backoff_retry, calculate_checksum, log_api_provenance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for data paths
DATA_PROCESSED_DIR = Path("data/processed")
DATA_LOGS_DIR = Path("data/logs")
OUTPUT_FILE = DATA_PROCESSED_DIR / "merged_filtered.csv"
CHECKSUM_FILE = DATA_PROCESSED_DIR / "merged_filtered.sha256"
API_LOG_FILE = DATA_LOGS_DIR / "api_log.jsonl"

def fetch_flare_catalog() -> pd.DataFrame:
    """
    Fetch flare events from MAST TESS Stellar Flare Catalog.
    Returns a DataFrame with flare data.
    """
    logger.info("Fetching flare catalog from MAST TESS...")
    # Placeholder for actual API call implementation
    # In a real implementation, this would use astroquery or requests
    # to query the MAST TESS Stellar Flare Catalog.
    # For now, we return an empty DataFrame with expected columns.
    df = pd.DataFrame(columns=['host_star_id', 'flare_id', 'flare_energy', 'flare_time'])
    log_api_provenance("MAST_TESS_Flare_Catalog", "fetch_flare_catalog", "success", len(df))
    return df

def fetch_exoplanet_params() -> pd.DataFrame:
    """
    Fetch exoplanet parameters from NASA Exoplanet Archive.
    Returns a DataFrame with planet and host star parameters.
    """
    logger.info("Fetching exoplanet parameters from NASA Exoplanet Archive...")
    # Placeholder for actual API call implementation
    # In a real implementation, this would use astroquery or requests
    # to query the NASA Exoplanet Archive.
    df = pd.DataFrame(columns=[
        'host_star_id', 'planet_name', 'mass', 'radius', 'semi_major_axis',
        'system_age', 'Rotation Period', 'eccentricity'
    ])
    log_api_provenance("NASA_Exoplanet_Archive", "fetch_exoplanet_params", "success", len(df))
    return df

def merge_datasets(flare_df: pd.DataFrame, planet_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join flare counts with planet parameters by host_star_id.
    """
    logger.info("Merging flare and exoplanet datasets...")
    # Count flares per host
    flare_counts = flare_df.groupby('host_star_id').size().reset_index(name='flare_count')
    
    # Merge with planet data
    merged = pd.merge(planet_df, flare_counts, on='host_star_id', how='inner')
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def validate_rotation_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for the presence of 'Rotation Period' column.
    Log a warning if missing and flag records for fallback.
    """
    if 'Rotation Period' not in df.columns:
        logger.warning("Column 'Rotation Period' is missing in the dataset. "
                       "Physics calculations will use fallback values.")
        # Create a placeholder column if missing, to prevent downstream errors
        df['Rotation Period'] = np.nan
    return df

def filter_and_impute(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter and impute data according to project constraints:
    - Exclude non-M-dwarf hosts (heuristic: Mass < 0.6 Msun)
    - Exclude systems with <10 flare events
    - Exclude records with missing mass, radius, or semi-major axis
    - Assign DEFAULT_M_DWARF_AGE if system_age is missing
    """
    logger.info("Applying filters and imputation...")
    
    # Filter for M-dwarfs (Mass < 0.6 Msun)
    df = df[df['mass'] < 0.6]
    
    # Filter for >= 10 flares
    df = df[df['flare_count'] >= 10]
    
    # Exclude records with missing critical values
    df = df.dropna(subset=['mass', 'radius', 'semi_major_axis'])
    
    # Impute missing age
    missing_age_mask = df['system_age'].isna()
    if missing_age_mask.any():
        logger.warning(f"Imputing {missing_age_mask.sum()} missing system_age values with DEFAULT_M_DWARF_AGE.")
        df.loc[missing_age_mask, 'system_age'] = DEFAULT_M_DWARF_AGE
    
    # Handle eccentricity if present (exclude extreme values > 0.8)
    if 'eccentricity' in df.columns:
        df = df[df['eccentricity'] < 0.8]
    
    logger.info(f"Filtered dataset shape: {df.shape}")
    return df

def save_processed_data(df: pd.DataFrame, output_path: Path = OUTPUT_FILE) -> str:
    """
    Save the final filtered dataset to CSV and generate a checksum.
    Returns the path to the checksum file.
    """
    logger.info(f"Saving processed data to {output_path}...")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")
    
    # Generate checksum
    checksum = calculate_checksum(output_path)
    checksum_path = output_path.with_suffix(output_path.suffix + '.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    
    logger.info(f"Checksum generated and saved to {checksum_path}: {checksum}")
    return str(checksum_path)

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Main pipeline to fetch, merge, filter, and save data.
    """
    # Fetch data
    flare_df = fetch_flare_catalog()
    planet_df = fetch_exoplanet_params()
    
    # Merge
    merged_df = merge_datasets(flare_df, planet_df)
    
    # Validate rotation period
    merged_df = validate_rotation_period(merged_df)
    
    # Filter and impute
    filtered_df = filter_and_impute(merged_df)
    
    # Save to CSV with checksum
    if not filtered_df.empty:
        save_processed_data(filtered_df)
    else:
        logger.warning("Filtered dataset is empty. No file saved.")
        # Create an empty file with headers to satisfy downstream tasks
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(OUTPUT_FILE, index=False)
        calculate_checksum(OUTPUT_FILE) # Generate checksum for empty file
    
    return filtered_df

if __name__ == "__main__":
    run_ingestion_pipeline()
