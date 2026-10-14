"""
verify_data_source.py

This script queries public repositories (Zenodo, NIST, Materials Project) for
datasets that contain all required variables for the adhesion strength
prediction project. It writes a JSON report listing datasets that satisfy the
column requirements. If no dataset satisfies the requirement, the script logs
an error but exits with status 0 so that downstream CI can decide how to handle
the situation.
"""

import sys
import json
import logging
from pathlib import Path

import requests
import pandas as pd

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

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _log_setup() -> logging.Logger:
    """Configure and return a logger."""
    log = get_logger(__name__)
    log.setLevel(logging.INFO)
    return log

LOG = _log_setup()

def _fetch_zenodo_records(query: str = "adhesion strength polymer", size: int = 20):
    """
    Query Zenodo's public API for records matching the query string.

    Returns a list of record dictionaries (each representing a Zenodo record).
    """
    url = "https://zenodo.org/api/records"
    params = {"q": query, "size": size, "sort": "mostviewed"}
    LOG.info("Querying Zenodo API: %s", url)
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Zenodo nests records under data['hits']['hits']
        records = data.get("hits", {}).get("hits", [])
        LOG.info("Found %d Zenodo records", len(records))
        return records
    except Exception as e:
        LOG.error("Failed to query Zenodo API: %s", e)
        return []

def _download_csv_header(file_url: str, max_bytes: int = 1024 * 64):
    """
    Download only the first few bytes of a CSV file and return its column names.

    Parameters
    ----------
    file_url: str
        Direct URL to the CSV file.
    max_bytes: int
        Maximum number of bytes to download (default 64 KiB).

    Returns
    -------
    List[str] | None
        List of column names if parsing succeeds, otherwise None.
    """
    LOG.info("Downloading CSV header from %s", file_url)
    headers = {"Range": f"bytes=0-{max_bytes - 1}"}
    try:
        resp = requests.get(file_url, headers=headers, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(pd.io.common.BytesIO(resp.content), nrows=0)
        return list(df.columns)
    except Exception as e:
        LOG.warning("Failed to parse CSV header from %s: %s", file_url, e)
        return None

def _check_columns(columns):
    """Return True if the required set is a subset of the provided columns."""
    if columns is None:
        return False
    col_set = set(col.strip().lower() for col in columns)
    missing = REQUIRED_COLUMNS - col_set
    if missing:
        LOG.debug("Missing columns: %s", missing)
        return False
    return True

def _process_zenodo():
    """
    Process Zenodo records, returning a list of dataset descriptors that
    contain all required columns.
    """
    matching = []
    records = _fetch_zenodo_records()
    for rec in records:
        # Each record is a dict; ensure we have the expected structure.
        files = rec.get("files", [])
        csv_files = [f for f in files if f.get("key", "").lower().endswith(".csv")]
        if not csv_files:
            continue
        # Try the first CSV file
        file_meta = csv_files[0]
        file_url = file_meta.get("links", {}).get("self")
        if not file_url:
            continue
        cols = _download_csv_header(file_url)
        if _check_columns(cols):
            matching.append(
                {
                    "source": "zenodo",
                    "record_id": rec.get("id"),
                    "doi": rec.get("doi"),
                    "title": rec.get("metadata", {}).get("title"),
                    "url": file_url,
                }
            )
    return matching

def _process_nist():
    """
    Placeholder for NIST data portal query.

    The NIST Materials Data Repository does not provide a simple public
    search API without authentication. For the purpose of this feasibility
    check we attempt to fetch a known example CSV that is publicly reachable.
    If the URL is invalid or the content does not satisfy the column check,
    the function simply returns an empty list.
    """
    example_url = "https://materialsdata.nist.gov/tdb/v1/records/1/files/adhesion_data.csv"
    try:
        cols = _download_csv_header(example_url)
        if _check_columns(cols):
            return [
                {
                    "source": "nist",
                    "record_id": "example-1",
                    "doi": None,
                    "title": "NIST Adhesion Strength Dataset (example)",
                    "url": example_url,
                }
            ]
    except Exception as e:
        LOG.info("NIST example fetch failed: %s", e)
    return []

def _process_materials_project():
    """
    Materials Project requires an API key; without one we cannot query.
    This function therefore returns an empty list but is kept for future
    extension.
    """
    LOG.info("Materials Project query skipped (API key not configured).")
    return []

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main():
    LOG.info("Starting data source verification...")
    candidates = []

    # Zenodo
    try:
        zenodo_matches = _process_zenodo()
        LOG.info("Zenodo matches found: %d", len(zenodo_matches))
        candidates.extend(zenodo_matches)
    except Exception as e:
        LOG.error("Error processing Zenodo records: %s", e)

    # NIST
    try:
        nist_matches = _process_nist()
        LOG.info("NIST matches found: %d", len(nist_matches))
        candidates.extend(nist_matches)
    except Exception as e:
        LOG.error("Error processing NIST records: %s", e)

    # Materials Project
    try:
        mp_matches = _process_materials_project()
        LOG.info("Materials Project matches found: %d", len(mp_matches))
        candidates.extend(mp_matches)
    except Exception as e:
        LOG.error("Error processing Materials Project records: %s", e)

    # Write JSON report
    report_path = paths.data("source", "availability_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_content = {"datasets": candidates}
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_content, f, indent=2, sort_keys=True)
    LOG.info("Availability report written to %s", report_path)

    if not candidates:
        LOG.error(
            "No publicly downloadable dataset contains all required variables. "
            "Pipeline will continue, but downstream steps may need a manual dataset."
        )
    else:
        LOG.info("At least one suitable dataset found. Verification succeeded.")

    # Exit with status 0 regardless; downstream logic can decide how to handle emptiness.
    sys.exit(0)

if __name__ == "__main__":
    main()
