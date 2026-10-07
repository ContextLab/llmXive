"""
Data Retrieval Module for Caco-2 Permeability Dataset.

This module fetches raw Caco-2 assay data from the ChEMBL REST API,
extracts relevant records, and saves them to a CSV file. It implements
exponential backoff for rate limiting and invokes the checksum utility
after successful data retrieval.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import requests

from utils.logging import get_logger
from utils.config import get_project_root
from utils.checksum import scan_and_register_data_files

logger = get_logger(__name__)

# ChEMBL API Configuration
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
ASSAY_TYPE = "Caco-2"
STANDARD_TYPE = "MEASUREMENT"
MAX_RETRIES = 3
INITIAL_DELAY = 5  # seconds
MAX_DELAY = 60  # seconds

def fetch_assay_page(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch a single page of results from the ChEMBL API with exponential backoff.

    Args:
        url: The API endpoint URL.
        params: Query parameters.

    Returns:
        JSON response as a dictionary.

    Raises:
        RuntimeError: If the request fails after max retries.
    """
    delay = INITIAL_DELAY
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching {url} (Attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [429, 503, 504]:
                last_error = e
                logger.warning(f"Rate limit or server error. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
            else:
                logger.error(f"HTTP Error {e.response.status_code}: {e}")
                raise
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Network error. Retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)

    raise RuntimeError(f"Failed to fetch data after {MAX_RETRIES} attempts: {last_error}")

def extract_records(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from a ChEMBL API page.

    Args:
        page_data: The JSON response from the API.

    Returns:
        List of extracted record dictionaries.
    """
    results = []
    assays = page_data.get("assays", [])

    for assay in assays:
        # Filter by assay type and standard type
        if assay.get("assay_type") != ASSAY_TYPE:
            continue

        # Extract standard values
        standard_values = assay.get("standard_values", [])
        if not standard_values:
            continue

        for sv in standard_values:
            if sv.get("standard_type") != STANDARD_TYPE:
                continue

            # Extract required fields
            record = {
                "smiles": sv.get("molecule_structures", {}).get("canonical_smiles"),
                "logPapp": sv.get("standard_value"),
                "mw": sv.get("molecule_structures", {}).get("molecular_weight"),
                "psa": sv.get("molecule_structures", {}).get("polar_surface_area"),
                "assay_id": assay.get("assay_id"),
                "protocol_metadata": {
                    "standard_type": sv.get("standard_type"),
                    "standard_units": sv.get("standard_units"),
                    "assay_description": assay.get("assay_description"),
                    "cell_line": assay.get("cell_line_chembl_id"),
                    "tissue": assay.get("tissue_chembl_id")
                }
            }

            # Only include records with valid SMILES and logPapp
            if record["smiles"] and record["logPapp"] is not None:
                results.append(record)

    return results

def fetch_all_caco2_data() -> List[Dict[str, Any]]:
    """
    Fetch all Caco-2 data from ChEMBL with pagination.

    Returns:
        List of all extracted records.
    """
    all_records = []
    url = f"{CHEMBL_API_BASE}/assay.json"
    params = {
        "assay_type": ASSAY_TYPE,
        "format": "json",
        "limit": 100,
        "offset": 0
    }

    page_count = 0
    while True:
        page_data = fetch_assay_page(url, params)
        records = extract_records(page_data)
        all_records.extend(records)

        logger.info(f"Page {page_count + 1}: Fetched {len(records)} valid records. Total: {len(all_records)}")

        # Check for next page
        next_url = page_data.get("meta", {}).get("next")
        if not next_url:
            break

        params["offset"] += params["limit"]
        page_count += 1

        # Safety break to avoid infinite loops in testing
        if page_count > 100:
            logger.warning("Reached maximum page limit (100). Stopping pagination.")
            break

    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write records to a CSV file.

    Args:
        records: List of record dictionaries.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    # Define CSV columns
    fieldnames = [
        "smiles",
        "logPapp",
        "mw",
        "psa",
        "assay_id",
        "protocol_metadata"
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            # Serialize protocol_metadata to JSON string
            row = record.copy()
            row["protocol_metadata"] = json.dumps(row["protocol_metadata"])
            writer.writerow(row)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def invoke_checksum_utility() -> None:
    """
    Invoke the checksum utility to register the newly created data file.
    """
    logger.info("Invoking checksum utility...")
    scan_and_register_data_files()
    logger.info("Checksum utility completed.")

def main():
    """
    Main entry point for data retrieval.
    """
    logger.info("Starting Caco-2 data retrieval.")

    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "chembl_raw.csv"

    # Fetch data
    records = fetch_all_caco2_data()

    if len(records) < 600:
        logger.warning(f"Retrieved only {len(records)} records. Expected >= 600.")
        # Continue anyway as the data might be limited in the real API response

    # Write data
    write_raw_data(records, output_path)

    # Invoke checksum utility
    invoke_checksum_utility()

    logger.info("Data retrieval completed.")

if __name__ == '__main__':
    main()
