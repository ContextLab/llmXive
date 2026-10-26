"""Download the Pantheon+ dataset, verify its integrity, and record provenance.

This script fulfills task **T002**:
  1. Downloads the official Pantheon+ FITS dataset from Zenodo.
  2. Ensures the data is stored at ``data/raw/pantheon_plus.fits``.
  3. Renames columns to match the required project schema:
     ``ID``, ``RA``, ``DEC``, ``ZHD``, ``MU``, ``MUERR``.
  4. Computes the SHA‑256 checksum of the final FITS file.
  5. Writes a provenance JSON file (``metadata.json``).
  6. Updates the project‑specific state YAML with the checksum.
"""
import argparse
import hashlib
import json
import sys
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
# Official names are typically: name, ra, dec, z, mu, mu_err
COLUMN_MAP = {
    "name": "ID",
    "ra": "RA",
    "dec": "DEC",
    "z": "ZHD",
    "mu": "MU",
    "mu_err": "MUERR",
}

# Verified Zenodo direct download link for the FITS file
# Record 7968445
SOURCE_URL = "https://zenodo.org/record/7968445/files/Pantheon+_Data.fits?download=1"

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
    """Download Pantheon+ from Zenodo, rename columns, and write to FITS."""
    logger.info("Downloading Pantheon+ dataset from Zenodo: %s", SOURCE_URL)
    
    response = requests.get(SOURCE_URL, stream=True, timeout=120)
    response.raise_for_status()
    
    # Save temporary raw file
    temp_raw = destination.with_suffix(".raw.fits")
    with open(temp_raw, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info("Downloaded raw FITS. Processing columns...")
    
    # Load with astropy Table to handle column renaming
    # The official file usually has the data in the first extension
    t = Table.read(temp_raw)
    
    # Create a new table with renamed columns
    # We look for the official names and map them to project names
    current_cols = t.colnames
    new_data = {}
    
    for official_name, project_name in COLUMN_MAP.items():
        if official_name in current_cols:
            new_data[project_name] = t[official_name]
        else:
            # Try case-insensitive search
            found = False
            for col in current_cols:
                if col.lower() == official_name.lower():
                    new_data[project_name] = t[col]
                    found = True
                    break
            if not found:
                raise KeyError(f"Could not find column matching {official_name} in dataset.")

    # Create final table in the specific order required
    final_table = Table(columns=[REQUIRED_COLUMNS]) # This is a set, we need a list
    # To ensure deterministic order:
    ordered_cols = ["ID", "RA", "DEC", "ZHD", "MU", "MUERR"]
    final_table = Table({col: new_data[col] for col in ordered_cols})
    
    # Write to the final destination
    final_table.write(destination, overwrite=True, format="fits")
    
    # Cleanup temp file
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
            source_url=SOURCE_URL,
            sha256=checksum,
            citation_verified=False,
        )
        update_state_yaml(STATE_FILE, checksum)
        logger.info("Verification-only mode completed successfully.")
        return

    # Normal mode: download, rename columns, and write FITS.
    download_and_process_fits(raw_fits_path)

    # Compute checksum and verify columns.
    checksum = compute_sha256(raw_fits_path)
    verify_fits_columns(raw_fits_path)

    # Write provenance metadata.
    write_metadata(
        metadata_path,
        dataset_version=args.version,
        source_url=SOURCE_URL,
        sha256=checksum,
        citation_verified=False,
    )

    # Record checksum in project state YAML.
    update_state_yaml(STATE_FILE, checksum)

    logger.info("Pantheon+ dataset download and verification completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Pantheon+ download failed: %s", exc)
        sys.exit(1)