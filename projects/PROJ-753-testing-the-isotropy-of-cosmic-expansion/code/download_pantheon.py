"""Download the Pantheon+ dataset, verify its integrity, and record provenance.

This script fulfills task **T002**:
  1. Downloads the official Pantheon+ release from Zenodo.
  2. Handles both direct FITS downloads and archive (tar.gz/zip) extraction.
  3. Ensures the data is stored at ``data/raw/pantheon_plus.fits``.
  4. Renames columns to match the required project schema:
     ``ID``, ``RA``, ``DEC``, ``ZHD``, ``MU``, ``MUERR``.
  5. Computes the SHA‑256 checksum of the final FITS file.
  6. Writes a provenance JSON file (``metadata.json``).
  7. Updates the project‑specific state YAML with the checksum.
"""
import argparse
import hashlib
import json
import sys
import tarfile
import zipfile
import io
from pathlib import Path

import yaml
import requests
from astropy.io import fits
from astropy.table import Table

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_DATASET_VERSION = "v1.0"
REQUIRED_COLUMNS = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}

# Column mapping from official Pantheon+ names to project names
COLUMN_MAP = {
    "name": "ID",
    "ra": "RA",
    "dec": "DEC",
    "z": "ZHD",
    "mu": "MU",
    "mu_err": "MUERR",
}

# Zenodo Record ID for Pantheon+
RECORD_ID = "7968445"
# The DOI resolves to https://doi.org/10.5281/zenodo.7968445
# We use the API to find the actual file names and download URLs.
API_URL = f"https://zenodo.org/api/records/{RECORD_ID}"

