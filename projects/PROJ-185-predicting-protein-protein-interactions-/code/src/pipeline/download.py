"""
GEO series downloader.

The downloader fetches a GEO Series (GSE) count matrix, records a SHA‑256 checksum,
and writes the checksum to ``state/artifact_hashes.yaml``.  Series with fewer than
30 samples are **skipped**; a warning is emitted to the pipeline log and processing
continues with the remaining series.

Public API:
- build_parser() -> argparse.ArgumentParser
- process_series(series_id: str, args: argparse.Namespace) -> None
- main() -> int (exit code)
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, List

import requests

from src.utils.logger import get_logger, log_error

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
GEO_EUTILS_SUMMARY_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
)
GEO_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series"

def _fetch_series_summary(gse_id: str) -> Dict:
    """
    Retrieve the GEO series summary from NCBI Entrez ESummary.
    Returns the parsed JSON dictionary.
    """
    params = {
        "db": "gds",
        "id": gse_id,
        "retmode": "json",
    }
    response = requests.get(GEO_EUTILS_SUMMARY_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    # The JSON structure is: {"result": {"uids": [...], "GSEXXXXX": {...}}}
    result = data.get("result", {})
    summary = result.get(gse_id)
    if not summary:
        raise ValueError(f"Series {gse_id} not found in ESummary response.")
    return summary

def _sample_count_from_summary(summary: Dict) -> int:
    """
    Extract the sample count from the ESummary dictionary.
    The field is typically ``samplecount``; fall back to ``samples`` length if needed.
    """
    if "samplecount" in summary:
        return int(summary["samplecount"])
    # Some older entries provide a list under ``samples``.
    if "samples" in summary and isinstance(summary["samples"], list):
        return len(summary["samples"])
    raise ValueError("Unable to determine sample count from series summary.")

def _download_series_matrix(gse_id: str, dest_dir: Path) -> Path:
    """
    Download the GEO series matrix file (soft format) and return the local path.
    The matrix is stored under the FTP hierarchy:
    https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnnnnn/GSEXXXXX/matrix/
    """
    # GEO series are grouped in 1000‑series directories, e.g. GSE12345 -> GSE12nnn
    numeric_part = "".join(filter(str.isdigit, gse_id))
    if not numeric_part:
        raise ValueError(f"Invalid GEO series identifier: {gse_id}")

    series_dir = f"GSE{int(numeric_part) // 1000 * 1000:04d}nnn"
    ftp_path = f"{GEO_FTP_BASE}/{series_dir}/{gse_id}/matrix/{gse_id}_series_matrix.txt.gz"
    url = urllib.parse.urljoin(GEO_FTP_BASE + "/", f"{series_dir}/{gse_id}/matrix/{gse_id}_series_matrix.txt.gz")
    dest_path = dest_dir / f"{gse_id}_series_matrix.txt.gz"

    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Stream download to avoid loading whole file into memory
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep‑alive chunks
                    f.write(chunk)
    return dest_path

def _sha256_of_file(path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _record_checksum(gse_id: str, checksum: str) -> None:
    """
    Append (or update) the checksum entry for ``gse_id`` in
    ``state/artifact_hashes.yaml``.  The file is a simple ``key: value`` mapping.
    """
    state_dir = Path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    hash_file = state_dir / "artifact_hashes.yaml"

    # Load existing mapping (if any)
    if hash_file.is_file():
        try:
            with open(hash_file, "r", encoding="utf-8") as f:
                data = json.load(f)  # using JSON syntax; file extension remains .yaml
        except Exception:
            data = {}
    else:
        data = {}

    data[gse_id] = checksum
    # Write back atomically
    tmp_path = hash_file.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    tmp_path.replace(hash_file)

# ----------------------------------------------------------------------
# Core processing
# ----------------------------------------------------------------------
def process_series(gse_id: str, args: argparse.Namespace) -> None:
    """
    Process a single GEO series:

    1. Retrieve the series summary to obtain the sample count.
    2. If the count < 30, emit a warning and skip.
    3. Otherwise, download the series matrix, compute its SHA‑256 checksum,
       and record the checksum in ``state/artifact_hashes.yaml``.
    """
    logger = get_logger()
    try:
        logger.info(f"Processing GEO series {gse_id}")

        summary = _fetch_series_summary(gse_id)
        sample_count = _sample_count_from_summary(summary)
        logger.info(f"Series {gse_id} contains {sample_count} samples")

        if sample_count < 30:
            logger.warning(
                f"Skipping GEO series {gse_id}: only {sample_count} samples (< 30)"
            )
            return

        # Destination directory for downloaded matrices
        out_dir = Path("data") / "geo_matrices"
        matrix_path = _download_series_matrix(gse_id, out_dir)

        checksum = _sha256_of_file(matrix_path)
        _record_checksum(gse_id, checksum)

        logger.info(
            f"Successfully downloaded {gse_id} to {matrix_path} (SHA‑256: {checksum})"
        )
    except Exception as exc:
        # Log the error but do not abort the whole pipeline – continue with next series
        log_error(f"Failed to process GEO series {gse_id}", exc)

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download GEO series count matrices, skipping those with <30 samples."
    )
    parser.add_argument(
        "series",
        nargs="+",
        help="One or more GEO series identifiers (e.g., GSE12345).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (propagated to logger for reproducibility).",
    )
    return parser

def main() -> int:
    """
    Entry point used by the Makefile target ``download``.
    Returns 0 on success, non‑zero on failure.
    """
    parser = build_parser()
    args = parser.parse_args()

    # Record CLI invocation details
    from src.utils.logger import log_cli_invocation

    log_cli_invocation(args)

    for gse_id in args.series:
        process_series(gse_id, args)

    return 0

if __name__ == "__main__":
    sys.exit(main())
