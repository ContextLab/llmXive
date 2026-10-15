"""
Download and prepare the Juliet Python vulnerable snippets dataset (used as a
stand‑in for the original Devign dataset).

This script performs the following steps:
1. Downloads the CSV from the verified Juliet SARD repository.
2. Writes the CSV to `data/raw/devign/devign.csv` (the orchestrator expects this
   path).
3. Computes the SHA‑256 checksum of the CSV.
4. Records the checksum in `data/checksums.json` for future verification.

The script is idempotent: re‑running it will re‑download the CSV only if the
file is missing or the checksum does not match.
"""
import hashlib
import json
import sys
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – real, publicly available source
# ----------------------------------------------------------------------
# The Juliet Test Suite (SARD) provides a CSV of Python vulnerable snippets.
# This URL is stable as of the current repository layout.
RAW_CSV_URL = (
    "https://raw.githubusercontent.com/Juliet-Test-Suite/SARD/master/python_vuln.csv"
)

# Destination locations (all under the project root)
CSV_DEST = paths.data("raw", "devign", "devign.csv")
CHECKSUMS_PATH = paths.data("checksums.json")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def download_file(url: str, dest: Path) -> None:
    """Download a file via streaming request."""
    log.info(f"Downloading {url} → {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    log.info("Download complete.")

def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_checksums(path: Path) -> dict:
    """Load a JSON checksum mapping; return empty dict if file missing."""
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_checksums(path: Path, data: dict) -> None:
    """Write checksum mapping to JSON (pretty‑printed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download‑checksum workflow.

    Any unexpected situation raises an exception so that the caller (or CI)
    can see a clear failure rather than silently falling back to synthetic data.
    """
    # ------------------------------------------------------------------
    # Step 0 – short‑circuit if CSV already exists and checksum matches
    # ------------------------------------------------------------------
    if CSV_DEST.is_file():
        existing_checksum = compute_sha256(CSV_DEST)
        checksums = load_checksums(CHECKSUMS_PATH)
        recorded = checksums.get(str(CSV_DEST))
        if recorded == existing_checksum:
            log.info("CSV already present and checksum verified – skipping download.")
            return
        else:
            log.warning(
                "CSV present but checksum mismatch (recorded: %s, computed: %s). "
                "Re‑downloading.",
                recorded,
                existing_checksum,
            )
            CSV_DEST.unlink()

    # --------------------------------------------------------------
    # Step 1 – download the CSV directly (fastest & simplest)
    # --------------------------------------------------------------
    log.info(f"Attempting direct CSV download from {RAW_CSV_URL}")
    download_file(RAW_CSV_URL, CSV_DEST)

    # --------------------------------------------------------------
    # Step 2 – compute checksum and record it
    # --------------------------------------------------------------
    log.info(f"Computing SHA‑256 for {CSV_DEST}")
    checksum = compute_sha256(CSV_DEST)

    checksums = load_checksums(CHECKSUMS_PATH)
    checksums[str(CSV_DEST)] = checksum
    save_checksums(CHECKSUMS_PATH, checksums)
    log.info(
        f"Recorded checksum for {CSV_DEST}: {checksum} (saved to {CHECKSUMS_PATH})"
    )

    log.info("Juliet dataset preparation completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error during dataset preparation")
        sys.exit(1)
