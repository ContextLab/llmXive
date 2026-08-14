"""
Download and merge perovskite data from Materials Project and OQMD.
Implements T012: Fetch, validate schema, merge, filter by space group.
"""
import os
import sys
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Project imports
from utils.api_client import get_api_key, RateLimitedSession, fetch_with_backoff
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary

# Constants
MP_API_BASE = "https://api.materialsproject.org"
OQMD_API_BASE = "http://oqmd.org/api"
REQUIRED_COLUMNS = ["composition", "decomposition_energy", "space_group"]
TARGET_COLUMNS = ["material_id", "formula", "composition", "elements", "decomposition_energy", "space_group", "source"]
MIN_VALID_ENTRIES = 5000
MAX_ENTRIES = 10000
CUBIC_SPACE_GROUPS = [221, 222, 223, 224, 225, 226, 227, 228, 229, 230] # Fm-3m, etc.
RHO_SPACE_GROUPS = [148, 155, 160, 161, 166, 167] # R-3m, etc.
VALID_SPACE_GROUPS = CUBIC_SPACE_GROUPS + RHO_SPACE_GROUPS

logger = get_logger(__name__)

def fetch_materials_project_entries(session: RateLimitedSession, limit: int = MAX_ENTRIES) -> List[Dict[str, Any]]:
    """
    Fetch entries from Materials Project API.
    Filters for perovskites (ABX3) implicitly by structure or formula if possible,
    but primarily relies on API response structure.
    """
    api_key = get_api_key()
    if not api_key:
        logger.warning("No Materials Project API key found. Skipping MP fetch.")
        return []

    entries = []
    # MP API endpoint for structures
    # We request specific fields to reduce payload
    endpoint = f"{MP_API_BASE}/materials/docs"
    params = {
        "api_key": api_key,
        "fields": "material_id,formula,structure,decomposition_energy,space_group",
        "limit": limit
    }

    try:
        # MP API often requires specific headers
        headers = {"x-api-key": api_key}
        response = session.get(endpoint, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                for item in data["data"]:
                    # Basic validation
                    if all(k in item for k in ["material_id", "formula", "decomposition_energy", "space_group"]):
                        entries.append({
                            "material_id": item["material_id"],
                            "formula": item["formula"],
                            "composition": item.get("composition", item["formula"]),
                            "elements": item.get("elements", []),
                            "decomposition_energy": item["decomposition_energy"],
                            "space_group": item["space_group"],
                            "source": "materials_project"
                        })
            logger.info(f"Materials Project: Fetched {len(entries)} entries.")
        else:
            logger.warning(f"Materials Project API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error fetching from Materials Project: {e}")
    
    return entries

def validate_oqmd_schema(session: RateLimitedSession) -> bool:
    """
    Perform Dataset Fit Check on OQMD to verify required columns exist.
    Returns True if schema is valid, False otherwise.
    """
    logger.info("Performing Dataset Fit Check on OQMD schema...")
    # OQMD often uses a different endpoint structure. We'll try a simple query.
    # Assuming an endpoint like /entries or similar that returns metadata.
    # Since OQMD API specifics can vary, we attempt a standard query.
    endpoint = f"{OQMD_API_BASE}/entries"
    params = {"limit": 1} # Just check one to see structure

    try:
        response = session.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                first_entry = data[0]
                # Check for required keys
                has_energy = "decomposition_energy" in first_entry
                has_sg = "space_group" in first_entry
                
                if has_energy and has_sg:
                    logger.info("OQMD Schema Check: PASSED (decomposition_energy, space_group found)")
                    return True
                else:
                    logger.error(f"OQMD Schema Check: FAILED. Keys found: {list(first_entry.keys())}")
                    return False
            else:
                logger.error("OQMD Schema Check: FAILED (Empty or invalid response)")
                return False
        else:
            logger.error(f"OQMD Schema Check: FAILED (Status {response.status_code})")
            return False
    except Exception as e:
        logger.error(f"OQMD Schema Check: FAILED with exception: {e}")
        return False

def fetch_oqmd_entries(session: RateLimitedSession, limit: int = MAX_ENTRIES) -> List[Dict[str, Any]]:
    """
    Fetch entries from OQMD API.
    """
    entries = []
    endpoint = f"{OQMD_API_BASE}/entries"
    params = {
        "limit": limit,
        "fields": "material_id,formula,composition,decomposition_energy,space_group"
    }

    try:
        response = session.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if all(k in item for k in ["material_id", "formula", "decomposition_energy", "space_group"]):
                        entries.append({
                            "material_id": item["material_id"],
                            "formula": item["formula"],
                            "composition": item.get("composition", item["formula"]),
                            "elements": [], # OQMD might not return elements list directly in summary
                            "decomposition_energy": item["decomposition_energy"],
                            "space_group": item["space_group"],
                            "source": "oqmd"
                        })
            logger.info(f"OQMD: Fetched {len(entries)} entries.")
        else:
            logger.warning(f"OQMD API returned status {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching from OQMD: {e}")
    
    return entries

def validate_and_filter_entries(entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Filter entries for valid space groups (Cubic or Rhombohedral).
    Returns filtered list and count of excluded entries.
    """
    filtered = []
    excluded_count = 0
    
    for entry in entries:
        sg = entry.get("space_group")
        if sg in VALID_SPACE_GROUPS:
            filtered.append(entry)
        else:
            excluded_count += 1
            # Log exclusion reason
            log_exclusion_reason(f"Space Group {sg} not in Cubic/Rhombohedral set")
    
    logger.info(f"Filtered {len(entries)} entries. Kept {len(filtered)}, excluded {excluded_count} based on space group.")
    return filtered, excluded_count

def main():
    """
    Main execution flow for T012.
    1. Fetch MP.
    2. If < 5000, check OQMD schema.
    3. If schema valid, fetch OQMD.
    4. Merge.
    5. Filter by space group.
    6. Check total count >= 5000.
    7. Save to data/raw/combined.csv.
    """
    log_pipeline_event("Starting T012: Data Download and Merge")
    
    session = RateLimitedSession()
    all_entries = []
    
    # Step 1: Fetch Materials Project
    logger.info("Fetching from Materials Project...")
    mp_entries = fetch_materials_project_entries(session, limit=MAX_ENTRIES)
    all_entries.extend(mp_entries)
    current_count = len(all_entries)
    logger.info(f"Current total: {current_count}")

    # Step 2: Check if fallback needed
    if current_count < MIN_VALID_ENTRIES:
        logger.warning(f"MP entries ({current_count}) < {MIN_VALID_ENTRIES}. Checking OQMD schema.")
        
        if not validate_oqmd_schema(session):
            logger.critical("OQMD Schema validation failed. Aborting fetch.")
            sys.exit(1)
        
        logger.info("OQMD Schema valid. Fetching OQMD data...")
        oqmd_entries = fetch_oqmd_entries(session, limit=MAX_ENTRIES)
        all_entries.extend(oqmd_entries)
        current_count = len(all_entries)
        logger.info(f"Total after OQMD: {current_count}")
    else:
        logger.info(f"MP entries ({current_count}) >= {MIN_VALID_ENTRIES}. Skipping OQMD fetch.")

    # Step 3: Filter by Space Group
    logger.info("Filtering by Space Group (Cubic/Rhombohedral)...")
    filtered_entries, excluded_count = validate_and_filter_entries(all_entries)
    final_count = len(filtered_entries)
    
    # Step 4: Final Count Check
    if final_count < MIN_VALID_ENTRIES:
        logger.critical(f"Total valid entries ({final_count}) < {MIN_VALID_ENTRIES} after filtering. Aborting.")
        sys.exit(1)
    
    logger.info(f"Final valid entry count: {final_count}")

    # Step 5: Save to CSV
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "combined_perovskites.csv")
    
    df = pd.DataFrame(filtered_entries)
    # Ensure column order
    df = df[TARGET_COLUMNS]
    df.to_csv(output_path, index=False)
    
    log_pipeline_event(f"Saved {final_count} entries to {output_path}")
    print(f"SUCCESS: Downloaded {final_count} entries to {output_path}")

if __name__ == "__main__":
    main()
