"""
01_discover_data.py

Queries the Dryad API to find datasets related to bird telomere length.
Extracts valid dataset IDs and writes them back into `code/config.yaml`.
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

import yaml
from logging_config import setup_logging, ensure_log_directory
from utils import generate_checksum, update_state_file

# Constants
SEARCH_QUERY = "telomere bird"
CONFIG_PATH = Path("code") / "config.yaml"
LOG_FILE_NAME = "discover_data.log"  # name only; logging_config will prepend the logs dir

def load_config() -> Dict[str, Any]:
    """Load the YAML configuration file."""
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg: Dict[str, Any]) -> None:
    """Write the updated configuration back to disk."""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, default_flow_style=False)

def search_dryad(query: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Query Dryad API for datasets matching the query.
    Returns a list of dataset metadata dictionaries.
    """
    base_url = "https://datadryad.org/api/v2/datasets"
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

    response = requests.get(base_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    # Dryad may return results under different keys depending on version
    return data.get("data", data.get("entry", []))

def extract_dataset_ids(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract relevant dataset ID and metadata from Dryad search results.
    Returns a list of dicts with 'id', 'doi', and 'title'.
    """
    valid = []
    for item in results:
        dataset_id = item.get("identifier") or item.get("id")
        doi = item.get("doi") or item.get("dc:identifier")
        title = item.get("title") or item.get("dc:title") or "Unknown Title"
        if dataset_id and doi:
            valid.append({
                "id": str(dataset_id),
                "doi": doi,
                "title": title,
            })
    return valid

def main() -> None:
    # Initialise logger – only the filename is passed; the helper creates the logs directory.
    logger = setup_logging(log_file=LOG_FILE_NAME)
    logger.info("Starting Dryad dataset discovery (T002)...")

    cfg = load_config()
    dryad_api_key = cfg.get("dryad_api_key")  # optional; may be absent

    try:
        logger.info(f"Searching Dryad for query: '{SEARCH_QUERY}'")
        results = search_dryad(SEARCH_QUERY, dryad_api_key)

        if not results:
            logger.error("Dryad API returned no results.")
            sys.exit(1)

        logger.info(f"Dryad returned {len(results)} raw entries.")
        datasets = extract_dataset_ids(results)

        if not datasets:
            logger.error("No usable dataset IDs could be extracted.")
            sys.exit(1)

        # Update config with the discovered DOIs (store just the DOI strings)
        discovered_dois = [d["doi"] for d in datasets]
        cfg["dataset_ids"] = discovered_dois
        save_config(cfg)

        # Persist the full list as a JSON artefact for downstream steps
        output_dir = Path("data") / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "dryad_dataset_ids.json"
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(datasets, jf, indent=2)

        # Record checksum for provenance
        checksum = generate_checksum(json_path)
        update_state_file({"dryad_discovery": checksum})

        logger.info(f"Discovered {len(discovered_dois)} DOIs and wrote to {CONFIG_PATH}")
        logger.info("Discovery phase completed successfully.")
    except Exception as exc:
        logger.exception(f"Discovery failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
