import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from astroquery.mast import Observations
from astroquery.exoplanet_archive import ExoplanetArchive
import requests

from config import DEFAULT_M_DWARF_AGE
from utils import exponential_backoff_retry, log_api_provenance

# Configure logger
logger = logging.getLogger(__name__)

# Constants
LOG_PATH = "data/logs/api_log.jsonl"
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

@exponential_backoff_retry
def fetch_flare_catalog(
    star_ids: Optional[List[str]] = None,
    max_records: int = 1000
) -> pd.DataFrame:
    """
    Fetch flare events from MAST TESS Stellar Flare Catalog.

    Args:
        star_ids: Optional list of specific star IDs to fetch.
        max_records: Maximum number of records to fetch.

    Returns:
        DataFrame containing flare events.
    """
    start_time = time.time()
    params = {"catalog": "TESSStellarFlare", "columns": "all"}
    if star_ids:
        params["target"] = star_ids[0]  # Fetch for first target as example

    try:
        # Using astroquery to query MAST
        table = Observations.query_criteria(**params)
        duration = time.time() - start_time
        
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="flare_fetch",
            source="MAST TESS Stellar Flare Catalog",
            params=params,
            status="success",
            record_count=len(table),
            duration_seconds=duration
        )
        
        return pd.DataFrame(table)
    except Exception as e:
        duration = time.time() - start_time
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="flare_fetch",
            source="MAST TESS Stellar Flare Catalog",
            params=params,
            status="failure",
            error_message=str(e),
            duration_seconds=duration
        )
        raise

@exponential_backoff_retry
def fetch_exoplanet_params(
    star_ids: Optional[List[str]] = None,
    max_records: int = 1000
) -> pd.DataFrame:
    """
    Fetch exoplanet parameters from NASA Exoplanet Archive.

    Args:
        star_ids: Optional list of specific host star IDs.
        max_records: Maximum number of records to fetch.

    Returns:
        DataFrame containing exoplanet parameters.
    """
    start_time = time.time()
    params = {
        "columns": "pl_name,pl_hostname,pl_orbper,pl_radj,pl_massj,pl_discmethod,host_name,host_mass,host_rad,host_age,pl_orbsmax",
        "format": "csv"
    }
    
    try:
        # Using requests to query NASA Exoplanet Archive API
        url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?script=select " + \
              "from pscomp where 1=1"
        
        if star_ids:
            # Filter by host names if provided
            host_filter = " or ".join([f"host_name='{sid}'" for sid in star_ids])
            url += f" and ({host_filter})"
        
        response = requests.get(url, params={"format": "csv"})
        response.raise_for_status()
        
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        duration = time.time() - start_time
        
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="exoplanet_fetch",
            source="NASA Exoplanet Archive",
            params=params,
            status="success",
            record_count=len(df),
            duration_seconds=duration
        )
        
        return df
    except Exception as e:
        duration = time.time() - start_time
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="exoplanet_fetch",
            source="NASA Exoplanet Archive",
            params=params,
            status="failure",
            error_message=str(e),
            duration_seconds=duration
        )
        raise

def merge_datasets(
    flare_df: pd.DataFrame,
    exoplanet_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Join flare counts with planet parameters by host_star_id.

    Args:
        flare_df: DataFrame containing flare events.
        exoplanet_df: DataFrame containing exoplanet parameters.

    Returns:
        Merged DataFrame.
    """
    start_time = time.time()
    
    # Aggregate flare counts by host
    flare_counts = flare_df.groupby('target_name').size().reset_index(name='flare_count')
    flare_counts.columns = ['host_star_id', 'flare_count']
    
    # Rename exoplanet host column to match
    exoplanet_df = exoplanet_df.rename(columns={'host_name': 'host_star_id'})
    
    # Merge datasets
    merged_df = pd.merge(
        exoplanet_df,
        flare_counts,
        on='host_star_id',
        how='inner'
    )
    
    duration = time.time() - start_time
    log_api_provenance(
        log_path=LOG_PATH,
        query_type="merge_datasets",
        source="Internal",
        params={"flare_count": len(flare_counts), "exoplanet_count": len(exoplanet_df)},
        status="success",
        record_count=len(merged_df),
        duration_seconds=duration
    )
    
    return merged_df

def validate_rotation_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explicitly check for the presence of the 'Rotation Period' column.
    If missing, log a warning and flag records for fallback handling.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with 'rotation_period_missing' flag added.
    """
    start_time = time.time()
    
    if 'Rotation Period' not in df.columns:
        logger.warning("Rotation Period column not found in exoplanet dataset. Fallback handling will be used in physics phase.")
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="validation_warning",
            source="Internal",
            params={"column": "Rotation Period", "reason": "Missing in dataset"},
            status="warning",
            error_message="Rotation Period column not found"
        )
        df['rotation_period_missing'] = True
    else:
        df['rotation_period_missing'] = df['Rotation Period'].isna()
        
        # Log summary of missing rotation periods
        missing_count = df['rotation_period_missing'].sum()
        if missing_count > 0:
            log_api_provenance(
                log_path=LOG_PATH,
                query_type="validation_warning",
                source="Internal",
                params={"column": "Rotation Period", "missing_count": int(missing_count)},
                status="warning",
                error_message=f"{missing_count} records missing rotation period"
            )
    
    duration = time.time() - start_time
    log_api_provenance(
        log_path=LOG_PATH,
        query_type="validate_rotation_period",
        source="Internal",
        params={"total_records": len(df)},
        status="success",
        record_count=len(df),
        duration_seconds=duration
    )
    
    return df

