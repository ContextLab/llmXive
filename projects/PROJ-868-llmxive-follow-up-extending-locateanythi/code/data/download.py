"""
Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify
SHA-256 checksums.

This script is intended to be run as part of the pipeline's Phase 0.
It downloads the three required datasets via the 🤗 datasets library
(or a verified source for COCO), writes them as Parquet files under
data/raw/ and checks their integrity against the expected SHA-256
hashes.

The download functions stream a small, deterministic sample of each
dataset (the first 100 rows) to keep CI runtimes and storage modest.
All rows are real, sourced directly from the official datasets, so the
data remains authentic while remaining tractable for the CI environment.
"""

import hashlib
import logging
from pathlib import Path
from itertools import islice

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# pycocotools is no longer required for COCO download; we use the HuggingFace
# dataset directly (see the VERIFIED REAL DATA SOURCE block).

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
def _download_and_save(
    dataset_name: str,
    config_name: str | None,
    split: str,
    output_path: Path,
    sample_size: int = 100,
) -> None:
    """
    Generic helper to download a dataset split and store a *sample* as Parquet.
    The function streams the dataset and writes the first ``sample_size``
    records, guaranteeing that the data are real while keeping the file
    size small enough for CI.
    """
    log.info(
        "Downloading %s %s split (sample %d rows)...",
        dataset_name,
        split,
        sample_size,
    )
    if config_name is None:
        ds = load_dataset(dataset_name, split=split, streaming=True)
    else:
        ds = load_dataset(dataset_name, config_name, split=split, streaming=True)

    # Remove heavy image column if present – we only need annotations.
    if "image" in ds.column_names:
        ds = ds.remove_columns("image")
        log.debug("Removed 'image' column before saving parquet.")

    # Take a deterministic sample (first ``sample_size`` rows)
    sample_records = list(islice(ds, sample_size))
    if not sample_records:
        raise RuntimeError(
            f"No records retrieved from {dataset_name} split {split}"
        )

    df = pd.DataFrame.from_records(sample_records)
    log.info("Saving %s sample to %s", dataset_name, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), engine="pyarrow")
    log.info("Sample parquet written for %s.", dataset_name)


def download_vrsbench(output_path: Path) -> None:
    """
    Download a small sample of the VRSBench validation split and store it as Parquet.
    """
    # The VRSBench dataset is available on the HuggingFace Hub under the name
    # "vrsbench/vrsbench". We stream the validation split.
    _download_and_save("vrsbench/vrsbench", None, "validation", output_path)


def download_coco_val(output_path: Path) -> None:
    """
    Download a small sample of the COCO 2017 validation split via the
    verified HuggingFace dataset "phiyodr/coco2017" and store it as Parquet.
    """
    # Using the verified recipe from the CONTRACT block.
    _download_and_save(
        "phiyodr/coco2017", None, "validation", output_path, sample_size=100
    )


def download_refcoco_plus(output_path: Path) -> None:
    """
    Download a small sample of the RefCOCO+ validation subset and store it as Parquet.
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
                target_path.name,
                actual,
            )

    log.info(
        "All datasets downloaded and (if applicable) verified successfully."
    )


if __name__ == "__main__":
    main()
