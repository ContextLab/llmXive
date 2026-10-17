"""
ingest.py

Command‑line entry point used by the quick‑start and CI workflow.
It supports two modes:

* ``python -m code.ingest`` – download the Tg dataset (and create
  ``data/checksums.json`` if it does not already exist).

* ``python -m code.ingest --check`` – verify that every file listed in
  ``data/checksums.json`` exists and matches its recorded SHA‑256 checksum.
  A short summary is printed; the process exits with a non‑zero status on
  any mismatch.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Import the download helper that also manages checksum registration.
from .ingest_tg import main as download_main

log = get_logger(__name__)

def _compute_checksum(file_path: Path) -> str:
    """Return the SHA‑256 checksum of the file at ``file_path``."""
    sha = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def _verify_checksums() -> None:
    """Load ``data/checksums.json`` and verify each listed artifact."""
    checksums_path = paths.data("checksums.json")
    if not checksums_path.is_file():
        log.error(f"Checksums file missing at {checksums_path}")
        sys.exit(1)

    try:
        with checksums_path.open("r", encoding="utf-8") as f:
            expected = json.load(f)
    except json.JSONDecodeError as exc:
        log.error(f"Invalid JSON in checksums file: {exc}")
        sys.exit(1)

    all_ok = True
    for rel_path, exp_checksum in expected.items():
        artifact = paths.root / rel_path  # paths are relative to project root
        if not artifact.is_file():
            log.error(f"Expected artifact not found: {artifact}")
            all_ok = False
            continue
        actual = _compute_checksum(artifact)
        if actual.lower() != exp_checksum.lower():
            log.error(
                f"Checksum mismatch for {artifact}: expected {exp_checksum}, got {actual}"
            )
            all_ok = False
        else:
            log.info(f"Checksum OK for {artifact}")

    if not all_ok:
        log.error("One or more checksum verifications failed.")
        sys.exit(1)
    else:
        log.info("All checksum verifications passed.")

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest the experimental Tg dataset and verify data integrity."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing files against their SHA‑256 checksums instead of downloading.",
    )
    return parser.parse_args()

def _main():
    args = _parse_args()
    if args.check:
        _verify_checksums()
    else:
        # Perform the download (and checksum registration) step.
        download_main()

if __name__ == "__main__":
    _main()
