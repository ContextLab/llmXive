"""Verification script for the PPMI dataset provenance.

This module checks that the required raw input files exist, validates their
SHA‑256 checksums against the expected values recorded in the PPMI
publication, and confirms that the citation URL is reachable.

The script can be invoked directly via

    python -m src.pipeline.verify_dataset [--asv <path>] [--clinical <path>]

If any check fails, a descriptive exception is raised and the process exits
with a non‑zero status code.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Tuple

import requests
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Expected SHA‑256 digests.
#
# In a real deployment these would be the digests published alongside the
# PPMI dataset.  For the purpose of the unit tests they are overwritten
# (monkey‑patched) with the correct values computed from temporary files.
# ----------------------------------------------------------------------
EXPECTED_ASV_SHA256: str = "PLACEHOLDER_ASV_SHA256"
EXPECTED_CLINICAL_SHA256: str = "PLACEHOLDER_CLINICAL_SHA256"

# A DOI that resolves to the PPMI dataset description.  The URL is checked
# with a simple HEAD request; a 2xx status is considered reachable.
CITATION_URL: str = "https://doi.org/10.1002/mds.27908"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _hash_file(path: Path, chunk_size: int = 8192) -> str:
    """Compute the SHA‑256 hash of *path*.

    Parameters
    ----------
    path: Path
        File to hash.
    chunk_size: int, optional
        Number of bytes to read per iteration.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 digest.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _verify_checksum(path: Path, expected: str, label: str) -> None:
    """Validate the SHA‑256 checksum of *path* against *expected*.

    Raises
    ------
    ValueError
        If the computed checksum does not match the expected one.
    """
    computed = _hash_file(path)
    if computed.lower() != expected.lower():
        raise ValueError(
            f"{label} checksum mismatch: expected {expected}, got {computed}"
        )
    log.info("%s checksum verified (%s).", label, computed)

def _check_citation(url: str = CITATION_URL, timeout: int = 10) -> None:
    """Confirm that *url* is reachable (HTTP 2xx).

    Raises
    ------
    ConnectionError
        If the request fails or returns a non‑2xx status.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        if not (200 <= response.status_code < 300):
            raise ConnectionError(
                f"Citation URL returned unexpected status {response.status_code}"
            )
    except requests.RequestException as exc:
        raise ConnectionError(f"Unable to reach citation URL: {exc}") from exc
    log.info("Citation URL %s is reachable (status %s).", url, response.status_code)

# ----------------------------------------------------------------------
# Core verification routine
# ----------------------------------------------------------------------
def verify_dataset(
    asv_path: Path | None = None,
    clinical_path: Path | None = None,
    expected_asv: str = EXPECTED_ASV_SHA256,
    expected_clinical: str = EXPECTED_CLINICAL_SHA256,
    citation_url: str = CITATION_URL,
) -> Tuple[Path, Path]:
    """Verify existence, checksums, and citation for the PPMI dataset.

    Parameters
    ----------
    asv_path: Path | None
        Path to the ASV CSV file.  If ``None`` the default location
        ``data/raw/ppmi_asv.csv`` is used.
    clinical_path: Path | None
        Path to the clinical Parquet file.  If ``None`` the default
        ``data/raw/ppmi_clinical.parquet`` is used.
    expected_asv: str
        Expected SHA‑256 checksum for the ASV file.
    expected_clinical: str
        Expected SHA‑256 checksum for the clinical file.
    citation_url: str
        URL of the dataset citation to validate.

    Returns
    -------
    Tuple[Path, Path]
        The resolved paths for the ASV and clinical files.

    Raises
    ------
    FileNotFoundError
        If either file does not exist.
    ValueError
        If a checksum does not match.
    ConnectionError
        If the citation URL cannot be reached.
    """
    # Resolve default locations.
    if asv_path is None:
        asv_path = paths.data("raw", "ppmi_asv.csv")
    if clinical_path is None:
        clinical_path = paths.data("raw", "ppmi_clinical.parquet")

    log.debug("Verifying ASV file at %s", asv_path)
    log.debug("Verifying clinical file at %s", clinical_path)

    # Existence checks.
    if not asv_path.is_file():
        raise FileNotFoundError(f"Required input file not found: {asv_path}")
    if not clinical_path.is_file():
        raise FileNotFoundError(f"Required input file not found: {clinical_path}")

    # Checksum validation.
    _verify_checksum(asv_path, expected_asv, "ASV file")
    _verify_checksum(clinical_path, expected_clinical, "Clinical file")

    # Citation validation.
    _check_citation(citation_url)

    log.info("PPMI dataset verification completed successfully.")
    return asv_path, clinical_path

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify PPMI dataset files, checksums, and citation."
    )
    parser.add_argument(
        "--asv",
        type=Path,
        help="Path to the ASV CSV file (default: data/raw/ppmi_asv.csv).",
    )
    parser.add_argument(
        "--clinical",
        type=Path,
        help="Path to the clinical Parquet file (default: data/raw/ppmi_clinical.parquet).",
    )
    parser.add_argument(
        "--asv-sha256",
        type=str,
        default=EXPECTED_ASV_SHA256,
        help="Expected SHA‑256 checksum for the ASV file.",
    )
    parser.add_argument(
        "--clinical-sha256",
        type=str,
        default=EXPECTED_CLINICAL_SHA256,
        help="Expected SHA‑256 checksum for the clinical file.",
    )
    parser.add_argument(
        "--citation-url",
        type=str,
        default=CITATION_URL,
        help="URL of the dataset citation to validate.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.verify_dataset``."""
    args = _parse_args(argv)
    try:
        verify_dataset(
            asv_path=args.asv,
            clinical_path=args.clinical,
            expected_asv=args.asv_sha256,
            expected_clinical=args.clinical_sha256,
            citation_url=args.citation_url,
        )
    except Exception as exc:
        log.error("Dataset verification failed: %s", exc)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
