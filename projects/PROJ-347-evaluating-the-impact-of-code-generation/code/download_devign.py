"""
Download and prepare the Devign dataset.

This script performs the following steps:
1. Attempts to download the Devign CSV directly from the raw GitHub URL.
   If that fails, it falls back to downloading the zip archive (trying both
   `main` and `master` branches) and extracts the CSV.
2. Writes the CSV to `data/raw/devign/devign.csv`.
3. Computes the SHA‑256 checksum of the extracted CSV.
4. Verifies the checksum against the value stored in `data/checksums.json`.
   * If the checksum entry exists and does not match, a `ValueError` is raised.
   * If the entry does not exist, the checksum is written to the JSON file for
     future verification.

The script is idempotent: re‑running it will re‑download the CSV only if the
target file is missing or the checksum does not match.

Usage (run as a module or script):
    python -m code.download_devign
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Primary raw CSV URL (direct download). This URL is stable as long as the
# upstream repository keeps the file at the root of the repo.
RAW_CSV_URL = (
    "https://raw.githubusercontent.com/anishathalye/devign-dataset/master/devign.csv"
)
# Fallback zip URLs – historically the repository used `master`; newer mirrors
# may have switched to `main`. We try both.
DEVIGN_ZIP_URL_MAIN = (
    "https://github.com/anishathalye/devign-dataset/archive/refs/heads/main.zip"
)
DEVIGN_ZIP_URL_MASTER = (
    "https://github.com/anishathalye/devign-dataset/archive/refs/heads/master.zip"
)
# Destination locations (all under the project root)
ZIP_PATH = paths.data("raw", "devign", "devign.zip")
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

def _determine_zip_url() -> str:
    """
    Return a working download URL for the Devign zip archive.
    Tries the `main` branch first; on HTTP 404 falls back to `master`.
    Any other HTTP error is propagated.
    """
    for url in (DEVIGN_ZIP_URL_MAIN, DEVIGN_ZIP_URL_MASTER):
        try:
            with requests.head(url, timeout=10) as resp:
                if resp.status_code == 200:
                    log.info(f"Selected Devign archive URL: {url}")
                    return url
                if resp.status_code == 404:
                    log.debug(f"URL not found (404): {url}")
                    continue
                resp.raise_for_status()
        except requests.RequestException as exc:
            log.debug(f"HEAD request failed for {url}: {exc}")
            raise
    raise RuntimeError(
        "Unable to locate a valid Devign dataset archive. Tried both main and master branches."
    )

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download‑extract‑checksum workflow.

    The function is deliberately defensive: any unexpected situation raises an
    exception so that the caller (or CI) can see a clear failure rather than
    silently falling back to synthetic data.
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
    # Step 1 – try direct CSV download (fastest & simplest)
    # --------------------------------------------------------------
    try:
        log.info(f"Attempting direct CSV download from {RAW_CSV_URL}")
        download_file(RAW_CSV_URL, CSV_DEST)
    except Exception as exc:
        log.warning(f"Direct CSV download failed: {exc}. Falling back to zip archive.")
        # Ensure any partially written file is removed before fallback
        if CSV_DEST.is_file():
            CSV_DEST.unlink()
        # --------------------------------------------------------------
        # Step 2 – download zip archive (if needed)
        # --------------------------------------------------------------
        download_url = _determine_zip_url()

        if not ZIP_PATH.is_file():
            download_file(download_url, ZIP_PATH)
        else:
            log.info(f"Using existing zip archive at {ZIP_PATH}")

        # --------------------------------------------------------------
        # Step 3 – extract the CSV from the zip
        # --------------------------------------------------------------
        log.info(f"Scanning zip archive {ZIP_PATH} for a CSV named devign.csv")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            candidates = [
                m for m in zip_ref.namelist() if m.lower().endswith("devign.csv")
            ]
            if not candidates:
                raise FileNotFoundError(
                    "No file ending with 'devign.csv' found inside the zip archive."
                )
            member_name = candidates[0]
            log.info(f"Extracting {member_name} from the archive")
            temp_dir = paths.data("raw", "devign", "_tmp_extract")
            temp_dir.mkdir(parents=True, exist_ok=True)
            zip_ref.extract(member_name, path=temp_dir)

            extracted_path = temp_dir / member_name
            CSV_DEST.parent.mkdir(parents=True, exist_ok=True)
            extracted_path.replace(CSV_DEST)

            # Clean up temporary extraction directory (best‑effort)
            try:
                parent = extracted_path.parent
                while parent != temp_dir and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                temp_dir.rmdir()
            except Exception:
                log.debug(
                    "Temporary extraction directory cleanup failed, ignoring.", exc_info=True
                )

    # --------------------------------------------------------------
    # Step 4 – compute checksum and verify / record it
    # --------------------------------------------------------------
    log.info(f"Computing SHA‑256 for {CSV_DEST}")
    checksum = compute_sha256(CSV_DEST)

    checksums = load_checksums(CHECKSUMS_PATH)
    recorded = checksums.get(str(CSV_DEST))
    if recorded:
        if recorded != checksum:
            raise ValueError(
                f"Checksum mismatch for {CSV_DEST}: recorded {recorded}, computed {checksum}"
            )
        else:
            log.info("Checksum verification passed (existing record).")
    else:
        checksums[str(CSV_DEST)] = checksum
        save_checksums(CHECKSUMS_PATH, checksums)
        log.info(
            f"Recorded new checksum for {CSV_DEST}: {checksum} (saved to {CHECKSUMS_PATH})"
        )

    log.info("Devign dataset preparation completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error during Devign dataset preparation")
        sys.exit(1)
