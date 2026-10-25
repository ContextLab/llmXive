"""Download the Pantheon+ dataset, verify its integrity, and record provenance.

This script fulfills task **T002**:
  1. Loads the Pantheon+ supernova compilation from the verified
     HuggingFace `datasets` repository.
  2. Writes the data to ``data/raw/pantheon_plus.fits`` as an
     Astropy binary table containing the required columns:
     ``ID``, ``RA``, ``DEC``, ``ZHD``, ``MU``, ``MUERR``.
  3. Computes the SHA‑256 checksum of the FITS file.
  4. Writes a provenance JSON file (``metadata.json``) with the
     dataset version, source URL, checksum, and ``citation_verified`` flag.
  5. Updates the project‑specific state YAML with the checksum.

The script supports a ``--verify-only`` mode that checks an existing
FITS file without re‑downloading.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml
from astropy.io import fits
from astropy.table import Table
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_DATASET_VERSION = "v1.0"
REQUIRED_COLUMNS = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}
STATE_FILE = (
    Path(__file__).parents[2]
    / "state"
    / "projects"
    / "PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml"
)
# Source URL for provenance – the HuggingFace dataset page.
SOURCE_URL = "https://huggingface.co/datasets/juliensimon/pantheon-plus-sne-ia"

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


def download_and_write_fits(destination: Path) -> None:
    """Load the Pantheon+ dataset via ``datasets`` and write it as a FITS file."""
    logger.info("Loading Pantheon+ dataset from HuggingFace")
    ds = load_dataset("juliensimon/pantheon-plus-sne-ia", split="train")
    logger.info("Dataset loaded: %d records", len(ds))

    # Expected fields in the HF dataset (verified empirically):
    #   sn_name, ra, dec, redshift_hd, distance_modulus, distance_modulus_err
    # Map them to the required column names.
    table = Table(
        [
            ds["sn_name"],
            ds["ra"],
            ds["dec"],
            ds["redshift_hd"],
            ds["distance_modulus"],
            ds["distance_modulus_err"],
        ],
        names=("ID", "RA", "DEC", "ZHD", "MU", "MUERR"),
    )

    # Ensure correct data types (float64 for numeric columns)
    for col in ("RA", "DEC", "ZHD", "MU", "MUERR"):
        table[col] = table[col].astype(float)

    hdu = fits.BinTableHDU(table)
    hdu.writeto(destination, overwrite=True)
    logger.info("Wrote FITS file to %s", destination)


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
    # Use parse_known_args to tolerate pytest's injected arguments.
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

    # Normal mode: download (actually load) and write FITS.
    download_and_write_fits(raw_fits_path)

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
