"""
01_discover_data.py

Queries the Dryad API to find datasets related to bird telomere length.
Extracts valid dataset IDs and saves them to a JSON file.
Halts the pipeline (exit code 1) if no results are found.
"""

import json
import sys
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is on sys.path when run as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from logging_config import setup_logging, ensure_log_directory
from utils import generate_checksum, update_state_file

# Constants
DRYAD_API_BASE = "https://datadryad.org/api/v2/datasets"
SEARCH_QUERY = "telomere bird"
OUTPUT_DIR = Path("data") / "raw"
OUTPUT_FILE = OUTPUT_DIR / "dryad_dataset_ids.json"
LOG_FILE = Path("logs") / "discover_data.log"

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
        "limit": 50,
    }

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(DRYAD_API_BASE, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
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
        dataset_id = item.get("identifier") or item.get("id")
        doi = item.get("doi") or item.get("dc:identifier")
        title = item.get("title") or item.get("dc:title") or "Unknown Title"
        if dataset_id and doi:
            valid_datasets.append({
                "id": str(dataset_id),
                "doi": doi,
                "title": title,
            })
    return valid_datasets

def save_dataset_ids(dataset_ids: List[Dict[str, str]], output_path: Path):
    """
    Save the list of valid dataset IDs to a JSON file.
    """
    ensure_log_directory(output_path.parent)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(dataset_ids, f, indent=2)

    checksum = generate_checksum(output_path)
    update_state_file({"dryad_discovery": checksum})

def main():
    # Correct logger initialization – pass the *log_file* argument, not log_level
    logger = setup_logging(log_file=str(LOG_FILE))
    logger.info("Starting Dryad dataset discovery (T014)...")

    config = get_config()
    dryad_api_key = config.get("dryad_api_key")

    try:
        logger.info(f"Searching Dryad for: '{SEARCH_QUERY}'")
        results = search_dryad(SEARCH_QUERY, dryad_api_key)

        if not results:
            logger.warning("No results found from Dryad API.")
            sys.exit(1)

        logger.info(f"Found {len(results)} raw results.")
        valid_datasets = extract_dataset_ids(results)

        if not valid_datasets:
            logger.error("No valid dataset IDs could be extracted from results.")
            sys.exit(1)

        logger.info(f"Extracted {len(valid_datasets)} valid datasets.")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        save_dataset_ids(valid_datasets, OUTPUT_FILE)

        logger.info(f"Successfully saved dataset IDs to {OUTPUT_FILE}")
        logger.info("Discovery phase complete.")
    except Exception as e:
        logger.error(f"Discovery process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
