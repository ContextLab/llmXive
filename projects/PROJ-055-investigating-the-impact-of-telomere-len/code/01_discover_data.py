"""
01_discover_data.py

Queries the Dryad API to find datasets related to bird telomere length.
Extracts valid dataset IDs and saves them to a JSON file.
Halts the pipeline (exit code 1) if no results are found.
"""

import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
else:
    # If imported as a package, ensure parent is in path for relative imports if needed
    pass

from config import get_config
from logging_config import setup_logging, ensure_log_directory
from utils import generate_checksum, update_state_file

# Constants
DRYAD_API_BASE = "https://datadryad.org/api/v2/datasets"
SEARCH_QUERY = "telomere bird"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "dryad_dataset_ids.json"
LOG_FILE = Path("logs/discover_data.log")

def search_dryad(query: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Query Dryad API for datasets matching the query.
    Returns a list of dataset metadata dictionaries.
    """
    params = {
        "q": query,
        "qf": ["title", "abstract", "keyword"],
        "sort": "score",
        "order": "desc",
        "limit": 50  # Fetch top 50 results
    }
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(DRYAD_API_BASE, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Dryad API returns results in 'data' key usually, or 'entry'
        results = data.get("data", data.get("entry", []))
        return results
    except requests.exceptions.RequestException as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to query Dryad API: {e}")
        raise

def extract_dataset_ids(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract relevant dataset ID and metadata from Dryad search results.
    Returns a list of dicts with 'id', 'doi', and 'title'.
    """
    valid_datasets = []
    for item in results:
        # Dryad API structure varies, handle common keys
        # Often 'identifier' or 'id' inside 'entry' or direct
        dataset_id = None
        doi = None
        title = None

        # Attempt to find ID in various locations
        if "identifier" in item:
            dataset_id = item["identifier"]
        elif "id" in item:
            dataset_id = item["id"]
        
        if "doi" in item:
            doi = item["doi"]
        elif "dc:identifier" in item:
            doi = item["dc:identifier"]

        if "title" in item:
            title = item["title"]
        elif "dc:title" in item:
            title = item["dc:title"]

        if dataset_id and doi:
            valid_datasets.append({
                "id": str(dataset_id),
                "doi": doi,
                "title": title or "Unknown Title"
            })
    
    return valid_datasets

def save_dataset_ids(dataset_ids: List[Dict[str, str]], output_path: Path):
    """
    Save the list of valid dataset IDs to a JSON file.
    """
    ensure_log_directory(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset_ids, f, indent=2)
    
    # Update state file with checksum
    checksum = generate_checksum(output_path)
    update_state_file({"dryad_discovery": checksum})

def main():
    logger = setup_logging(LOG_FILE)
    logger.info("Starting Dryad dataset discovery (T014)...")
    
    config = get_config()
    dryad_api_key = config.get("dryad_api_key")
    
    try:
        logger.info(f"Searching Dryad for: '{SEARCH_QUERY}'")
        results = search_dryad(SEARCH_QUERY, dryad_api_key)
        
        if not results:
            logger.warning("No results found from Dryad API.")
            # Halt pipeline as per requirements
            sys.exit(1)
        
        logger.info(f"Found {len(results)} raw results.")
        
        valid_datasets = extract_dataset_ids(results)
        
        if not valid_datasets:
            logger.error("No valid dataset IDs could be extracted from results.")
            sys.exit(1)
        
        logger.info(f"Extracted {len(valid_datasets)} valid datasets.")
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        save_dataset_ids(valid_datasets, OUTPUT_FILE)
        
        logger.info(f"Successfully saved dataset IDs to {OUTPUT_FILE}")
        logger.info("Discovery phase complete.")
        
    except Exception as e:
        logger.error(f"Discovery process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
