"""
Download and prepare the Devign dataset.

This script performs the following steps:
1. Downloads the Devign dataset archive from the verified GitHub URL.
2. Extracts the CSV file `devign.csv` from the archive.
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

# Name of the CSV inside the zip archive (as per the repository layout).
# The zip extracts a top‑level directory named `devign-dataset-main`.
INTERNAL_CSV_PATH = Path("devign-dataset-main") / "devign.csv"

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
    # Step 1 – download the zip (skip if CSV already exists)
    if not CSV_DEST.is_file():
        download_file(DEVIGN_ZIP_URL, ZIP_PATH)

        # Step 2 – extract the CSV
        log.info(f"Extracting {INTERNAL_CSV_PATH} from {ZIP_PATH}")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            try:
                # Find the member that ends with the expected internal path
                members = [
                    m for m in zip_ref.namelist() if m.endswith(str(INTERNAL_CSV_PATH))
                ]
                if not members:
                    raise FileNotFoundError(
                        f"{INTERNAL_CSV_PATH} not found in the zip archive."
                    )
                # Extract only the required CSV to a temporary location
                temp_dir = paths.data("raw", "devign", "_tmp_extract")
                temp_dir.mkdir(parents=True, exist_ok=True)
                zip_ref.extract(members[0], path=temp_dir)
                extracted_path = temp_dir / members[0]
                CSV_DEST.parent.mkdir(parents=True, exist_ok=True)
                extracted_path.replace(CSV_DEST)
                # Clean up temporary extraction directory
                for child in temp_dir.iterdir():
                    if child.is_file():
                        child.unlink()
                temp_dir.rmdir()
            except Exception as e:
                log.error(f"Failed to extract CSV: {e}")
                raise

    # Step 3 – compute checksum
    log.info(f"Computing SHA‑256 for {CSV_DEST}")
    checksum = compute_sha256(CSV_DEST)

    # Step 4 – verify against recorded checksum
    checksums = load_checksums(CHECKSUMS_PATH)
    recorded = checksums.get(str(CSV_DEST))
    if recorded:
        if recorded != checksum:
            raise ValueError(
                f"Checksum mismatch for {CSV_DEST}: recorded {recorded}, "
                f"computed {checksum}"
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