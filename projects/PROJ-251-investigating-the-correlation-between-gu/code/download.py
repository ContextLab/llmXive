"""
download.py
-------------
Discover and verify a real paired microbiome‑serology dataset.

This script attempts to locate an open‑access dataset that contains both
16S OTU abundances and influenza serology measurements.  The primary
source is the Hugging‑Face Hub dataset named ``influenza_microbiome``.
If the dataset cannot be accessed or does not contain the required
columns, the script falls back to a synthetic‑data flag.

The result is written to ``data/research/sra_status.json`` with the
following schema:

{
    "status": "real_data_found" | "no_real_data",
    "use_synthetic": bool,
    "accession": <NCBI SRA accession string | null>,
    "hf_dataset_id": <HuggingFace dataset identifier | null>
}

The verification step in ``tasks.md`` only checks that the keys
``status`` and ``use_synthetic`` exist, but we also include the optional
identifiers for downstream scripts.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import requests

# llmxive toolkit helpers for consistent path handling
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {"subject_id", "titer_baseline", "titer_post"}
TAXON_PREFIX = "taxon_"                     # any column starting with this is considered a taxon
HF_DATASET_ID = "influenza_microbiome"
HF_API_URL = "https://huggingface.co/api/datasets"
HF_RAW_URL_TEMPLATE = "https://huggingface.co/datasets/{repo_id}/resolve/main/{filename}"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _hf_dataset_exists(repo_id: str) -> bool:
    """Check via the Hugging‑Face Hub API whether a dataset repo exists."""
    url = f"{HF_API_URL}/{repo_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            logger.debug("HF dataset %s exists (status 200).", repo_id)
            return True
        logger.debug("HF dataset %s not found (status %s).", repo_id, resp.status_code)
        return False
    except requests.RequestException as exc:
        logger.error("Error contacting Hugging‑Face API: %s", exc)
        raise RuntimeError("Failed to query Hugging‑Face API") from exc

def _list_dataset_files(repo_id: str) -> List[str]:
    """
    Return a list of file paths (relative to the repo root) for the given dataset.
    Uses the ``/tree`` endpoint of the HF API.
    """
    url = f"{HF_API_URL}/{repo_id}/tree/main"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # The JSON is a list of dicts with a ``type`` and ``path`` key.
        files = [entry["path"] for entry in data if entry.get("type") == "file"]
        logger.debug("Found %d files in HF dataset %s.", len(files), repo_id)
        return files
    except requests.RequestException as exc:
        logger.error("Failed to list files for HF dataset %s: %s", repo_id, exc)
        raise RuntimeError("Failed to list HF dataset files") from exc

def _download_file_sample(repo_id: str, filename: str, max_bytes: int = 8192) -> bytes:
    """
    Download the first ``max_bytes`` of a file from the HF dataset.
    This is sufficient to read the header line of a CSV without pulling the whole file.
    """
    raw_url = HF_RAW_URL_TEMPLATE.format(repo_id=repo_id, filename=filename)
    try:
        resp = requests.get(raw_url, stream=True, timeout=15)
        resp.raise_for_status()
        chunk = resp.raw.read(max_bytes)
        logger.debug("Downloaded %d bytes from %s.", len(chunk), raw_url)
        return chunk
    except requests.RequestException as exc:
        logger.error("Error downloading %s: %s", raw_url, exc)
        raise RuntimeError(f"Failed to download sample of {filename}") from exc

def _extract_header(csv_bytes: bytes) -> List[str]:
    """
    Decode the first line of a CSV byte stream and split into column names.
    Assumes UTF‑8 encoding.
    """
    try:
        text = csv_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.error("Failed to decode CSV bytes: %s", exc)
        raise RuntimeError("Unable to decode CSV sample") from exc
    first_line = text.splitlines()[0]
    columns = [col.strip() for col in first_line.split(",")]
    logger.debug("Extracted header columns: %s", columns)
    return columns

def dataset_has_required_columns(sample_columns: List[str]) -> bool:
    """
    Verify that a CSV file contains the mandatory columns and at least one taxon column.
    """
    if not REQUIRED_COLUMNS.issubset(set(sample_columns)):
        logger.debug(
            "Missing mandatory columns. Required=%s, present=%s",
            REQUIRED_COLUMNS,
            sample_columns,
        )
        return False

    taxon_cols = [c for c in sample_columns if c.startswith(TAXON_PREFIX)]
    if not taxon_cols:
        logger.debug("No taxon columns found with prefix %s", TAXON_PREFIX)
        return False

    return True

def discover_hf_dataset() -> dict:
    """
    Attempt to locate and minimally validate the Hugging‑Face dataset.
    Returns a discovery dictionary on success, otherwise raises.
    """
    logger.info("Attempting to discover HF dataset '%s'.", HF_DATASET_ID)

    if not _hf_dataset_exists(HF_DATASET_ID):
        raise RuntimeError(f"Hugging‑Face dataset '{HF_DATASET_ID}' not found.")

    files = _list_dataset_files(HF_DATASET_ID)

    # Prefer CSV files; any other format would need additional parsing.
    csv_files = [f for f in files if f.lower().endswith(".csv")]
    if not csv_files:
        raise RuntimeError("No CSV files found in the HF dataset.")

    # Examine the first CSV file (could be improved to iterate).
    candidate = csv_files[0]
    logger.info("Inspecting CSV file '%s' for required columns.", candidate)

    sample_bytes = _download_file_sample(HF_DATASET_ID, candidate, max_bytes=65536)
    header_cols = _extract_header(sample_bytes)

    if not dataset_has_required_columns(header_cols):
        raise RuntimeError(
            f"CSV '{candidate}' does not contain required columns or taxon prefix."
        )

    logger.info("HF dataset '%s' verified successfully.", HF_DATASET_ID)
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": None,
        "hf_dataset_id": HF_DATASET_ID,
    }

def fallback_to_synthetic() -> dict:
    """
    Return a minimal status dict indicating that no suitable real dataset
    could be located; downstream pipelines will switch to synthetic mode.
    """
    logger.warning(
        "No suitable real paired microbiome‑serology dataset found. "
        "Falling back to synthetic data."
    )
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "accession": None,
        "hf_dataset_id": None,
    }

def write_status_file(status_dict: dict) -> None:
    """
    Write the discovery result to ``data/research/sra_status.json``.
    The directory hierarchy is created automatically by ``paths.data``.
    """
    out_path = paths.data("research", "sra_status.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the JSON is pretty‑printed for readability.
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(status_dict, fp, indent=2, sort_keys=True)

    logger.info("Wrote discovery status to %s", out_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the script.  It first tries the HF dataset; if any step
    fails, it records a synthetic‑fallback status.
    """
    try:
        status = discover_hf_dataset()
    except Exception as exc:  # noqa: BLE001 (broad on purpose for discovery)
        logger.debug("HF discovery failed: %s", exc, exc_info=True)
        status = fallback_to_synthetic()

    write_status_file(status)

if __name__ == "__main__":
    # ``python code/download.py`` is the canonical way to run this step.
    # Any exception propagates to the caller (CI runner) so that a failure
    # is visible and not silently ignored.
    main()
