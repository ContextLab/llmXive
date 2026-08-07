"""
Data retrieval module for fetching Caco-2 permeability data from ChEMBL.

This module implements the retrieval of raw Caco-2 assay data using the ChEMBL
REST API. It fetches at least 600 raw records with assay_type='Caco-2' and
standard_type='MEASUREMENT', applies exponential backoff for rate limiting,
and registers the output checksum in the project state file.

Public API:
    fetch_assay_page: Fetch a single page of assay results from ChEMBL.
    extract_records: Parse ChEMBL JSON response into flat records.
    fetch_all_caco2_data: Fetch all pages until minimum record count reached.
    write_raw_data: Save fetched data to CSV.
    main: Entry point for script execution.
"""
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, configure_root_logger
from utils.checksum import register_checksum
from utils.config import get_project_root, get_data_path

# Constants
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
ASSAY_TYPE = "Caco-2"
STANDARD_TYPE = "MEASUREMENT"
MIN_RECORDS = 600
PAGE_SIZE = 100
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 60.0  # seconds

# Output paths
RAW_DATA_PATH = "data/raw/caco2_raw.csv"
STATE_FILE_PATH = "state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml"

logger = get_logger(__name__)


def fetch_assay_page(page: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of Caco-2 assay data from ChEMBL API.

    Args:
        page: Page number (0-indexed).

    Returns:
        JSON response dict or None if fetch fails after retries.
    """
    url = f"{CHEMBL_API_BASE}/assay.json"
    params = {
        "assay_type": ASSAY_TYPE,
        "standard_type": STANDARD_TYPE,
        "page": page,
        "page_size": PAGE_SIZE,
        "format": "json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching page {page} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
            logger.warning(f"Request failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)

    logger.error(f"Failed to fetch page {page} after {MAX_RETRIES} attempts")
    return None


def extract_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant fields from ChEMBL assay JSON response.

    Args:
        data: ChEMBL API JSON response.

    Returns:
        List of flat records with SMILES, logPapp, and metadata.
    """
    records = []
    results = data.get("assays", [])

    for assay in results:
        # Extract assay ID
        assay_id = assay.get("assay_id")
        if not assay_id:
            continue

        # Extract standard values (logPapp)
        standard_value = None
        if "standard_values" in assay:
            for sv in assay["standard_values"]:
                if sv.get("standard_type") == "LOGPAPP":
                    try:
                        standard_value = float(sv.get("standard_value"))
                        break
                    except (ValueError, TypeError):
                        continue

        # Extract structure SMILES
        structure_smiles = None
        if "molecule_structures" in assay:
            for ms in assay["molecule_structures"]:
                if ms.get("standard_type") == "SMILES":
                    structure_smiles = ms.get("smiles")
                    break

        # Only include if we have both SMILES and logPapp
        if structure_smiles and standard_value is not None:
            records.append({
                "assay_id": str(assay_id),
                "smiles": structure_smiles,
                "logPapp": standard_value,
                "molecule_chembl_id": assay.get("molecule_chembl_id"),
                "assay_description": assay.get("assay_description", ""),
                "cell_type_chembl_id": assay.get("cell_type_chembl_id"),
                "tissue_chembl_id": assay.get("tissue_chembl_id")
            })

    return records


def fetch_all_caco2_data() -> List[Dict[str, Any]]:
    """
    Fetch Caco-2 assay data from ChEMBL until minimum record count reached.

    Returns:
        List of all extracted records.
    """
    all_records = []
    page = 0

    while len(all_records) < MIN_RECORDS:
        response = fetch_assay_page(page)
        if not response:
            if page == 0:
                raise RuntimeError("Failed to fetch initial data from ChEMBL")
            break

        records = extract_records(response)
        all_records.extend(records)
        logger.info(f"Page {page}: fetched {len(records)} records. Total: {len(all_records)}")

        # Check if we have more pages
        if "count" in response and len(all_records) >= response["count"]:
            break

        # Check if there are more results
        if not records and page > 0:
            break

        page += 1

    if len(all_records) < MIN_RECORDS:
        logger.warning(f"Only fetched {len(all_records)} records (minimum: {MIN_RECORDS})")

    return all_records


def write_raw_data(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write raw records to CSV file.

    Args:
        records: List of record dictionaries.
        output_path: Path to output CSV file.
    """
    if not records:
        raise ValueError("No records to write")

    output_file = Path(get_project_root()) / output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "assay_id", "smiles", "logPapp", "molecule_chembl_id",
        "assay_description", "cell_type_chembl_id", "tissue_chembl_id"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_file}")


def main() -> None:
    """
    Main entry point for data retrieval.

    Fetches Caco-2 data, writes to CSV, and registers checksum.
    """
    configure_root_logger()
    logger.info("Starting Caco-2 data retrieval")

    try:
        # Fetch data
        records = fetch_all_caco2_data()
        logger.info(f"Total records fetched: {len(records)}")

        # Write to CSV
        write_raw_data(records, RAW_DATA_PATH)

        # Register checksum
        state_path = Path(get_project_root()) / STATE_FILE_PATH
        data_path = Path(get_project_root()) / RAW_DATA_PATH

        if not data_path.exists():
            raise FileNotFoundError(f"Output file not found: {data_path}")

        register_checksum(
            file_path=str(data_path),
            state_file=str(state_path),
            artifact_key="raw_caco2_data"
        )
        logger.info("Checksum registered successfully")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise


if __name__ == "__main__":
    main()