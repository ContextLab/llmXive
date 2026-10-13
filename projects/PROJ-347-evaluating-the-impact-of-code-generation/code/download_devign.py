"""
Download and prepare the Devign dataset.

This script performs the following steps:
1. Downloads the Devign dataset archive from the verified GitHub URL.
2. Extracts the CSV file `devign.csv` from the archive (searches flexibly for any
   file ending with `devign.csv` inside the zip, to accommodate possible repo
   layout changes).
3. Writes the CSV to `data/raw/devign/devign.csv`.
4. Computes the SHA‑256 checksum of the extracted CSV.
5. Verifies the checksum against the value stored in `data/checksums.json`.
   * If the checksum entry exists and does not match, a `ValueError` is raised.
   * If the entry does not exist, the checksum is written to the JSON file for
     future verification.

The script is idempotent: re‑running it will re‑download the archive only if the
target CSV is missing or the checksum does not match.

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
# Updated URL: the repository now uses the default branch `main` instead of `master`.
DEVIGN_ZIP_URL = (
    "https://github.com/anishathalye/devign-dataset/archive/refs/heads/main.zip"
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
    # Step 1 – download the zip (skip if CSV already exists and checksum matches)
    if CSV_DEST.is_file():
        # Verify existing checksum before deciding to skip download.
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
            CSV_DEST.unlink()  # remove corrupted / outdated file

    # At this point the CSV is missing or invalid – ensure we have the zip.
    if not ZIP_PATH.is_file():
        download_file(DEVIGN_ZIP_URL, ZIP_PATH)
    else:
        log.info(f"Using existing zip archive at {ZIP_PATH}")

    # Step 2 – extract the CSV
    log.info(f"Scanning zip archive {ZIP_PATH} for a CSV named devign.csv")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        # Find any member that ends with 'devign.csv' (case‑insensitive)
        candidates = [
            m for m in zip_ref.namelist() if m.lower().endswith("devign.csv")
        ]
        if not candidates:
            raise FileNotFoundError(
                "No file ending with 'devign.csv' found inside the zip archive."
            )
        # Prefer the top‑level devign.csv if multiple are present
        member_name = candidates[0]
        log.info(f"Extracting {member_name} from the archive")
        temp_dir = paths.data("raw", "devign", "_tmp_extract")
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_ref.extract(member_name, path=temp_dir)

        extracted_path = temp_dir / member_name
        # Ensure the destination directory exists
        CSV_DEST.parent.mkdir(parents=True, exist_ok=True)
        # Move the extracted file to the final location
        extracted_path.replace(CSV_DEST)

        # Clean up the temporary extraction directory (remove empty dirs)
        try:
            # Remove the extracted file's parent directories if they are now empty
            parent = extracted_path.parent
            while parent != temp_dir and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
            temp_dir.rmdir()
        except Exception:
            # Non‑critical cleanup failure; log and continue
            log.debug("Temporary extraction directory cleanup failed, ignoring.", exc_info=True)

    # Step 3 – compute checksum
    log.info(f"Computing SHA‑256 for {CSV_DEST}")
    checksum = compute_sha256(CSV_DEST)

    # Step 4 – verify against recorded checksum (or record it)
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
        # No prior record – store it for future runs
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
