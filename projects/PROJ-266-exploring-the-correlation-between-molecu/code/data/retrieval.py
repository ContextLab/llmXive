"""
Data Retrieval Module for ChEMBL Caco-2 Permeability Data.

This module fetches raw Caco-2 assay data from the ChEMBL REST API,
applies exponential backoff for rate limiting, and saves the results
to a CSV file. It also invokes the checksum utility to ensure data integrity.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils.logging import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# ChEMBL API Configuration
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/v1/"
MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # seconds
ASSAY_TYPE = "Caco-2"
STANDARD_TYPE = "MEASUREMENT"
REQUIRED_FIELDS = ["smiles", "logPapp", "mw", "psa", "assay_id", "protocol_metadata"]

def fetch_assay_page(offset: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Fetch a page of assay results from ChEMBL API with exponential backoff.

    Args:
        offset: Starting offset for pagination.
        limit: Number of records per page.

    Returns:
        JSON response as a dictionary, or None if failed after retries.
    """
    url = f"{CHEMBL_API_BASE}assay/"
    params = {
        "assay_type": ASSAY_TYPE,
        "standard_type": STANDARD_TYPE,
        "format": "json",
        "offset": offset,
        "limit": limit,
        "order_by": "assay_id"
    }

    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching ChEMBL data (offset={offset}, attempt={attempt + 1})...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Too Many Requests
                logger.warning(f"Rate limit hit (429). Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
                attempt += 1
            else:
                logger.error(f"HTTP error: {e}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            time.sleep(backoff)
            backoff *= 2
            attempt += 1

    logger.error(f"Failed to fetch data after {MAX_RETRIES} retries.")
    return None

def extract_records(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from a ChEMBL API response page.

    Args:
        page_data: JSON response from the API.

    Returns:
        List of extracted records.
    """
    results = []
    assays = page_data.get("assays", [])

    for assay in assays:
        # Extract basic assay info
        assay_id = assay.get("assay_id")
        # We need to fetch the specific assay details to get the standard_value
        # However, for efficiency, we can try to get the standard_value from the 'results'
        # endpoint linked to this assay, or assume the API returns standard_value in the assay object if filtered.
        # The ChEMBL API structure for 'assay' endpoint often requires a secondary call to 'results'
        # to get the specific measurements.
        
        # Let's fetch the results for this specific assay_id to get the standard_value and standard_units
        results_url = f"{CHEMBL_API_BASE}assay/{assay_id}/results/"
        try:
            res_response = requests.get(results_url, params={"format": "json"}, timeout=30)
            if res_response.status_code == 200:
                res_data = res_response.json()
                for res in res_data.get("results", []):
                    # Filter for standard_type = MEASUREMENT (already filtered in assay query, but double check)
                    if res.get("standard_type") == STANDARD_TYPE:
                        record = {
                            "smiles": res.get("smiles") or res.get("molecule_structures", {}).get("canonical_smiles"),
                            "logPapp": res.get("standard_value"),
                            "mw": res.get("molecule_properties", {}).get("molecular_weight"),
                            "psa": res.get("molecule_properties", {}).get("polar_surface_area"),
                            "assay_id": assay_id,
                            "protocol_metadata": {
                                "standard_type": res.get("standard_type"),
                                "heterogeneity_score": 0.0  # Placeholder, calculated later or from specific metadata
                            }
                        }
                        # Clean up None values where appropriate but keep structure
                        if record["smiles"] is None:
                            continue
                        results.append(record)
            else:
                logger.warning(f"Could not fetch results for assay {assay_id}: {res_response.status_code}")
        except Exception as e:
            logger.warning(f"Error fetching results for assay {assay_id}: {e}")
            continue

    return results

def fetch_all_caco2_data(target_count: int = 600) -> List[Dict[str, Any]]:
    """
    Fetch all Caco-2 records until we reach the target count or exhaust the API.

    Args:
        target_count: Minimum number of records to fetch.

    Returns:
        List of all extracted records.
    """
    all_records = []
    offset = 0
    limit = 100

    while len(all_records) < target_count:
        page_data = fetch_assay_page(offset=offset, limit=limit)
        if not page_data:
            logger.error("Failed to fetch page, stopping.")
            break

        records = extract_records(page_data)
        all_records.extend(records)

        # Check if there are more pages
        if len(records) < limit:
            break

        offset += limit
        logger.info(f"Fetched {len(all_records)} records so far.")

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

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS, extrasaction='ignore')
        writer.writeheader()
        for record in records:
            # Serialize protocol_metadata to JSON string for CSV compatibility
            row = dict(record)
            row['protocol_metadata'] = json.dumps(row['protocol_metadata'])
            writer.writerow(row)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def invoke_checksum_utility(output_path: Path) -> None:
    """
    Invoke the checksum utility to generate checksums for the new data file.

    Args:
        output_path: Path to the generated CSV file.
    """
    try:
        # Import the main function from the checksum utility
        from utils.checksum import scan_and_register_data_files
        scan_and_register_data_files()
        logger.info("Checksum utility invoked successfully.")
    except Exception as e:
        logger.error(f"Failed to invoke checksum utility: {e}")
        # Do not fail the main script if checksum fails, but log it

def main():
    """
    Main entry point for data retrieval.
    """
    logger.info("Starting Caco-2 data retrieval.")
    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "chembl_raw.csv"

    records = fetch_all_caco2_data(target_count=600)
    write_raw_data(records, output_path)
    invoke_checksum_utility(output_path)

    logger.info("Data retrieval completed.")

if __name__ == '__main__':
    main()
