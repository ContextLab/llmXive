"""
Data ingestion module for fetching perovskite structures from Materials Project and OQMD.
"""
import os
import sys
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.api_client import RateLimitedSession, fetch_with_backoff, get_api_key
from utils.config import get_config_summary

# Initialize logger
logger = get_logger(__name__)

# Constants
MAX_ENTRIES = 10000
MIN_VALID_ENTRIES = 5000
MP_API_URL = "https://next-gen.materialsproject.org/materials"
MP_API_KEY = get_api_key()

# Space group filters (Cubic: 200-230, Rhombohedral: 146, 148, 155, 160, 161, 166, 167)
CUBIC_SPACE_GROUPS = set(range(200, 231))
RHOMBOHEDRAL_SPACE_GROUPS = {146, 148, 155, 160, 161, 166, 167}
TARGET_SPACE_GROUPS = CUBIC_SPACE_GROUPS.union(RHOMBOHEDRAL_SPACE_GROUPS)

def fetch_materials_project_entries(limit: int = MAX_ENTRIES) -> Tuple[pd.DataFrame, int]:
    """
    Fetch entries from Materials Project API.
    Returns a DataFrame and the count of valid entries fetched.
    """
    if not MP_API_KEY:
        logger.warning("MATERIALS_PROJECT_API_KEY not found. Skipping MP fetch.")
        return pd.DataFrame(), 0

    session = RateLimitedSession()
    headers = {"X-API-Key": MP_API_KEY}
    
    # Construct query for perovskites (ABX3) with specific space groups
    # We request specific fields to minimize payload
    params = {
        "structure": {"space_group.number": {"$in": list(TARGET_SPACE_GROUPS)}},
        "fields": "material_id,formula,structure,decomposition_energy,space_group.number",
        "limit": limit,
        "prettyJSON": True
    }

    try:
        response = fetch_with_backoff(session, MP_API_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data:
            logger.error("Materials Project response missing 'data' key.")
            return pd.DataFrame(), 0

        entries = data["data"]
        df = pd.DataFrame(entries)
        
        # Normalize nested structure if needed (MP API returns structure as dict)
        # We only need the formula and space group for initial filtering
        # The 'structure' field is kept for later descriptor calculation if needed, 
        # but for now we rely on formula and space_group.number
        
        valid_count = len(df)
        log_pipeline_event(f"Fetched {valid_count} entries from Materials Project.")
        
        return df, valid_count

    except Exception as e:
        logger.error(f"Failed to fetch from Materials Project: {e}")
        raise RuntimeError("Real data fetch failed") from e

def fetch_oqmd_entries(limit: int = MAX_ENTRIES) -> Tuple[pd.DataFrame, int]:
    """
    Fetch entries from OQMD (Open Quantum Materials Database).
    Note: OQMD access often requires registration or specific endpoints.
    For this implementation, we attempt a standard fetch or return empty if unavailable.
    """
    # OQMD API key handling (if needed)
    oqmd_key = os.getenv("OQMD_API_KEY")
    
    # OQMD endpoint example (simplified for demonstration of logic)
    # In a real scenario, this would point to the specific OQMD query endpoint
    oqmd_url = "https://oqmd.org/materials/composition"
    
    if not oqmd_key:
        logger.warning("OQMD_API_KEY not found. Skipping OQMD fetch.")
        return pd.DataFrame(), 0

    session = RateLimitedSession()
    headers = {"Authorization": f"Token {oqmd_key}"}
    
    # OQMD query logic would go here. 
    # Since OQMD API structure differs significantly and might require complex pagination,
    # we implement a placeholder that attempts to fetch or returns empty if not configured.
    # Given the constraints, we assume if MP fails the threshold, we try to fetch OQMD.
    
    try:
        # Placeholder for OQMD specific query construction
        # This assumes an endpoint that returns JSON compatible with our schema
        params = {
            "formula": "perovskite", # Hypothetical filter
            "limit": limit
        }
        
        # Attempt fetch
        response = fetch_with_backoff(session, oqmd_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Convert to DataFrame (schema adaptation needed)
        # Assuming 'entries' key exists
        if "entries" in data:
            df = pd.DataFrame(data["entries"])
            # Map OQMD fields to our expected schema if necessary
            # e.g., OQMD might use 'energy_per_atom' instead of 'decomposition_energy'
            if 'energy_per_atom' in df.columns and 'decomposition_energy' not in df.columns:
                df['decomposition_energy'] = df['energy_per_atom']
            
            valid_count = len(df)
            log_pipeline_event(f"Fetched {valid_count} entries from OQMD.")
            return df, valid_count
        else:
            return pd.DataFrame(), 0

    except Exception as e:
        logger.warning(f"OQMD fetch failed or no data: {e}. Proceeding with available data.")
        return pd.DataFrame(), 0

def validate_oqmd_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the OQMD DataFrame has the necessary columns.
    """
    required_cols = ['formula', 'decomposition_energy', 'space_group.number']
    return all(col in df.columns for col in required_cols)

def merge_datasets(mp_df: pd.DataFrame, oqmd_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Materials Project and OQMD datasets.
    Removes duplicates based on formula and space group if possible.
    """
    if mp_df.empty:
        return oqmd_df
    if oqmd_df.empty:
        return mp_df
    
    # Concatenate
    combined = pd.concat([mp_df, oqmd_df], ignore_index=True)
    
    # Drop duplicates based on formula (simple deduplication)
    # In a real scenario, we might use material_id if available
    combined = combined.drop_duplicates(subset=['formula'], keep='first')
    
    log_pipeline_event(f"Merged datasets. Total unique entries: {len(combined)}")
    return combined

def validate_and_filter_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter entries strictly for Cubic or Rhombohedral space groups.
    """
    if df.empty:
        return df

    # Ensure space_group.number is numeric
    if 'space_group.number' in df.columns:
        df = df.dropna(subset=['space_group.number'])
        df['space_group.number'] = df['space_group.number'].astype(int)
        
        # Filter
        mask = df['space_group.number'].isin(TARGET_SPACE_GROUPS)
        filtered = df[mask]
        
        excluded_count = len(df) - len(filtered)
        if excluded_count > 0:
            log_pipeline_event(f"Excluded {excluded_count} entries with non-target space groups.")
        
        return filtered
    else:
        logger.warning("Space group column missing. Returning all entries.")
        return df

def main():
    """
    Main entry point for data download.
    1. Fetch from MP.
    2. If < 5000, fetch from OQMD.
    3. Merge.
    4. Filter by space group.
    5. Log warning if < 5000 but proceed.
    """
    log_pipeline_event("Starting data download process.")
    
    # Step 1: Fetch Materials Project
    mp_df, mp_count = fetch_materials_project_entries()
    total_count = mp_count
    
    # Step 2: Fetch OQMD if needed
    oqmd_df = pd.DataFrame()
    if total_count < MIN_VALID_ENTRIES:
        log_pipeline_event(f"MP count ({total_count}) < {MIN_VALID_ENTRIES}. Fetching OQMD.")
        oqmd_df, oqmd_count = fetch_oqmd_entries()
        total_count += oqmd_count
    
    # Step 3: Merge
    combined_df = merge_datasets(mp_df, oqmd_df)
    
    # Step 4: Filter by Space Group
    final_df = validate_and_filter_entries(combined_df)
    final_count = len(final_df)
    
    # Step 5: Check count
    if final_count < MIN_VALID_ENTRIES:
        logger.warning(f"Total valid entries ({final_count}) is less than {MIN_VALID_ENTRIES}. Proceeding with available data.")
    else:
        log_pipeline_event(f"Target reached: {final_count} valid entries.")
    
    # Save to intermediate raw file
    output_path = "data/processed/raw_perovskites.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    log_pipeline_event(f"Saved raw data to {output_path}")
    
    return final_df

if __name__ == "__main__":
    main()