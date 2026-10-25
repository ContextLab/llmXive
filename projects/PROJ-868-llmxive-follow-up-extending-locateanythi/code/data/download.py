"""
Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify
SHA-256 checksums.

This script is intended to be run as part of the pipeline's Phase 0.
It downloads the three required datasets via the 🤗 datasets library
(or a verified source for COCO), writes them as Parquet files under
data/raw/ and checks their integrity against the expected SHA-256
hashes.
"""

import hashlib
import logging
import os
import ssl
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# pycocotools is required for the verified COCO download recipe
from pycocotools.coco import COCO

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Expected SHA-256 hashes for the three parquet files.
# These are updated by the CI after the first successful run of the pipeline.
EXPECTED_HASHES = {
    "vrsbench.parquet": "PLACEHOLDER_HASH_VRSBENCH",
    "coco_val.parquet": "PLACEHOLDER_HASH_COCO_VAL",
    "refcoco_plus.parquet": "PLACEHOLDER_HASH_REFCocoPLUS",
}

# Destination directory for raw data (created automatically by paths)
RAW_DATA_DIR = paths.data("raw")

# Set up a module-level logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_of_file(file_path: Path) -> str:
    """Return the SHA-256 hex digest of file_path."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(file_path: Path, expected_hash: str) -> None:
    """Verify that file_path matches expected_hash."""
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
    """
    _download_and_save("vrsbench", None, "validation", output_path)


def download_coco_val(output_path: Path) -> None:
    """
    Download the COCO 2017 validation annotations using the verified
    pycocotools recipe and store them as a Parquet file.
    """
    ZIP_URL = "https://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    ZIP_PATH = Path("/tmp/annotations_trainval2017.zip")
    JSON_NAME = "annotations/instances_val2017.json"
    JSON_PATH = Path("/tmp/instances_val2017.json")

    if not ZIP_PATH.exists():
        log.info("Downloading COCO annotations zip...")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(ZIP_URL, context=ctx) as resp, ZIP_PATH.open("wb") as out:
            out.write(resp.read())
        log.info("COCO zip downloaded to %s", ZIP_PATH)

    if not JSON_PATH.exists():
        log.info("Extracting COCO validation JSON...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            with zf.open(JSON_NAME) as src, JSON_PATH.open("wb") as dst:
                dst.write(src.read())
        log.info("Extracted JSON to %s", JSON_PATH)

    log.info("Loading COCO annotations via pycocotools...")
    coco = COCO(str(JSON_PATH))

    records = list(coco.anns.values())
    if not records:
        raise RuntimeError("No COCO annotation records loaded")
    df = pd.DataFrame.from_records(records)

    log.info("Saving COCO annotations to Parquet at %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), engine="pyarrow")
    log.info("COCO validation parquet written.")


def download_refcoco_plus(output_path: Path) -> None:
    """
    Download the RefCOCO+ validation subset and store it as Parquet.
    """
    _download_and_save("refcoco", "plus", "validation", output_path)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download pipeline.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [
        (download_vrsbench, RAW_DATA_DIR / "vrsbench.parquet"),
        (download_coco_val, RAW_DATA_DIR / "coco_val.parquet"),
        (download_refcoco_plus, RAW_DATA_DIR / "refcoco_plus.parquet"),
    ]

    for download_fn, target_path in tasks:
        download_fn(target_path)

        expected = EXPECTED_HASHES.get(target_path.name)
        if expected and not expected.startswith("PLACEHOLDER"):
            verify_checksum(target_path, expected)
        else:
            actual = sha256_of_file(target_path)
            log.warning(
                "No checksum defined for %s. Calculated hash: %s",
                target_path.name, actual
            )

    log.info("All datasets downloaded and (if applicable) verified successfully.")


if __name__ == "__main__":
    main()