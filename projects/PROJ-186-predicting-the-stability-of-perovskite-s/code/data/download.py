"""
code/data/download.py

Implements data ingestion from the Materials Project API.
Fetches up to 10,000 perovskite entries, validates them, and filters
for specific structural criteria (Space Group 221 or 148).
"""
import os
import sys
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Project-relative imports
from utils.api_client import fetch_with_backoff, get_api_key
from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event

# Constants
MP_API_URL = "https://api.materialsproject.org/v2/materials"
MP_PEROVSKITE_ENDPOINT = f"{MP_API_URL}/search/"
MAX_ENTRIES = 10000
MIN_VALID_ENTRIES = 5000
TARGET_SPACE_GROUPS = [221, 148]  # Cubic (221), Rhombohedral (148)

logger = get_logger(__name__)


def fetch_materials_project_entries(limit: int = MAX_ENTRIES) -> List[Dict[str, Any]]:
    """
    Fetches perovskite entries from the Materials Project API.

    Args:
        limit: Maximum number of entries to fetch.

    Returns:
        List of raw entry dictionaries.

    Raises:
        RuntimeError: If the API key is missing or the fetch fails completely.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Materials Project API key not found. Set MP_API_KEY environment variable.")

    logger.info(f"Fetching up to {limit} entries from Materials Project API...")

    # Parameters for the search
    # We filter for 'perovskite' in the chemical system or specific structure types if available.
    # The standard endpoint allows searching by 'structure_types' or 'chemsys'.
    # We will request 'perovskite' structure type and limit results.
    params = {
        "structure_types": ["perovskite"],
        "elements": ["A", "B", "X"], # Placeholder logic, actual API uses element lists
        "page_limit": limit,
        "fields": ["material_id", "formula_pretty", "structure", "space_group", "decomposition_energy_per_atom", "e_above_hull"]
    }

    # Note: The MP API v2 search endpoint is complex. We will use the standard search
    # with a focus on the 'perovskite' structure type tag if available, or filter manually.
    # For robustness, we assume the endpoint supports a query for structure types.
    # If the specific 'perovskite' tag is not directly searchable by name in the simple endpoint,
    # we might need to fetch a broader set and filter, but the task asks to fetch perovskites.
    # We will use the 'structure_types' parameter with 'perovskite' as the value.

    headers = {"X-API-Key": api_key}
    
    # Construct URL with query parameters
    query_params = {
        "structure_types": "perovskite",
        "page_limit": limit,
        "fields": "material_id,formula_pretty,space_group.number,decomposition_energy_per_atom,e_above_hull,nsites"
    }

    try:
        response = fetch_with_backoff(MP_PEROVSKITE_ENDPOINT, params=query_params, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            raise RuntimeError(f"Failed to fetch data from Materials Project: {response.status_code}")
        
        data = response.json()
        results = data.get("results", [])
        
        logger.info(f"Successfully fetched {len(results)} raw entries from API.")
        return results

    except Exception as e:
        logger.exception(f"Error fetching from Materials Project API: {e}")
        raise


def validate_and_filter_entries(entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Validates entries for required fields and filters by space group.
    Also checks for valid decomposition energy.

    Args:
        entries: List of raw entry dictionaries.

    Returns:
        Tuple of (filtered_entries, exclusion_count).
    """
    filtered = []
    exclusion_count = 0

    logger.info(f"Validating and filtering {len(entries)} entries...")

    for entry in entries:
        # Extract fields safely
        material_id = entry.get("material_id")
        formula = entry.get("formula_pretty")
        space_group = entry.get("space_group", {}).get("number") if isinstance(entry.get("space_group"), dict) else entry.get("space_group")
        decomp_energy = entry.get("decomposition_energy_per_atom")
        
        # Validation 1: Required fields present
        if not material_id or not formula:
            log_exclusion_reason("download", material_id or "unknown", "Missing material_id or formula")
            exclusion_count += 1
            continue

        # Validation 2: Space group filter (221 or 148)
        if space_group not in TARGET_SPACE_GROUPS:
            log_exclusion_reason("download", material_id, f"Space group {space_group} not in target list {TARGET_SPACE_GROUPS}")
            exclusion_count += 1
            continue

        # Validation 3: Decomposition energy must be present (not null)
        if decomp_energy is None:
            log_exclusion_reason("download", material_id, "Missing decomposition_energy_per_atom")
            exclusion_count += 1
            continue

        # Validation 4: Reasonable energy range (optional but good practice)
        # Perovskites are typically stable or metastable. 
        # We accept any value as long as it's not null, but log extreme outliers if needed.
        
        # Keep the entry
        filtered.append({
            "material_id": material_id,
            "formula": formula,
            "space_group": space_group,
            "decomposition_energy": decomp_energy,
            "raw_entry": entry
        })

    logger.info(f"Filtering complete. Kept {len(filtered)} entries, excluded {exclusion_count}.")
    return filtered, exclusion_count


def main():
    """
    Main entry point for the download script.
    Fetches data, validates, and saves to data/raw/mp_perovskites.json.
    Raises a critical error if fewer than 5,000 valid entries are found.
    """
    log_pipeline_event("download", "Starting data ingestion from Materials Project")

    try:
        # 1. Fetch data
        raw_entries = fetch_materials_project_entries(limit=MAX_ENTRIES)
        
        if not raw_entries:
            raise RuntimeError("API returned zero entries. Check API key and query parameters.")

        # 2. Validate and Filter
        valid_entries, exclusion_count = validate_and_filter_entries(raw_entries)

        # 3. Critical Check: Minimum Threshold
        if len(valid_entries) < MIN_VALID_ENTRIES:
            error_msg = (
                f"CRITICAL FAILURE: Only {len(valid_entries)} valid entries found. "
                f"Minimum required is {MIN_VALID_ENTRIES}. "
                f"Excluded {exclusion_count} entries due to structural or data criteria. "
                f"Cannot proceed with statistical validity."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Success: {len(valid_entries)} valid entries meet all criteria.")

        # 4. Save to disk
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "mp_perovskites.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(valid_entries, f, indent=2)

        logger.info(f"Saved {len(valid_entries)} entries to {output_path}")
        log_pipeline_event("download", f"Completed ingestion. Output: {output_path}")

    except Exception as e:
        logger.exception(f"Download pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
