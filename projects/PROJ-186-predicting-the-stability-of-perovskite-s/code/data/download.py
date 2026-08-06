"""
Materials Project Data Ingestion Module for Perovskite Stability Prediction.

This module handles fetching raw ABX3 compositions from the Materials Project API,
validating the count, and filtering by structure. It also integrates OQMD data
if the MP fetch yields fewer than 5,000 valid entries.
"""
import os
import sys
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import requests

# Import from existing API surface
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary
from utils.api_client import get_api_key, RateLimitedSession, fetch_with_backoff
from data.download_oqmd import fetch_oqmd_entries, merge_oqmd_with_mp

logger = get_logger(__name__)

# Constants
MP_API_URL = "https://materialsproject.org/rest/v2/materials"
MP_API_KEY = get_api_key() # Retrieves from env or config
MIN_MP_ENTRIES = 5000
MAX_MP_ENTRIES = 10000

def fetch_materials_project_entries(limit: int = MAX_MP_ENTRIES) -> pd.DataFrame:
    """
    Fetches entries from Materials Project API.
    
    Args:
        limit: Maximum number of entries to fetch.
        
    Returns:
        DataFrame with raw MP data.
    """
    logger.info(f"Fetching Materials Project data (limit={limit})...")
    
    if not MP_API_KEY:
        logger.error("Materials Project API key not found. Please set MP_API_KEY environment variable.")
        raise ValueError("MP_API_KEY not set")
    
    session = RateLimitedSession()
    url = f"{MP_API_URL}/search"
    
    params = {
        'api_key': MP_API_KEY,
        'limit': limit,
        'fields': 'material_id,formula,space_group,decomposition_energy,structure'
    }
    
    try:
        response = fetch_with_backoff(session, url, params=params, max_retries=5)
        response.raise_for_status()
        data = response.json()
        
        if 'results' not in data:
            logger.error("MP API response did not contain 'results' key.")
            raise ValueError("Invalid MP API response format")
        
        entries = data['results']
        df = pd.DataFrame(entries)
        
        # Ensure required columns exist
        required_cols = ['formula', 'space_group', 'decomposition_energy']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"MP data missing required column: {col}")
                raise ValueError(f"MP data missing column: {col}")
        
        logger.info(f"Successfully fetched {len(df)} entries from Materials Project.")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch MP data: {e}")
        raise RuntimeError("MP data fetch failed.")
    except ValueError as e:
        logger.error(f"Failed to parse MP data: {e}")
        raise

def validate_and_filter_entries(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validates and filters entries based on structure (space_group).
    Filters for space_group == 221 (Cubic) OR space_group == 148 (Rhombohedral).
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded entries).
    """
    logger.info(f"Validating and filtering {len(df)} entries...")
    
    initial_count = len(df)
    
    # Filter by space group
    valid_space_groups = [221, 148]
    filtered_df = df[df['space_group'].isin(valid_space_groups)]
    
    excluded_count = initial_count - len(filtered_df)
    
    logger.info(f"Filtered to {len(filtered_df)} entries (space groups: {valid_space_groups}). Excluded: {excluded_count}")
    
    # Log exclusion reasons (simplified for this task)
    if excluded_count > 0:
        log_exclusion_reason("Structure Filtering", f"Excluded {excluded_count} entries with space_group not in {valid_space_groups}")
    
    return filtered_df, excluded_count

def main():
    """
    Main entry point for data download and merging.
    """
    log_pipeline_event("Starting data ingestion pipeline (T012 + T013)")
    
    mp_data_path = "data/raw/mp_data.csv"
    filtered_mp_path = "data/raw/mp_filtered.csv"
    merged_data_path = "data/raw/merged_data.csv"
    
    # 1. Fetch MP Data
    mp_df = None
    try:
        mp_df = fetch_materials_project_entries(limit=MAX_MP_ENTRIES)
        mp_df.to_csv(mp_data_path, index=False)
        logger.info(f"Saved MP raw data to {mp_data_path}")
    except Exception as e:
        logger.error(f"MP fetch failed: {e}")
        mp_df = pd.DataFrame()
    
    # 2. Filter MP Data
    if len(mp_df) > 0:
        mp_df, excluded_count = validate_and_filter_entries(mp_df)
        mp_df.to_csv(filtered_mp_path, index=False)
        logger.info(f"Saved filtered MP data to {filtered_mp_path}")
    else:
        mp_df = pd.DataFrame()
    
    # 3. Check Threshold and Merge with OQMD if needed
    final_df = mp_df
    
    if len(mp_df) < MIN_MP_ENTRIES:
        logger.warning(f"MP data ({len(mp_df)}) is below threshold ({MIN_MP_ENTRIES}). Fetching OQMD...")
        try:
            oqmd_df = fetch_oqmd_entries(limit=10000)
            final_df, status = merge_oqmd_with_mp(mp_df, oqmd_df)
            logger.info(f"Merging result: {status}")
        except Exception as e:
            logger.error(f"OQMD merge failed: {e}")
            # If OQMD fails, we proceed with MP data only (which is < 5000)
            # The pipeline might fail later, but we don't fabricate data.
    else:
        logger.info(f"MP data ({len(mp_df)}) is sufficient. Skipping OQMD.")
    
    # 4. Save Final Merged Data
    if len(final_df) > 0:
        final_df.to_csv(merged_data_path, index=False)
        logger.info(f"Saved final merged data to {merged_data_path}")
        log_pipeline_event(f"Ingestion complete. Total entries: {len(final_df)}")
    else:
        logger.error("No data available after ingestion.")
        raise RuntimeError("Ingestion failed: No data produced.")
    
    return final_df

if __name__ == "__main__":
    main()
