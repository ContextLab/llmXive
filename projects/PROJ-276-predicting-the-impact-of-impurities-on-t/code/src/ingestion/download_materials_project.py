"""
Download Magnesium Diboride (MgB2) entries from the Materials Project API.

This script fetches crystal structure and property data for Mg-B compounds,
filters for entries with critical temperature (Tc) data, and handles rate limits.

Exit codes:
    0: Success (data downloaded and saved)
    1: Failure (API error, empty results, or missing configuration)
"""
import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import RequestException, Timeout

# Project imports
from src.utils.config import get_materials_project_api_key, get_project_root
from src.utils.logging import get_ingestion_logger

# Constants
RATE_LIMIT_DELAY = 1.5  # seconds between requests
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds
MATERIALS_PROJECT_API_URL = "https://api.materialsproject.org/v2/materials"

logger = get_ingestion_logger()


def fetch_materials_project_entries(
    api_key: str,
    chemical_system: str = "Mg-B",
    fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch entries from Materials Project API for a specific chemical system.
    
    Args:
        api_key: Materials Project API key
        chemical_system: Chemical system to query (e.g., "Mg-B")
        fields: List of specific fields to retrieve (defaults to essential fields)
        
    Returns:
        List of material entries as dictionaries
        
    Raises:
        RequestException: If API request fails after retries
        ValueError: If API key is invalid or missing
    """
    if fields is None:
        fields = [
            "material_id", "formula_pretty", "nsites", "structure",
            "e_above_hull", "decomp_energy", "formation_energy_per_atom",
            "band_gap", "is_metal", "is_stable", "space_group.number",
            "space_group.symbol", "thermo.Tc", "thermo.Tc_method",
            "thermo.Tc_temperature"
        ]
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Build query parameters
    params = {
        "chemical_system": chemical_system,
        "fields": ",".join(fields),
        "limit": 1000  # Max allowed per request
    }
    
    url = f"{MATERIALS_PROJECT_API_URL}/search"
    
    all_entries = []
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Fetching Mg-B entries from Materials Project (attempt {retry_count + 1})...")
            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", RATE_LIMIT_DELAY))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                retry_count += 1
                continue
            
            # Check for other errors
            response.raise_for_status()
            
            data = response.json()
            
            if "data" not in data:
                logger.error("Invalid API response: 'data' key missing")
                raise ValueError("Invalid API response structure")
            
            entries = data.get("data", [])
            all_entries.extend(entries)
            
            # Check if there are more pages (pagination not fully implemented for simplicity)
            if len(entries) < params["limit"]:
                break
                
            # If we got the max limit, there might be more data
            # For now, we stop at 1000 as per API limit per request
            logger.info(f"Retrieved {len(entries)} entries. Total: {len(all_entries)}")
            break
            
        except Timeout:
            logger.warning(f"Request timed out (attempt {retry_count + 1})")
            retry_count += 1
            time.sleep(RATE_LIMIT_DELAY)
            
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            if retry_count < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_DELAY * (retry_count + 1))
                retry_count += 1
            else:
                raise
                
        except ValueError as e:
            logger.error(f"API response error: {e}")
            raise
    
    if not all_entries:
        logger.warning("No entries returned from Materials Project API")
        
    return all_entries


def filter_mgb2_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter entries to keep only those relevant to MgB2 superconductivity research.
    
    Criteria:
        - Contains Magnesium (Mg) and Boron (B)
        - Has critical temperature (Tc) data available
        - Preferentially selects stoichiometric MgB2 or close variants
        
    Args:
        entries: List of raw API entries
        
    Returns:
        Filtered list of entries
    """
    filtered = []
    
    for entry in entries:
        formula = entry.get("formula_pretty", "")
        
        # Check for Mg and B in formula
        if "Mg" not in formula or "B" not in formula:
            continue
        
        # Check for Tc data
        thermo = entry.get("thermo", {})
        tc_value = thermo.get("Tc")
        
        if tc_value is None or tc_value == "null":
            logger.debug(f"Skipping {formula} (material_id: {entry.get('material_id')}) - No Tc data")
            continue
        
        # Additional validation: check if it's a reasonable superconductor
        try:
            tc_float = float(tc_value) if isinstance(tc_value, str) else tc_value
            if tc_float <= 0:
                logger.debug(f"Skipping {formula} - Non-positive Tc: {tc_float}")
                continue
        except (ValueError, TypeError):
            logger.debug(f"Skipping {formula} - Invalid Tc value: {tc_value}")
            continue
        
        filtered.append(entry)
    
    logger.info(f"Filtered {len(entries)} entries down to {len(filtered)} with valid Tc data")
    return filtered


def save_entries_to_json(entries: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save filtered entries to a JSON file with metadata.
    
    Args:
        entries: List of entries to save
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "source": "Materials Project API",
        "chemical_system": "Mg-B",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": len(entries),
        "api_version": "v2"
    }
    
    output_data = {
        "metadata": metadata,
        "entries": entries
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"Saved {len(entries)} entries to {output_path}")


def main() -> int:
    """
    Main entry point for downloading Materials Project data.
    
    Returns:
        Exit code: 0 for success, 1 for failure
    """
    try:
        # Get configuration
        project_root = get_project_root()
        api_key = get_materials_project_api_key()
        
        if not api_key:
            logger.error("Materials Project API key not found. Set MATERIALS_PROJECT_API_KEY environment variable.")
            return 1
        
        # Define output path
        output_dir = project_root / "data" / "raw"
        output_path = output_dir / "materials_project_mgb2.json"
        
        logger.info("Starting Materials Project download for Mg-B system")
        
        # Fetch data
        raw_entries = fetch_materials_project_entries(api_key)
        
        if not raw_entries:
            logger.error("No entries found in Materials Project API response")
            return 1
        
        # Filter entries
        filtered_entries = filter_mgb2_entries(raw_entries)
        
        if not filtered_entries:
            logger.error("No valid MgB2 entries with Tc data found after filtering")
            return 1
        
        # Save data
        save_entries_to_json(filtered_entries, output_path)
        
        logger.info(f"Successfully downloaded {len(filtered_entries)} MgB2 entries")
        return 0
        
    except KeyError as e:
        logger.error(f"Missing configuration key: {e}")
        return 1
    except RequestException as e:
        logger.error(f"API request failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())