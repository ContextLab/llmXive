"""
Data Retrieval Module for Caco‑2 Permeability Dataset.

This script fetches ≥ 600 Caco‑2 assay records from the ChEMBL REST API,
extracts the required fields, writes them to
``data/raw/chembl_caco2_raw.csv`` (conforming to ``dataset.schema.yaml``),
and finally registers the new file in the checksum registry.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root
from utils.checksum import run_checksum_utility

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
ASSAY_TYPE = "Caco-2"
STANDARD_TYPE = "MEASUREMENT"
MAX_RETRIES = 3
INITIAL_DELAY = 5  # seconds
MAX_DELAY = 60  # seconds
PAGE_LIMIT = 1000  # maximum records per API request

logger = get_logger(__name__)
configure_root_logger()


def _fetch_page(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch a single page from the ChEMBL API with exponential back‑off.

    Parameters
    ----------
    url: str
        Full API endpoint.
    params: dict | None
        Query parameters.

    Returns
    -------
    dict
        Parsed JSON response.

    Raises
    ------
    RuntimeError
        If all retry attempts fail.
    """
    delay = INITIAL_DELAY
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Requesting {url} (attempt {attempt}/{MAX_RETRIES})")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status in (429, 503, 504):
                last_error = e
                logger.warning(
                    f"Rate limit / server error (HTTP {status}). Retrying in {delay}s..."
                )
            else:
                logger.error(f"Unrecoverable HTTP error {status}: {e}")
                raise
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Network problem: {e}. Retrying in {delay}s...")

        time.sleep(delay)
        delay = min(delay * 2, MAX_DELAY)

    raise RuntimeError(
        f"Failed to fetch data after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


def _extract_records(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a page of ChEMBL ``activity`` results into the flat record format
    required downstream.

    Only records that contain a canonical SMILES string and a non‑null
    ``standard_value`` (the permeability measurement) are kept.

    Parameters
    ----------
    page_data: dict
        JSON payload from the ``activity`` endpoint.

    Returns
    -------
    list[dict]
        List of cleaned record dictionaries.
    """
    records: List[Dict[str, Any]] = []

    activities = page_data.get("activities", [])
    for act in activities:
        # Basic filter on assay type and standard type (already applied at request level,
        # but we keep a defensive check)
        if act.get("assay_type") != ASSAY_TYPE:
            continue
        if act.get("standard_type") != STANDARD_TYPE:
            continue

        molecule_struct = act.get("molecule_structures", {})
        smiles = molecule_struct.get("canonical_smiles")
        mw = molecule_struct.get("molecular_weight")
        psa = molecule_struct.get("polar_surface_area")

        # ``standard_value`` holds the permeability measurement (logPapp)
        logpapp = act.get("standard_value")

        if not smiles or logpapp is None:
            continue

        record = {
            "smiles": smiles,
            "logPapp": logpapp,
            "mw": mw,
            "psa": psa,
            "assay_id": act.get("assay_chembl_id"),
            "protocol_metadata": {
                "standard_type": act.get("standard_type"),
                "standard_units": act.get("standard_units"),
                "assay_description": act.get("assay_description"),
                "cell_line": act.get("cell_line_chembl_id"),
                "tissue": act.get("tissue_chembl_id"),
            },
        }
        records.append(record)

    return records


def fetch_all_caco2_data() -> List[Dict[str, Any]]:
    """
    Retrieve the full Caco‑2 dataset using pagination.

    Returns
    -------
    list[dict]
        All extracted records across all pages.
    """
    all_records: List[Dict[str, Any]] = []
    endpoint = f"{CHEMBL_API_BASE}/activity.json"
    offset = 0

    while True:
        params = {
            "assay_type": ASSAY_TYPE,
            "standard_type": STANDARD_TYPE,
            "limit": PAGE_LIMIT,
            "offset": offset,
        }
        page = _fetch_page(endpoint, params)
        page_records = _extract_records(page)
        all_records.extend(page_records)

        logger.info(
            f"Fetched page starting at offset {offset}: {len(page_records)} new records "
            f"(total so far: {len(all_records)})"
        )

        # Pagination control – ``page`` contains a ``page_meta`` dict with ``next``
        # indicator. If fewer than PAGE_LIMIT records were returned we are at the end.
        if len(page_records) < PAGE_LIMIT:
            break

        offset += PAGE_LIMIT

    return all_records


def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Persist the list of records to a CSV file.

    Parameters
    ----------
    records: list[dict]
        Extracted assay records.
    output_path: pathlib.Path
        Destination CSV file.
    """
    if not records:
        logger.warning("No records to write – the retrieved dataset is empty.")
        return

    fieldnames = [
        "smiles",
        "logPapp",
        "mw",
        "psa",
        "assay_id",
        "protocol_metadata",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = rec.copy()
            # ``protocol_metadata`` must be stored as a JSON string for later parsing.
            row["protocol_metadata"] = json.dumps(row["protocol_metadata"])
            writer.writerow(row)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def invoke_checksum_utility() -> None:
    """
    Register newly created data files in ``state/pending/checksums.yaml``.
    """
    logger.info("Running checksum utility...")
    run_checksum_utility()
    logger.info("Checksum registration completed.")


def main() -> None:
    """
    Orchestrate the full retrieval → write → checksum workflow.
    """
    logger.info("Starting Caco‑2 data retrieval pipeline.")

    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "chembl_caco2_raw.csv"

    # ------------------------------------------------------------------
    # 1. Fetch data from ChEMBL
    # ------------------------------------------------------------------
    records = fetch_all_caco2_data()

    if len(records) < 600:
        logger.warning(
            f"Retrieved only {len(records)} records; expected at least 600. "
            "Proceeding with whatever was obtained."
        )
    else:
        logger.info(f"Successfully retrieved {len(records)} Caco‑2 records.")

    # ------------------------------------------------------------------
    # 2. Write CSV
    # ------------------------------------------------------------------
    write_raw_data(records, output_path)

    # ------------------------------------------------------------------
    # 3. Register checksum
    # ------------------------------------------------------------------
    invoke_checksum_utility()

    logger.info("Caco‑2 data retrieval pipeline completed.")


if __name__ == "__main__":
    sys.exit(main())