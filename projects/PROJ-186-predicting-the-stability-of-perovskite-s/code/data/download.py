import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path to ensure imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.api_client import fetch_with_backoff, get_api_key
from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Constants
MATERIALS_PROJECT_API_URL = "https://api.materialsproject.org/v2/materials"
MAX_ENTRIES = 10000
MIN_VALID_ENTRIES = 5000
SPACE_GROUPS = [221, 148]  # Cubic (221) and Rhombohedral (148)

def fetch_materials_project_entries(limit: int = MAX_ENTRIES) -> List[Dict[str, Any]]:
    """
    Fetches material entries from the Materials Project API using the
    utils.api_client fetch_with_backoff function.
    
    Args:
        limit: Maximum number of entries to fetch.
        
    Returns:
        A list of material dictionaries containing necessary fields.
        
    Raises:
        RuntimeError: If the API returns fewer than MIN_VALID_ENTRIES.
        ConnectionError: If API access fails completely.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Materials Project API key not found. Set MP_API_KEY environment variable.")
    
    logger.info(f"Fetching up to {limit} entries from Materials Project API...")
    
    # Construct query parameters for ABX3 perovskites (simplified query for demonstration)
    # In a real scenario, we might need to iterate through pages or use specific filters.
    # Here we assume the API supports a limit parameter and returns a list of documents.
    # Note: The actual MP API v2 structure might differ, but we follow the task's requirement
    # to use the API client and fetch data.
    
    params = {
        "api_key": api_key,
        "limit": limit,
        "fields": "material_id,formula,space_group,structure,decomposition_energy"
    }
    
    # The actual endpoint for bulk retrieval might be /search or similar.
    # Using the base URL with query params as a placeholder for the specific search logic
    # required to get perovskite candidates.
    # For this implementation, we target a search endpoint that allows filtering by formula or structure.
    # Since we cannot know the exact MP API search syntax without external docs, we use a generic
    # approach that would work if the API supported a 'search' endpoint with these params.
    # However, to be robust, we will assume the standard MP API search pattern.
    
    # Standard MP API v2 search endpoint
    url = "https://api.materialsproject.org/v2/materials/search"
    
    # We need to filter for perovskites. MP doesn't have a direct "perovskite" filter in v2 search easily
    # without specific formula patterns. We will fetch a large batch and filter locally,
    # or rely on the API to return a broad set if we don't specify formula filters.
    # To ensure we get enough data, we fetch the maximum allowed and filter later.
    # The task requires fetching UP TO 10,000.
    
    try:
        response = fetch_with_backoff(url, params=params)
        
        if response.status_code != 200:
            raise ConnectionError(f"API request failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        
        # MP API v2 usually returns {'data': [...]} or similar
        if 'data' in data:
            entries = data['data']
        else:
            # Fallback if structure is different
            entries = data if isinstance(data, list) else [data]
        
        logger.info(f"Retrieved {len(entries)} entries from Materials Project API.")
        
        if len(entries) < MIN_VALID_ENTRIES:
            error_msg = (
                f"Critical: Materials Project API returned only {len(entries)} entries. "
                f"Minimum required: {MIN_VALID_ENTRIES}. "
                "The dataset is insufficient for statistical validity."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        return entries
        
    except Exception as e:
        logger.error(f"Failed to fetch from Materials Project: {str(e)}")
        raise

def validate_and_filter_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates and filters entries based on structural criteria.
    
    Args:
        entries: List of raw entries from the API.
        
    Returns:
        List of filtered entries matching space_group 221 or 148.
    """
    logger.info(f"Validating and filtering {len(entries)} entries...")
    filtered = []
    
    for entry in entries:
        try:
            # Extract space group
            # MP API structure varies; assuming 'space_group' is a dict or int
            sg = entry.get('space_group')
            
            if isinstance(sg, dict):
                sg_num = sg.get('number')
            elif isinstance(sg, int):
                sg_num = sg
            else:
                # Try to parse from string if present
                sg_str = str(sg)
                if sg_str.isdigit():
                    sg_num = int(sg_str)
                else:
                    continue
            
            # Filter for Cubic (221) or Rhombohedral (148)
            if sg_num in SPACE_GROUPS:
                filtered.append(entry)
            else:
                # Log exclusion reason if needed (optional for this task)
                pass
                
        except Exception as e:
            logger.warning(f"Could not parse entry {entry.get('material_id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Filtered down to {len(filtered)} valid perovskite candidates.")
    return filtered

def main():
    """
    Main entry point for the download script.
    Fetches data, validates count, filters, and saves to data/raw/mp_data.json.
    """
    log_pipeline_event("Starting Materials Project data download")
    
    try:
        # Step 1: Fetch entries
        raw_entries = fetch_materials_project_entries(limit=MAX_ENTRIES)
        
        # Step 2: Validate and filter (T014 logic merged here)
        valid_entries = validate_and_filter_entries(raw_entries)
        
        if len(valid_entries) == 0:
            raise RuntimeError("No valid entries found after filtering. Cannot proceed.")
        
        # Step 3: Save to disk
        output_dir = Path(PROJECT_ROOT) / "data" / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "mp_data.json"
        
        with open(output_path, 'w') as f:
            json.dump(valid_entries, f, indent=2)
        
        logger.info(f"Successfully saved {len(valid_entries)} entries to {output_path}")
        log_pipeline_event(f"Data download complete: {len(valid_entries)} entries saved")
        
    except RuntimeError as e:
        logger.critical(str(e))
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()
