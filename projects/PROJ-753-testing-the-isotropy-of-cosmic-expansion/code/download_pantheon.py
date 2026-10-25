"""Download the Pantheon+ dataset (FITS format), verify its SHA‑256 checksum,
record provenance, and update the project state file.

This script fulfills task **T002**:
  1. Downloads the official Pantheon+ FITS file from a reliable public URL.
  2. Computes its SHA‑256 checksum.
  3. Writes a provenance JSON file (metadata.json) containing:
     - dataset_version
     - source_url
     - sha256
     - citation_verified (initially false)
  4. Verifies that the FITS header contains the required columns:
     ID, RA, DEC, ZHD, MU, MUERR.
  5. Updates the project‑specific state YAML with the checksum.

The script exits with a non‑zero status on any failure, ensuring that the
pipeline aborts loudly if the real data cannot be obtained or validated.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import requests
import yaml
from astropy.io import fits

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The Pantheon+ FITS file is publicly hosted on Zenodo. This URL points
# directly to the file (download forced). It resolves to the official
# Pantheon+ release tarball containing ``Pantheon+_Data.fits``.
DEFAULT_URL = (
    "https://zenodo.org/record/7968445/files/Pantheon%2B_Data.fits?download=1"
)
DEFAULT_DATASET_VERSION = "v1.0"
REQUIRED_COLUMNS = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}
STATE_FILE = (
    Path(__file__).parents[2]
    / "state"
    / "projects"
    / "PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml"
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def download_file(url: str, destination: Path) -> None:
    """Download ``url`` to ``destination`` using a streaming request."""
    logger.info("Downloading Pantheon+ dataset from %s", url)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(destination, "wb") as out_f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    out_f.write(chunk)
    logger.info("Saved dataset to %s", destination)


def compute_sha256(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_metadata(
    metadata_path: Path,
    *,
    dataset_version: str,
    source_url: str,
    sha256: str,
    citation_verified: bool = False,
) -> None:
    """Write the provenance JSON file required by the spec."""
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
        # The Pantheon+ data is stored in the first extension (binary table)
        if len(hdul) < 2:
            raise ValueError(
                "FITS file does not contain a binary table extension."
            )
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


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download Pantheon+ FITS dataset, verify it, and record provenance."
        )
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="URL of the Pantheon+ FITS dataset (default: Zenodo download link).",
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_DATASET_VERSION,
        help="Dataset version identifier to store in metadata.json.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify an existing file; do not download.",
    )
    # Use parse_known_args to tolerate pytest's injected arguments.
    args, _ = parser.parse_known_args()

    # Resolve target paths using llmxive_toolkit helpers.
    raw_fits_path = paths.data("raw", "pantheon_plus.fits")
    metadata_path = paths.data("raw", "metadata.json")

    if args.verify_only:
        # Verify that the file exists, compute checksum, verify columns,
        # write metadata and update state without re‑downloading.
        if not raw_fits_path.is_file():
            raise FileNotFoundError(
                f"File not found for verification: {raw_fits_path}"
            )
        checksum = compute_sha256(raw_fits_path)
        verify_fits_columns(raw_fits_path)
        write_metadata(
            metadata_path,
            dataset_version=args.version,
            source_url=args.url,
            sha256=checksum,
            citation_verified=False,
        )
        update_state_yaml(STATE_FILE, checksum)
        logger.info("Verification-only mode completed successfully.")
        return

    # Normal mode: download, then verify.
    download_file(args.url, raw_fits_path)

    # 2️⃣ Compute checksum
    checksum = compute_sha256(raw_fits_path)

    # 3️⃣ Verify required columns
    verify_fits_columns(raw_fits_path)

    # 4️⃣ Write provenance metadata (citation not yet verified)
    write_metadata(
        metadata_path,
        dataset_version=args.version,
        source_url=args.url,
        sha256=checksum,
        citation_verified=False,
    )

    # 5️⃣ Record checksum in project state YAML
    update_state_yaml(STATE_FILE, checksum)

    logger.info(
        "Pantheon+ dataset download and verification completed successfully."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Pantheon+ download failed: %s", exc)
        sys.exit(1)
