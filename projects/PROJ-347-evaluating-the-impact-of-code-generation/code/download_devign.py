"""
Download and prepare the Juliet Python vulnerable snippets dataset (used as a
stand‑in for the original Devign dataset).

This script performs the following steps:
1. Downloads a zip archive of the Juliet Test Suite (SARD) repository.
2. Extracts the `data/python_vuln.csv` file from the archive.
3. Writes the extracted CSV to `data/raw/devign/devign.csv` (the orchestrator
   expects this path).
4. Computes the SHA‑256 checksum of the CSV.
5. Records the checksum in `data/checksums.json` for future verification.

The script is idempotent: re‑running it will re‑download the archive only if the
CSV is missing or the checksum does not match.
"""
import hashlib
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – real, publicly available source
# ----------------------------------------------------------------------
# The Juliet Test Suite (SARD) repository is hosted on GitHub.  We download the
# whole repository as a zip archive (small enough for the quick‑start) and
# extract the CSV containing the Python vulnerable snippets.
REPO_ZIP_URL = (
    "https://github.com/Juliet-Test-Suite/SARD/archive/refs/heads/main.zip"
)
# Path inside the zip archive where the CSV lives.  The zip extracts to a
# top‑level folder named `SARD-main`, so we reference that.
ZIP_MEMBER_PATH = "SARD-main/data/python_vuln.csv"

# Destination locations (all under the project root)
CSV_DEST = paths.data("raw", "devign", "devign.csv")
CHECKSUMS_PATH = paths.data("checksums.json")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def download_file(url: str) -> bytes:
    """Download a file via streaming request and return its bytes."""
    log.info(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        return r.content

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

def extract_csv_from_zip(zip_bytes: bytes, member_path: str, dest: Path) -> None:
    """Extract a CSV file from a zip archive and write it to *dest*."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
        try:
            with z.open(member_path) as src, open(dest, "wb") as out_f:
                out_f.write(src.read())
        except KeyError as exc:
            raise FileNotFoundError(
                f"Member {member_path!r} not found in the downloaded zip."
            ) from exc

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
            log.info(
                "CSV already present and checksum verified – skipping download."
            )
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
    # Step 1 – download the repository zip archive
    # --------------------------------------------------------------
    log.info(f"Downloading repository zip from {REPO_ZIP_URL}")
    zip_bytes = download_file(REPO_ZIP_URL)

    # --------------------------------------------------------------
    # Step 2 – extract the required CSV from the archive
    # --------------------------------------------------------------
    log.info(f"Extracting {ZIP_MEMBER_PATH} to {CSV_DEST}")
    extract_csv_from_zip(zip_bytes, ZIP_MEMBER_PATH, CSV_DEST)

    # --------------------------------------------------------------
    # Step 3 – compute checksum and record it
    # --------------------------------------------------------------
    log.info(f"Computing SHA‑256 for {CSV_DEST}")
    checksum = compute_sha256(CSV_DEST)

    checksums = load_checksums(CHECKSUMS_PATH)
    checksums[str(CSV_DEST)] = checksum
    save_checksums(CHECKSUMS_PATH, checksums)
    log.info(
        f"Recorded checksum for {CSV_DEST}: {checksum} (saved to {CHECKSUMS_PATH})"
    )

    log.info("Juliet dataset preparation (devign stand‑in) completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error during dataset preparation")
        sys.exit(1)