STATE_FILE = (
    paths.root / "state" / "projects" / "PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml"
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 checksum of ``file_path``."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def write_metadata(
    metadata_path: Path,
    *,
    dataset_version: str,
    source_url: str,
    sha256: str,
    citation_verified: bool = False,
) -> None:
    """Write the provenance JSON file."""
    data = {
        "dataset_version": dataset_version,
        "source_url": source_url,
        "sha256": sha256,
        "citation_verified": citation_verified,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Wrote metadata to %s", metadata_path)


def verify_fits_columns(fits_path: Path) -> None:
    """Raise an error if required columns are missing from the FITS table."""
    logger.info("Verifying FITS columns in %s", fits_path)
    with fits.open(fits_path) as hdul:
        if len(hdul) < 2:
            raise ValueError("FITS file does not contain a binary table extension.")
        table = hdul[1].data
        present = set(table.columns.names)
        missing = REQUIRED_COLUMNS - present
        if missing:
            raise ValueError(
                f"Missing required columns in FITS file {fits_path.name}: {missing}"
            )
    logger.info("All required FITS columns are present.")


def update_state_yaml(state_path: Path, checksum: str) -> None:
    """Add or update the checksum entry for the Pantheon+ FITS file."""
    logger.info("Updating state file %s", state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.is_file():
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    artifact_hashes = state.get("artifact_hashes", {})
    artifact_hashes["pantheon_plus.fits"] = checksum
    state["artifact_hashes"] = artifact_hashes

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f)
    logger.info("State file updated with checksum.")


def download_and_process_fits(destination: Path) -> None:
    """Download Pantheon+ from Zenodo, extract if archived, rename columns, and write to FITS."""
    logger.info("Fetching file list from Zenodo API: %s", API_URL)
    
    resp = requests.get(API_URL, timeout=60)
    resp.raise_for_status()
    record_data = resp.json()
    
    files = record_data.get("files", [])
    if not files:
        raise RuntimeError("No files found in Zenodo record.")

    # Search for the FITS file directly, or a tarball/zip containing it
    fits_entry = next((f for f in files if f["key"].endswith(".fits")), None)
    archive_entry = next((f for f in files if f["key"].endswith((".tar.gz", ".tgz", ".zip"))), None)
    
    download_url = None
    is_archive = False
    
    if fits_entry:
        download_url = fits_entry["links"]["self"]
        # Ensure we use the direct download link format
        download_url = download_url.replace("/api/records/", "/record/").replace("/files/", "/files/") + "?download=1"
        # Simplified: Zenodo API 'self' link is often the API endpoint. 
        # The standard download URL is /record/{id}/files/{key}?download=1
        download_url = f"https://zenodo.org/record/{RECORD_ID}/files/{fits_entry['key']}?download=1"
        is_archive = False
        logger.info("Found direct FITS file: %s", fits_entry["key"])
    elif archive_entry:
        download_url = f"https://zenodo.org/record/{RECORD_ID}/files/{archive_entry['key']}?download=1"
        is_archive = True
        logger.info("Found archive file: %s", archive_entry["key"])
    else:
        raise FileNotFoundError("Could not find Pantheon+ FITS or archive in Zenodo record.")

    logger.info("Downloading from: %s", download_url)
    response = requests.get(download_url, stream=True, timeout=300)
    response.raise_for_status()

    if is_archive:
        logger.info("Extracting FITS file from archive...")
        content = response.content
        if download_url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                fits_filename = next((n for n in z.namelist() if n.endswith(".fits")), None)
                if not fits_filename:
                    raise FileNotFoundError("No .fits file found in zip archive.")
                with z.open(fits_filename) as f:
                    raw_fits_bytes = f.read()
        else: # tar.gz
            with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as t:
                fits_member = next((m for m in t.getmembers() if m.name.endswith(".fits")), None)
                if not fits_member:
                    raise FileNotFoundError("No .fits file found in tar archive.")
                raw_fits_bytes = t.extractfile(fits_member).read()
        
        temp_raw = destination.with_suffix(".raw.fits")
        with open(temp_raw, "wb") as f:
            f.write(raw_fits_bytes)
    else:
        temp_raw = destination.with_suffix(".raw.fits")
        with open(temp_raw, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    logger.info("Processing columns...")
    t = Table.read(temp_raw)
    current_cols = t.colnames
    new_data = {}
    
    for official_name, project_name in COLUMN_MAP.items():
        found_col = None
        if official_name in current_cols:
            found_col = official_name
        else:
            for col in current_cols:
                if col.lower() == official_name.lower():
                    found_col = col
                    break
        
        if found_col:
            new_data[project_name] = t[found_col]
        else:
            raise KeyError(f"Could not find column matching {official_name} in dataset.")

    ordered_cols = ["ID", "RA", "DEC", "ZHD", "MU", "MUERR"]
    final_table = Table({col: new_data[col] for col in ordered_cols})
    final_table.write(destination, overwrite=True, format="fits")
    
    if temp_raw.exists():
        temp_raw.unlink()
        
    logger.info("Processed and wrote FITS file to %s", destination)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Pantheon+ dataset, verify it, and record provenance."
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_DATASET_VERSION,
        help="Dataset version identifier to store in metadata.json.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify an existing FITS file; do not download.",
    )
    args, _ = parser.parse_known_args()

    raw_fits_path = paths.data("raw", "pantheon_plus.fits")
    metadata_path = paths.data("raw", "metadata.json")

    if args.verify_only:
        if not raw_fits_path.is_file():
            raise FileNotFoundError(f"File not found for verification: {raw_fits_path}")
        checksum = compute_sha256(raw_fits_path)
        verify_fits_columns(raw_fits_path)
        write_metadata(
            metadata_path,
            dataset_version=args.version,
            source_url=f"https://doi.org/10.5281/zenodo.{RECORD_ID}",
            sha256=checksum,
            citation_verified=False,
        )
        update_state_yaml(STATE_FILE, checksum)
        logger.info("Verification-only mode completed successfully.")
        return

    download_and_process_fits(raw_fits_path)

    checksum = compute_sha256(raw_fits_path)
    verify_fits_columns(raw_fits_path)

    write_metadata(
        metadata_path,
        dataset_version=args.version,
        source_url=f"https://doi.org/10.5281/zenodo.{RECORD_ID}",
        sha256=checksum,
        citation_verified=False,
    )

    update_state_yaml(STATE_FILE, checksum)
    logger.info("Pantheon+ dataset download and verification completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Pantheon+ download failed: %s", exc)
        sys.exit(1)