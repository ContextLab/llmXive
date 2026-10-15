"""
Download the Juliet Test Suite (SARD) vulnerable Python snippets.

This script mirrors ``code/download_devign.py`` but stores the file under
``data/raw/juliet/python_vuln.csv`` as required by task T001. It also
records the SHA‑256 checksum in ``data/checksums.json`` (the same file used
by the devign downloader). The workflow is idempotent: if the file already
exists and the recorded checksum matches, the download is skipped.
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
# The CSV containing Python vulnerable snippets is hosted in the Juliet
# Test Suite repository under the ``data`` directory.
RAW_CSV_URL = (
    "https://raw.githubusercontent.com/Juliet-Test-Suite/SARD/master/data/python_vuln.csv"
)

# Destination locations (all under the project root)
CSV_DEST = paths.data("raw", "juliet", "python_vuln.csv")
CHECKSUMS_PATH = paths.data("checksums.json")

# ----------------------------------------------------------------------
# Helper functions (identical to those in ``download_devign.py``)
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
    Execute the download‑checksum workflow for the Juliet Python snippets.
    """
    # --------------------------------------------------------------
    # Step 0 – short‑circuit if CSV already exists and checksum matches
    # --------------------------------------------------------------
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
    # Step 1 – download the CSV
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
        log.exception("Fatal error during Juliet dataset preparation")
        sys.exit(1)
