"""
Fetch Zenodo dataset and prepare raw barrier CSV.

Implements FR-001 data fetching (T004b, T004c) required by downstream
tasks such as T011. The script downloads the record identified by
`ZENODO_ID` from Zenodo, verifies the SHA‑256 checksum (if provided),
extracts archives when necessary, selects the appropriate CSV file,
and places it at `data/raw/barrier_dataset.csv`. It also writes a short
verification entry to `logs/verification.log`.
"""

import hashlib
import logging
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

import requests

# llmxive toolkit helpers for path management and logging
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
try:
    # The Zenodo accession ID is defined in the project config (T004a)
    from config import ZENODO_ID  # noqa: F401
except Exception:
    # Fallback to the hard‑coded ID from the spec if the config module does not
    # define it (this should never happen in a correctly configured project).
    ZENODO_ID = "1048765"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, destination: Path) -> None:
    """Download a file from *url* to *destination* (streaming)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def fetch_and_prepare() -> None:
    """Download the Zenodo record, verify, extract and normalise."""
    log = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1. Retrieve record metadata
    # ------------------------------------------------------------------
    record_url = f"https://zenodo.org/api/records/{ZENODO_ID}"
    log.info(f"Fetching Zenodo record metadata from {record_url}")
    response = requests.get(record_url, timeout=30)
    response.raise_for_status()
    record = response.json()
    files = record.get("files", [])
    if not files:
        raise RuntimeError("No files found in the Zenodo record.")

    # ------------------------------------------------------------------
    # 2. Choose a file to download
    # ------------------------------------------------------------------
    # Prefer a CSV file directly; otherwise take the first file (likely an archive)
    target_file = None
    for f in files:
        if f["key"].lower().endswith(".csv"):
            target_file = f
            break
    if target_file is None:
        target_file = files[0]

    filename = target_file["key"]
    download_url = target_file["links"]["self"]
    download_path = paths.data("raw", filename)

    # ------------------------------------------------------------------
    # 3. Download the selected file
    # ------------------------------------------------------------------
    log.info(f"Downloading {filename} → {download_path}")
    download_file(download_url, download_path)

    # ------------------------------------------------------------------
    # 4. Optional checksum verification (Zenodo supplies SHA‑256)
    # ------------------------------------------------------------------
    checksum_entry = target_file.get("checksum")
    if checksum_entry:
        # Zenodo checksum format: "sha256:<hash>"
        if ":" in checksum_entry:
            _, expected = checksum_entry.split(":", 1)
        else:
            expected = checksum_entry
        actual = compute_sha256(download_path)
        if actual != expected:
            log.error(
                f"Checksum mismatch for {filename}: expected {expected}, got {actual}"
            )
            raise RuntimeError("Checksum verification failed.")
        else:
            log.info("Checksum verification passed.")

    # ------------------------------------------------------------------
    # 5. Extract if archive, otherwise treat as CSV
    # ------------------------------------------------------------------
    dest_csv = paths.data("raw", "barrier_dataset.csv")
    if filename.lower().endswith((".zip", ".tar.gz", ".tgz", ".tar")):
        extract_dir = paths.data("raw", "extracted")
        extract_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Extracting archive {download_path} to {extract_dir}")

        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(download_path, "r") as zf:
                zf.extractall(extract_dir)
        else:
            with tarfile.open(download_path, "r:*") as tf:
                tf.extractall(extract_dir)

        # Locate CSV files inside the extracted tree
        csv_candidates = list(extract_dir.rglob("*.csv"))
        if not csv_candidates:
            raise RuntimeError("No CSV files found after extracting the archive.")

        # Prefer a CSV whose name contains 'barrier'
        selected = None
        for p in csv_candidates:
            if "barrier" in p.name.lower():
                selected = p
                break
        if selected is None:
            # Fallback: choose the largest CSV (most data)
            selected = max(csv_candidates, key=lambda p: p.stat().st_size)

        # Move the chosen CSV to the canonical location
        log.info(f"Moving selected CSV {selected} → {dest_csv}")
        shutil.move(str(selected), str(dest_csv))

    else:
        # Already a CSV – just rename/move to the canonical name
        log.info(f"Renaming downloaded CSV to {dest_csv}")
        shutil.move(str(download_path), str(dest_csv))

    # ------------------------------------------------------------------
    # 6. Log verification details
    # ------------------------------------------------------------------
    verification_log = paths.logs("verification.log")
    with open(verification_log, "a", encoding="utf-8") as vlog:
        vlog.write(
            f"Fetched Zenodo ID {ZENODO_ID}, file {filename}, size {dest_csv.stat().st_size} bytes, SHA256 {compute_sha256(dest_csv)}\\n"
        )
    log.info("Data fetch and preparation completed successfully.")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point used by ``code/main.py fetch``."""
    fetch_and_prepare()

if __name__ == "__main__":
    main()
