"""
ingest.py

Command‑line entry point used by the quick‑start and CI workflow.
It supports two modes:

* ``python -m code.ingest`` – download the Tg dataset and the Van Krevelen
  fragment contributions, recording their SHA‑256 checksums in
  ``data/checksums.json``.

* ``python -m code.ingest --check`` – verify that every file listed in
  ``data/checksums.json`` exists under ``data/raw/`` and matches its
  recorded checksum.  If the checksum registry is missing, the script
  first downloads the required artefacts and then performs the
  verification.  A short summary is printed; the process exits with a
  non‑zero status on any mismatch.
"""

import argparse
import sys
import json
import hashlib
import time
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Local imports for the actual download steps.
from .ingest_tg import main as download_tg
from .ingest_vk import main as download_vk

log = get_logger(__name__)

def _parse_args() -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest required datasets and verify data integrity."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing files against their SHA‑256 checksums. "
             "If the checksum registry is missing, the required files "
             "are downloaded first.",
    )
    return parser.parse_args()

def _compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 checksum of the file at *file_path*."""
    sha = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def _load_checksums() -> dict:
    """Load the JSON checksum registry (or return an empty dict)."""
    checksums_path = paths.data("checksums.json")
    if not checksums_path.is_file():
        return {}
    with checksums_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _verify_checksums() -> None:
    """
    Verify all artefacts listed in ``data/checksums.json``.
    If the registry is missing, the required artefacts are downloaded
    first.  The function exits with status 1 on any failure; otherwise
    it logs a success message and returns.
    """
    checksums_path = paths.data("checksums.json")

    # Ensure the registry exists – download artefacts if it does not.
    if not checksums_path.is_file():
        log.warning(
            f"Checksums file not found at {checksums_path}. "
            "Downloading required artefacts before verification."
        )
        download_tg()
        download_vk()
        # After download the file must exist; otherwise abort.
        if not checksums_path.is_file():
            log.error("Checksum file still missing after download.")
            sys.exit(1)

    # Load (or reload) the checksum mapping now that the file should exist.
    checksums = _load_checksums()

    all_ok = True
    for filename, expected_checksum in checksums.items():
        file_path = paths.data("raw", filename)
        if not file_path.is_file():
            log.error(f"Missing expected file: {file_path}")
            all_ok = False
            continue

        actual_checksum = _compute_sha256(file_path)
        if actual_checksum.lower() != expected_checksum.lower():
            log.error(
                f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual_checksum}"
            )
            all_ok = False
        else:
            log.info(f"Checksum verified for {filename}")

    if not all_ok:
        log.error("One or more checksum verifications failed.")
        sys.exit(1)
    else:
        log.info("All checksums verified successfully.")

def _main() -> None:
    """Entry point used by ``python -m code.ingest``."""
    args = _parse_args()
    if args.check:
        _verify_checksums()
    else:
        # Download the Tg dataset first, then the Van Krevelen fragment table.
        download_tg()
        download_vk()

if __name__ == "__main__":
    _main()
