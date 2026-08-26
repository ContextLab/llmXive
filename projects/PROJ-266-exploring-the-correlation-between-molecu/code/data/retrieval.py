"""
Data Retrieval Module.

This module fetches Caco-2 permeability data from the ChEMBL REST API,
applies exponential backoff for rate limiting, and saves the raw data
to a CSV file. It also invokes the checksum utility to verify data integrity.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# ChEMBL API configuration
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
ASSAY_TYPE = "Caco-2"
STANDARD_TYPE = "MEASUREMENT"
MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # seconds

def fetch_assay_page(cursor: str = "") -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of assay data from ChEMBL.

    Args:
        cursor: Pagination cursor (empty for first page).

    Returns:
        API response dictionary or None on failure.
    """
    params = {
        "assay_type": ASSAY_TYPE,
        "standard_type": STANDARD_TYPE,
        "format": "json",
        "limit": 100
    }
    if cursor:
        params["cursor"] = cursor

    url = f"{CHEMBL_API_BASE}/assay.json"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limited
                backoff = INITIAL_BACKOFF * (2 ** attempt)
                logger.warning(f"Rate limit hit. Retrying in {backoff}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(backoff)
            else:
                logger.error(f"HTTP error: {e}")
                return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(INITIAL_BACKOFF * (2 ** attempt))

    return None

def extract_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from ChEMBL API response.

    Args:
        data: API response dictionary.

    Returns:
        List of extracted records.
    """
    records = []
    results = data.get("results", [])

    for item in results:
        try:
            # Extract SMILES (from molecule_structures)
            smiles = None
            if "molecule_structures" in item and item["molecule_structures"]:
                smiles = item["molecule_structures"][0].get("canonical_smiles")

            # Extract logPapp (standard_value, standard_units)
            logpapp = None
            if item.get("standard_type") == "MEASUREMENT" and item.get("standard_value"):
                try:
                    logpapp = float(item["standard_value"])
                except (ValueError, TypeError):
                    logpapp = None

            # Extract protocol metadata
            protocol_metadata = {
                "lab_id": item.get("assay_id", "unknown"),
                "temperature": item.get("temperature", None),
                "passage": item.get("cell_line", {}).get("passage", None) if "cell_line" in item else None
            }

            record = {
                "smiles": smiles,
                "logPapp": logpapp,
                "mw": item.get("molecular_weight", None),
                "psa": item.get("polar_surface_area", None),
                "assay_id": item.get("assay_id"),
                "protocol_metadata": json.dumps(protocol_metadata)
            }
            records.append(record)
        except Exception as e:
            logger.warning(f"Failed to extract record: {e}")
            continue

    return records

def fetch_all_caco2_data(target_count: int = 600) -> List[Dict[str, Any]]:
    """
    Fetch all Caco-2 records until target count is reached or no more data.

    Args:
        target_count: Minimum number of records to fetch.

    Returns:
        List of all fetched records.
    """
    all_records = []
    cursor = ""
    total_fetched = 0

    while total_fetched < target_count:
        logger.info(f"Fetching page. Total so far: {total_fetched}")
        data = fetch_assay_page(cursor)

        if not data or "results" not in data:
            logger.warning("No more data or failed to fetch.")
            break

        records = extract_records(data)
        all_records.extend(records)
        total_fetched = len(all_records)

        # Check for next page
        cursor = data.get("next_page")
        if not cursor:
            logger.info("No more pages available.")
            break

    logger.info(f"Total records fetched: {len(all_records)}")
    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write records to a CSV file.

    Args:
        records: List of record dictionaries.
        output_path: Path to output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    fieldnames = ["smiles", "logPapp", "mw", "psa", "assay_id", "protocol_metadata"]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def invoke_checksum_utility() -> None:
    """
    Invoke the checksum utility to generate checksums for data files.
    """
    from utils.checksum import scan_and_register_data_files
    logger.info("Invoking checksum utility.")
    scan_and_register_data_files()

def main():
    """
    Main entry point for data retrieval.
    """
    configure_root_logger()
    logger.info("Starting Caco-2 data retrieval.")

    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "chembl_raw.csv"

    records = fetch_all_caco2_data(target_count=600)

    if not records:
        logger.error("No records retrieved. Exiting.")
        sys.exit(1)

    write_raw_data(records, output_path)

    invoke_checksum_utility()

    logger.info("Data retrieval completed successfully.")

if __name__ == '__main__':
    main()
