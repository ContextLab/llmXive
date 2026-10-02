import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

# Import from existing project API
from code.src.utils.config import get_materials_project_api_key
from code.src.utils.logging import get_ingestion_logger

# Constants for MgB2 search
ELEMENTS = ["Mg", "B"]
MIN_ELEMENTS = 2  # MgB2 has exactly 2 elements
MAX_ELEMENTS = 2  # Strictly MgB2

logger = get_ingestion_logger()

def fetch_materials_project_entries(
    api_key: str,
    elements: List[str] = None,
    max_results: int = 1000,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch entries from Materials Project API containing specified elements.

    Args:
        api_key: Materials Project API key
        elements: List of chemical elements to filter (e.g., ["Mg", "B"])
        max_results: Maximum number of entries to fetch
        timeout: Request timeout in seconds

    Returns:
        List of material entries as dictionaries
    """
    if elements is None:
        elements = ELEMENTS

    base_url = "https://next-gen.materialsproject.org/api/v2/materials"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # Construct query parameters for element presence
    # MP API uses ?elements=Mg,B for OR logic, but we need AND logic (Mg AND B)
    # We'll fetch all Mg-B compounds and filter client-side for strict MgB2
    params = {
        "elements": ",".join(elements),
        "limit": max_results,
        "fields": "material_id,elements,nelements,structure,band_gap,e_form_energy_per_atom,final_structure"
    }

    entries = []
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            logger.info(f"Fetching materials from MP API with elements: {elements}")
            response = requests.get(base_url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if "data" not in data:
                logger.warning("API response missing 'data' key")
                return []

            entries.extend(data["data"])
            logger.info(f"Successfully fetched {len(entries)} entries from MP")
            return entries

        except requests.exceptions.RequestException as e:
            retry_count += 1
            logger.warning(f"Request failed (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                logger.error("Max retries exceeded. Aborting fetch.")
                raise

def filter_mgb2_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter entries to keep only those that are strictly MgB2.

    Criteria:
    - Contains exactly Mg and B elements
    - Has exactly 2 distinct elements (nelements == 2)

    Args:
        entries: List of raw material entries

    Returns:
        Filtered list of MgB2 entries
    """
    filtered = []
    for entry in entries:
        elements = entry.get("elements", [])
        nelements = entry.get("nelements", 0)

        # Check if entry has exactly Mg and B
        element_names = [el["element"] if isinstance(el, dict) else el for el in elements]
        
        # Normalize to set of unique element symbols
        unique_elements = set(element_names)
        
        # Must have exactly Mg and B, no more, no less
        if unique_elements == {"Mg", "B"} and nelements == 2:
            filtered.append(entry)
        else:
            logger.debug(f"Skipping entry {entry.get('material_id')}: elements={unique_elements}, nelements={nelements}")

    logger.info(f"Filtered {len(entries)} entries down to {len(filtered)} MgB2 entries")
    return filtered

def save_entries_to_json(entries: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save entries to a JSON file.

    Args:
        entries: List of material entries
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2)
    
    logger.info(f"Saved {len(entries)} entries to {output_path}")

def main() -> int:
    """
    Main entry point for downloading MgB2 data from Materials Project.

    Returns:
        Exit code: 0 for success, 1 for failure (empty response or API error)
    """
    try:
        # Get API key
        api_key = get_materials_project_api_key()
        if not api_key:
            logger.error("Materials Project API key not found. Set MP_API_KEY environment variable.")
            return 1

        # Fetch entries
        entries = fetch_materials_project_entries(api_key)

        # Check for empty response
        if not entries:
            logger.error("No entries returned from Materials Project API.")
            return 1

        # Filter for MgB2
        mgb2_entries = filter_mgb2_entries(entries)

        # Check for empty filtered result
        if not mgb2_entries:
            logger.error("No MgB2 entries found after filtering.")
            return 1

        # Determine output path
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        output_dir = project_root / "data" / "raw"
        output_file = output_dir / "materials_project_mgb2_raw.json"

        # Save results
        save_entries_to_json(mgb2_entries, output_file)

        logger.info(f"Successfully downloaded and saved {len(mgb2_entries)} MgB2 entries.")
        return 0

    except Exception as e:
        logger.exception(f"Critical error in download_materials_project: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