def filter_and_impute(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter and impute data according to project requirements.

    - Exclude non-M-dwarf hosts (based on mass/radius criteria)
    - Exclude systems with <10 flare events
    - Exclude records with missing mass, radius, or semi-major axis
    - Assign DEFAULT_M_DWARF_AGE if system_age is missing

    Args:
        df: Input DataFrame.

    Returns:
        Filtered and imputed DataFrame.
    """
    start_time = time.time()
    initial_count = len(df)
    filter_log = []

    # Filter 1: Exclude non-M-dwarfs (Mass < 0.6 Msun and Radius < 0.7 Rsun)
    # Using host_mass and host_rad columns (in solar units)
    m_dwarf_mask = (df['host_mass'] < 0.6) & (df['host_rad'] < 0.7)
    df = df[m_dwarf_mask].copy()
    filter_log.append(f"M-dwarf filter: {initial_count - len(df)} records excluded")
    
    # Filter 2: Exclude systems with <10 flare events
    flare_mask = df['flare_count'] >= 10
    df = df[flare_mask].copy()
    filter_log.append(f"Flare count filter: {initial_count - len(df)} records excluded")
    
    # Filter 3: Exclude records with missing mass, radius, or semi-major axis
    valid_mask = df['host_mass'].notna() & df['host_rad'].notna() & df['pl_orbsmax'].notna()
    df = df[valid_mask].copy()
    filter_log.append(f"Missing data filter: {initial_count - len(df)} records excluded")
    
    # Impute missing system_age with DEFAULT_M_DWARF_AGE
    age_missing = df['host_age'].isna()
    if age_missing.any():
        df.loc[age_missing, 'host_age'] = DEFAULT_M_DWARF_AGE
        log_api_provenance(
            log_path=LOG_PATH,
            query_type="imputation",
            source="Internal",
            params={"column": "host_age", "value": DEFAULT_M_DWARF_AGE, "count": int(age_missing.sum())},
            status="warning",
            error_message=f"Imputed {int(age_missing.sum())} missing age values with DEFAULT_M_DWARF_AGE"
        )
    
    duration = time.time() - start_time
    log_api_provenance(
        log_path=LOG_PATH,
        query_type="filter_and_impute",
        source="Internal",
        params={"initial_count": initial_count, "final_count": len(df), "filters": filter_log},
        status="success",
        record_count=len(df),
        duration_seconds=duration
    )
    
    return df

def save_processed_data(df: pd.DataFrame, output_path: str) -> str:
    """
    Save the final filtered dataset to CSV and generate checksum.

    Args:
        df: DataFrame to save.
        output_path: Path to save the CSV file.

    Returns:
        Checksum of the saved file.
    """
    start_time = time.time()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    checksum = calculate_checksum(output_file)
    
    duration = time.time() - start_time
    log_api_provenance(
        log_path=LOG_PATH,
        query_type="save_processed_data",
        source="Internal",
        params={"output_path": str(output_path), "record_count": len(df)},
        status="success",
        record_count=len(df),
        duration_seconds=duration
    )
    
    return checksum

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Run the complete data ingestion pipeline.

    Returns:
        Final processed DataFrame.
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Fetch data
    flare_df = fetch_flare_catalog()
    exoplanet_df = fetch_exoplanet_params()
    
    # Merge datasets
    merged_df = merge_datasets(flare_df, exoplanet_df)
    
    # Validate rotation period
    merged_df = validate_rotation_period(merged_df)
    
    # Filter and impute
    filtered_df = filter_and_impute(merged_df)
    
    # Save processed data
    output_path = "data/processed/merged_filtered.csv"
    checksum = save_processed_data(filtered_df, output_path)
    
    logger.info(f"Pipeline complete. Output saved to {output_path} (checksum: {checksum})")
    
    return filtered_df

# Import needed for save_processed_data
from utils import calculate_checksum
