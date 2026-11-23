"""
download.py
-------------
Discover, verify, and download a real paired microbiome‑serology dataset.

This script attempts to locate an open‑access dataset that contains both
16S OTU abundances and influenza serology measurements.  The primary
source is the Hugging‑Face Hub dataset named ``influenza_microbiome``.
If the dataset cannot be accessed or does not contain the required
columns, the script raises a ``RuntimeError`` – there is no silent
fallback to synthetic data.

When a suitable dataset is found, the script downloads the OTU table
and serology metadata files, verifies that they are non‑empty, computes
a SHA‑256 checksum for each (logged for audit), and writes them to
``data/raw/otutable.csv`` and ``data/raw/serology.csv`` respectively.

The result of the discovery step is also written to
``data/research/sra_status.json`` with the schema:

{
    "status": "real_data_found" | "no_real_data",
    "use_synthetic": bool,
    "accession": <NCBI SRA accession string | null>,
    "hf_dataset_id": <HuggingFace dataset identifier | null>
}

The verification step in ``tasks.md`` checks that the keys
``status`` and ``use_synthetic`` exist, and that the two raw CSV files
are present and non‑empty.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
import requests
from datasets import load_dataset  # huggingface datasets library

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

def _download_file(url: str, dest_path: Path) -> None:
    """
    Download the full contents of ``url`` to ``dest_path``.
    Raises ``RuntimeError`` on any failure.
    """
    try:
        logger.info("Downloading %s → %s", url, dest_path)
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as exc:
        logger.error("Failed to download %s: %s", url, exc)
        raise RuntimeError(f"Download failed for {url}") from exc

def _compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

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

    # Use the datasets library to stream a small sample and inspect columns
    try:
        logger.info("Loading HF dataset via `datasets` library for column inspection.")
        ds = load_dataset(HF_DATASET_ID, split="train", streaming=True)
    except Exception as exc:
        logger.error("Failed to load HF dataset via `datasets`: %s", exc)
        raise RuntimeError("Unable to load HF dataset") from exc

    # Grab the first record to infer columns
    try:
        first_record = next(iter(ds))
    except StopIteration:
        raise RuntimeError("HF dataset is empty.")

    sample_columns = list(first_record.keys())
    logger.debug("Sample columns from HF dataset: %s", sample_columns)

    if not dataset_has_required_columns(sample_columns):
        raise RuntimeError(
            f"HF dataset '{HF_DATASET_ID}' does not contain required columns or taxon prefix."
        )

    logger.info("HF dataset '%s' verified successfully.", HF_DATASET_ID)
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": None,
        "hf_dataset_id": HF_DATASET_ID,
    }

def _select_otu_and_serology(columns: List[str]) -> Tuple[List[str], List[str]]:
    """
    Given a list of column names, return two lists:
    - OTU columns (subject_id + all taxon columns)
    - Serology columns (subject_id + required serology columns)
    """
    otu_cols = ["subject_id"] + [c for c in columns if c.startswith(TAXON_PREFIX)]
    sero_cols = ["subject_id"] + [c for c in REQUIRED_COLUMNS if c != "subject_id"]
    return otu_cols, sero_cols

def download_full_dataset_and_write() -> None:
    """
    Streams the full HF dataset, splits into OTU and serology CSVs, and writes them.
    """
    logger.info("Streaming full HF dataset for download.")
    ds = load_dataset(HF_DATASET_ID, split="train", streaming=True)

    # Determine column groups from the first record
    first_record = next(iter(ds))
    all_columns = list(first_record.keys())
    otu_cols, sero_cols = _select_otu_and_serology(all_columns)

    # Prepare data containers (write incrementally to avoid memory issues)
    otutable_path = paths.data("raw", "otutable.csv")
    serology_path = paths.data("raw", "serology.csv")

    # Write headers
    otutable_path.parent.mkdir(parents=True, exist_ok=True)
    serology_path.parent.mkdir(parents=True, exist_ok=True)

    with open(otutable_path, "w", encoding="utf-8") as otu_f, \
         open(serology_path, "w", encoding="utf-8") as sero_f:
        otu_f.write(",".join(otu_cols) + "\n")
        sero_f.write(",".join(sero_cols) + "\n")

        # Write the first record
        otu_f.write(",".join(str(first_record.get(col, "")) for col in otu_cols) + "\n")
        sero_f.write(",".join(str(first_record.get(col, "")) for col in sero_cols) + "\n")

        # Stream remaining records
        for record in ds:
            # Skip the first record already written
            if record is first_record:
                continue
            otu_f.write(",".join(str(record.get(col, "")) for col in otu_cols) + "\n")
            sero_f.write(",".join(str(record.get(col, "")) for col in sero_cols) + "\n")

    logger.info("Finished writing OTU table to %s", otutable_path)
    logger.info("Finished writing serology table to %s", serology_path)

    # Verify non‑empty files
    if otutable_path.stat().st_size == 0 or serology_path.stat().st_size == 0:
        raise RuntimeError("Downloaded files are empty after streaming.")

    # Compute and log SHA‑256 checksums.
    otu_checksum = _compute_sha256(otutable_path)
    sero_checksum = _compute_sha256(serology_path)
    logger.info("SHA‑256 OTU table: %s", otu_checksum)
    logger.info("SHA‑256 Serology: %s", sero_checksum)

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
    Entry point for the script.

    1. Discover the HF dataset.
    2. If a real dataset is found, stream it, split into OTU and serology CSVs,
       verify they contain the required columns, compute SHA‑256 checksums,
       and write them to ``data/raw/otutable.csv`` and ``data/raw/serology.csv``.
    3. If any step fails, raise ``RuntimeError`` – no silent fallback.
    """
    try:
        discovery = discover_hf_dataset()
    except Exception as exc:  # noqa: BLE001 (broad on purpose for discovery)
        logger.debug("HF discovery failed: %s", exc, exc_info=True)
        discovery = fallback_to_synthetic()

    # Write the status file regardless of success/failure
    write_status_file(discovery)

    # If we couldn't find real data, abort with a clear error.
    if discovery.get("use_synthetic", True):
        raise RuntimeError("Real dataset not available – cannot download OTU/serology files.")

    # At this point we have a real dataset; download and write CSVs.
    download_full_dataset_and_write()
    logger.info("Successfully downloaded and verified raw data files.")

if __name__ == "__main__":
    # ``python code/download.py`` is the canonical way to run this step.
    # Any exception propagates to the CI runner so that a failure
    # is visible and not silently ignored.
    try:
        main()
    except RuntimeError as e:
        logger.error("Download step failed: %s", e)
        sys.exit(1)
