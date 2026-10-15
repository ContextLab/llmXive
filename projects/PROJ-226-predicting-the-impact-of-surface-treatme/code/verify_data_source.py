"""
Verify that at least one openly downloadable dataset contains all required variables.
This script queries public repositories (Zenodo) to find datasets matching the 
required schema. If no external dataset is found, it raises a RuntimeError to 
abort the pipeline as per the project plan.
"""

import json
import logging
from pathlib import Path
import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
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
    "polymer substrate adhesion plasma"
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _log_setup() -> logging.Logger:
    """Configure and return a logger."""
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)
    return logger

def _check_columns_in_header(header_line: str) -> bool:
    """Return True if the required columns are a subset of the CSV header."""
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
            first_line = response.text.splitlines()[0]
            return _check_columns_in_header(first_line)
    except Exception:
        pass
    return False

def _discover_external_datasets() -> list[dict]:
    """
    Query Zenodo API for datasets and verify their headers.
    """
    logger = get_logger(__name__)
    found_datasets = []

    for query in SEARCH_QUERIES:
        logger.info("Searching Zenodo for: %s", query)
        try:
            params = {"q": query, "type": "dataset", "size": 10}
            resp = requests.get(ZENODO_API_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for record in data.get("hits", []):
                # Check files associated with the record
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
                            # Found one that works, we can stop searching
                            return found_datasets
        except Exception as exc:
            logger.error("Error querying Zenodo for %s: %s", query, exc)

    return found_datasets

def _build_availability_report() -> dict:
    """
    Build the availability report. If no suitable external dataset is found,
    raise a RuntimeError to abort the pipeline.
    """
    external = _discover_external_datasets()
    if external:
        return {"datasets": external}

    # No suitable external dataset found - abort with a clear error.
    # This is the intended behavior when no real data is available.
    raise RuntimeError(
        "No openly downloadable dataset containing all required columns was found. "
        "Please provide a suitable dataset or revise the specification."
    )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the verification workflow and write the availability report.
    """
    logger = _log_setup()
    try:
        report = _build_availability_report()
        report_path = paths.data("source", "availability_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Availability report written to %s", report_path)
    except Exception as exc:
        logger.error("Failed to generate availability report: %s", exc)
        raise

if __name__ == "__main__":
    main()