"""
GEO Series Downloader with Sample‑Count Guard

This module implements the ``main`` entry‑point used by the pipeline
(see ``src/pipeline/download.py``).  Its responsibility is to download
count‑matrix files for a list of GEO series identifiers, compute a SHA‑256
checksum for each successfully processed series and record the checksum
in ``state/artifact_hashes.yaml``.  In accordance with task **T043**, any
GEO series that contains fewer than 30 samples is **skipped** – a warning
is emitted to the central ``pipeline.log`` and the series is omitted from
the checksum manifest.

The implementation is deliberately lightweight and relies only on the
packages already declared in ``requirements.txt`` (``requests``,
``pandas``, ``tqdm``, ``pyyaml`` and ``numpy``).  It does **not** fall back
to synthetic data – if a download fails the exception propagates, causing
the pipeline to abort as required by the project policies.
"""

import argparse
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
import yaml
from tqdm import tqdm

# --------------------------------------------------------------------------- #
# Central logger – all warnings / info are written to ``pipeline.log``.
# --------------------------------------------------------------------------- #
from src.utils.logger import get_logger, log_cli_invocation, log_error

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _download_matrix(series_id: str, dest_dir: Path) -> Path:
    """
    Download the GEO Series matrix file for ``series_id``.
    The function follows the standard GEO FTP layout:

        https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnnnnn/GSExxxx/matrix/<file>

    where ``nnn`` are the first three digits of the series number.
    The exact matrix filename is not always predictable; however,
    GEO provides a ``soft`` link called ``GSExxxx_series_matrix.txt.gz``.
    We therefore attempt to download that file.

    Parameters
    ----------
    series_id: str
        GEO series identifier, e.g. ``GSE12345``.
    dest_dir: Path
        Directory where the matrix will be saved.

    Returns
    -------
    Path
        Path to the downloaded (and decompressed) TSV file.

    Raises
    ------
    RuntimeError
        If the file cannot be retrieved.
    """
    # Normalise the identifier
    series_id = series_id.upper()
    if not series_id.startswith("GSE"):
        raise ValueError(f"Invalid GEO series identifier: {series_id}")

    # Derive the FTP path components
    numeric_part = series_id[3:]  # strip 'GSE'
    # Pad with leading zeros to at least 6 digits for the series folder
    padded = numeric_part.zfill(6)
    series_folder = f"GSE{padded[:3]}nnn"
    ftp_base = (
        f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_folder}/{series_id}"
    )
    matrix_url = f"{ftp_base}/matrix/{series_id}_series_matrix.txt.gz"

    response = requests.get(matrix_url, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download matrix for {series_id} (status code {response.status_code})"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    gz_path = dest_dir / f"{series_id}_matrix.txt.gz"
    with open(gz_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Decompress
    import gzip

    tsv_path = dest_dir / f"{series_id}_matrix.txt"
    with gzip.open(gz_path, "rt") as gz_in, open(tsv_path, "w") as out_f:
        for line in gz_in:
            out_f.write(line)

    # Remove the compressed file to keep the workspace tidy
    gz_path.unlink(missing_ok=True)

    return tsv_path

def _count_samples(matrix_path: Path) -> int:
    """
    Count the number of sample columns in a GEO matrix file.

    GEO matrix files have the first column as the probe/gene identifier,
    the remaining columns correspond to samples.  This function loads only
    the header line to avoid unnecessary memory consumption.

    Parameters
    ----------
    matrix_path: Path
        Path to the decompressed matrix TSV file.

    Returns
    -------
    int
        Number of samples (i.e. number of columns minus one).
    """
    with open(matrix_path, "r") as f:
        header = f.readline().strip()
    # GEO headers are tab‑separated; the first field is the identifier column.
    fields = header.split("\t")
    # Guard against malformed files
    if len(fields) <= 1:
        raise RuntimeError(f"Matrix file {matrix_path} appears to have no sample columns.")
    return len(fields) - 1

def _sha256_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _load_existing_hashes(hash_file: Path) -> Dict[str, str]:
    """
    Load the existing artifact hash manifest (YAML).  Returns an empty dict
    if the file does not exist.
    """
    if not hash_file.is_file():
        return {}
    with open(hash_file, "r") as f:
        data = yaml.safe_load(f) or {}
    return data

def _save_hashes(hash_file: Path, hashes: Dict[str, str]) -> None:
    """
    Persist ``hashes`` (mapping series_id → checksum) to ``hash_file``.
    """
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    with open(hash_file, "w") as f:
        yaml.safe_dump(hashes, f)

# --------------------------------------------------------------------------- #
# Core workflow
# --------------------------------------------------------------------------- #
def process_series(series_id: str, out_dir: Path, hash_manifest: Path) -> None:
    """
    Process a single GEO series:

    1. Download the matrix.
    2. Count the samples.
    3. If ``samples >= 30`` → record checksum; otherwise log a warning and
       delete the matrix file.

    Parameters
    ----------
    series_id: str
        GEO series identifier.
    out_dir: Path
        Directory where matrix files are stored.
    hash_manifest: Path
        Path to ``state/artifact_hashes.yaml``.
    """
    try:
        matrix_path = _download_matrix(series_id, out_dir)
    except Exception as exc:
        # Propagate download errors – the pipeline must fail loudly.
        log_error(logger, f"Download failed for {series_id}: {exc}")
        raise

    try:
        n_samples = _count_samples(matrix_path)
    except Exception as exc:
        log_error(logger, f"Failed to count samples for {series_id}: {exc}")
        # Clean up the possibly corrupted file before re‑raising.
        matrix_path.unlink(missing_ok=True)
        raise

    if n_samples < 30:
        logger.warning(
            f"Skipping GEO series {series_id} – only {n_samples} samples (<30)."
        )
        # Remove the matrix because it should not be used downstream.
        matrix_path.unlink(missing_ok=True)
        return

    # Compute and persist checksum
    checksum = _sha256_checksum(matrix_path)
    existing = _load_existing_hashes(hash_manifest)
    existing[series_id] = checksum
    _save_hashes(hash_manifest, existing)
    logger.info(f"Processed {series_id}: {n_samples} samples, checksum {checksum[:8]}...")

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download GEO series count matrices and record SHA‑256 checksums. "
        "Series with fewer than 30 samples are automatically skipped."
    )
    parser.add_argument(
        "series_ids",
        nargs="+",
        help="One or more GEO series identifiers (e.g. GSE12345).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/raw_geo"),
        help="Directory to store downloaded matrix files (default: data/raw_geo).",
    )
    parser.add_argument(
        "--hash-manifest",
        type=Path,
        default=Path("state/artifact_hashes.yaml"),
        help="YAML file that maps series IDs to SHA‑256 checksums.",
    )
    return parser

def main() -> None:
    """
    Entry point used by the Makefile and CI.  It parses CLI arguments,
    records the invocation in the central log, and iterates over the
    supplied series identifiers invoking :func:`process_series`.
    """
    parser = build_parser()
    args = parser.parse_args()

    # Log the CLI invocation for reproducibility (timestamp, args, etc.)
    log_cli_invocation(logger, sys.argv)

    out_dir: Path = args.out_dir
    hash_manifest: Path = args.hash_manifest

    for series_id in args.series_ids:
        try:
            process_series(series_id, out_dir, hash_manifest)
        except Exception as exc:
            # Any exception is fatal – we log it and abort the whole run.
            log_error(logger, f"Aborting due to error processing {series_id}: {exc}")
            raise

if __name__ == "__main__":
    main()