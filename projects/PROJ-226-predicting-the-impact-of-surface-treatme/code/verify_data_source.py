"""
Verify that at least one openly downloadable dataset contains all required variables.
This script queries public repositories (Zenodo) to find datasets matching the 
required schema. If no external dataset is found, it writes an empty report and 
raises a RuntimeError/sys.exit(1) to abort the pipeline as per the project plan.
"""

import json
import logging
import sys
from pathlib import Path
import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The set of variables that MUST be present in the dataset to satisfy T001.
REQUIRED_COLUMNS = {
    "plasma_power_w",
    "exposure_time_s",
    "chemical_concentration_pct",
    "polymer_surface_energy",
    "substrate_roughness_nm",
    "adhesion_strength_mj_m2",
    "treatment_type",
    "pair_id",
}

ZENODO_API_URL = "https://zenodo.org/api/records"
SEARCH_QUERIES = [
    "polymer adhesion surface treatment",
    "plasma treatment adhesion strength",
    "polymer substrate adhesion plasma",
    "interfacial adhesion strength polymers",
    "surface treatment polymers CSV"
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _log_setup() -> logging.Logger:
    """Configure and return a logger."""
    return get_logger(__name__)

def _check_columns_in_header(header_line: str) -> bool:
    """Return True if the required columns are a subset of the CSV header."""
    if not header_line:
        return False
    columns = set(col.strip() for col in header_line.split(","))
    return REQUIRED_COLUMNS.issubset(columns)

def _verify_csv_url(url: str) -> bool:
    """
    Fetch only the first line of a CSV from a URL to check if it contains 
    the required columns.
    """
    try:
        # Use a Range request to get only the first 1024 bytes (header)
        headers = {"Range": "bytes=0-1023"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code in (200, 206):
            lines = response.text.splitlines()
            if lines:
                return _check_columns_in_header(lines[0])
    except Exception:
        pass
    return False

def _discover_external_datasets() -> list[dict]:
    """
    Query Zenodo API for datasets and verify their headers.
    """
    logger = _log_setup()
    found_datasets = []

    for query in SEARCH_QUERIES:
        logger.info("Searching Zenodo for: %s", query)
        try:
            params = {"q": query, "type": "dataset", "size": 20}
            resp = requests.get(ZENODO_API_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for record in data.get("hits", []):
                files = record.get("files", [])
                for file_info in files:
                    if file_info.get("key", "").endswith(".csv"):
                        download_url = file_info.get("links", {}).get("download")
                        if download_url and _verify_csv_url(download_url):
                            logger.info("Found matching dataset: %s", download_url)
                            found_datasets.append({
                                "url": download_url,
                                "source_name": record.get("title", "unknown_zenodo_source"),
                                "description": record.get("description", "Public Zenodo dataset."),
                            })
                            # Return immediately upon finding the first valid source to satisfy T001
                            return found_datasets
        except Exception as exc:
            logger.error("Error querying Zenodo for %s: %s", query, exc)

    return found_datasets

def main() -> None:
    """
    Execute the verification workflow and write the availability report.
    If no suitable external dataset is found, exit with status 1 to abort the pipeline.
    """
    logger = _log_setup()
    
    # 1. Search for real external data
    external_datasets = _discover_external_datasets()
    
    # 2. Build and write the report (REQUIRED output artifact)
    # We write the report regardless of whether datasets were found.
    report = {"datasets": external_datasets}
    report_path = paths.data("source", "availability_report.json")
    
    try:
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Availability report written to %s", report_path)
    except Exception as exc:
        logger.error("Failed to write availability report: %s", exc)
        sys.exit(1)

    # 3. Final verification check
    if not external_datasets:
        # As per plan.md and tasks.md, if no real data is found, we abort.
        # This is a "loud failure" to prevent downstream fabrication.
        logger.error(
            "CRITICAL: No openly downloadable dataset containing all required columns was found. "
            "The pipeline cannot proceed without real data. "
            "Please provide a suitable dataset or revise the specification."
        )
        sys.exit(1)
    
    logger.info("Verification successful. Found %d suitable dataset(s).", len(external_datasets))

if __name__ == "__main__":
    main()