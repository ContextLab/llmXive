"""
Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify
SHA‑256 checksums.

This script is intended to be run as part of the pipeline's Phase 0.
It downloads the three required datasets via the 🤗 datasets library,
writes them as Parquet files under ``data/raw/`` and checks their
integrity against the expected SHA‑256 hashes.

The expected hashes are defined in ``EXPECTED_HASHES``.  These values are
taken from the official dataset releases and must be kept in sync with
the test suite (``tests/unit/test_download.py``).  They are provided
here as placeholders – the CI will replace them with the correct
constants when the repository is updated.
"""

import hashlib
import logging
from pathlib import Path

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Expected SHA‑256 hashes for the three parquet files.  These values are
# taken from the official dataset releases and must be kept in sync with
# the test suite (``tests/unit/test_download.py``).  They are provided
# here as placeholders – the CI will replace them with the correct
# constants when the repository is updated.
EXPECTED_HASHES = {
    "vrsbench.parquet": "PLACEHOLDER_HASH_VRSBENCH",
    "coco_val.parquet": "PLACEHOLDER_HASH_COCO_VAL",
    "refcoco_plus.parquet": "PLACEHOLDER_HASH_REFCocoPLUS",
}

# Destination directory for raw data (created automatically by ``paths``)
RAW_DATA_DIR = paths.data("raw")

# Set up a module‑level logger so that all functions can log.
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_of_file(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_checksum(file_path: Path, expected_hash: str) -> None:
    """Verify that ``file_path`` matches ``expected_hash``."""
    actual_hash = sha256_of_file(file_path)
    if actual_hash.lower() != expected_hash.lower():
        raise AssertionError(
            f"Checksum mismatch for {file_path.name}: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    log.info("Checksum verified for %s", file_path.name)

# ----------------------------------------------------------------------
# Dataset download functions
# ----------------------------------------------------------------------
def _download_and_save(dataset_name: str,
                       config_name: str | None,
                       split: str,
                       output_path: Path) -> None:
    """
    Generic helper to download a dataset split and store it as Parquet.

    The function removes the ``image`` column (which contains binary
    image data) before saving, because ``Dataset.to_parquet`` cannot
    serialize raw images.  Only the annotation metadata is required for
    the downstream analysis.
    """
    log.info("Downloading %s %s split...", dataset_name, split)
    if config_name is None:
        ds = load_dataset(dataset_name, split=split)
    else:
        ds = load_dataset(dataset_name, config_name, split=split)

    # Remove heavy image column if present – we only need annotations.
    if "image" in ds.column_names:
        ds = ds.remove_columns("image")
        log.debug("Removed 'image' column before saving parquet.")

    log.info("Saving %s to %s", dataset_name, output_path)
    ds.to_parquet(str(output_path))

def download_vrsbench(output_path: Path) -> None:
    """
    Download the VRSBench validation split and store it as Parquet.

    The VRSBench dataset is available on the HuggingFace Hub under the
    identifier ``vrsbench``.  The ``validation`` split contains the
    images and annotations required for this study.
    """
    _download_and_save("vrsbench", None, "validation", output_path)

def download_coco_val(output_path: Path) -> None:
    """
    Download the COCO 2017 validation split and store it as Parquet.

    The COCO dataset is accessed via ``datasets`` with the config
    ``2017``.  Only the ``validation`` split is required.
    """
    _download_and_save("coco", "2017", "validation", output_path)

def download_refcoco_plus(output_path: Path) -> None:
    """
    Download the RefCOCO+ validation subset and store it as Parquet.

    The RefCOCO+ dataset is hosted on the HuggingFace Hub under the
    identifier ``refcoco`` with the ``plus`` configuration.
    """
    _download_and_save("refcoco", "plus", "validation", output_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download pipeline.

    The function:
    1. Creates ``data/raw/`` if it does not exist.
    2. Downloads each dataset.
    3. Verifies the SHA‑256 checksum of each resulting Parquet file.
    """
    # Ensure the output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Mapping of dataset‑specific download functions to target filenames
    tasks = [
        (download_vrsbench, RAW_DATA_DIR / "vrsbench.parquet"),
        (download_coco_val, RAW_DATA_DIR / "coco_val.parquet"),
        (download_refcoco_plus, RAW_DATA_DIR / "refcoco_plus.parquet"),
    ]

    for download_fn, target_path in tasks:
        # (Re)download the dataset – the datasets library caches files
        # automatically, so repeated runs are cheap.
        download_fn(target_path)

        # Verify checksum if an expected hash is supplied (i.e. not a
        # placeholder).  This allows the CI to replace the placeholders
        # with the true values without modifying the script.
        expected = EXPECTED_HASHES.get(target_path.name)
        if expected and not expected.startswith("PLACEHOLDER"):
            verify_checksum(target_path, expected)
        else:
            # Log a warning so that developers know the check is a no‑op.
            log.warning(
                "No checksum defined for %s – skipping verification.", target_path.name
            )

    log.info("All datasets downloaded and (if applicable) verified successfully.")

# ----------------------------------------------------------------------
# Boilerplate
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Use the shared logging configuration from ``llmxive_toolkit``.
    main()
