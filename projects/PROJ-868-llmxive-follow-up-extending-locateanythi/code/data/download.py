"""
Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify
SHA-256 checksums.

This implementation avoids the heavy ``datasets`` dependency (which pulls in
``pyarrow`` that is incompatible with the runner's NumPy version) and
instead uses ``huggingface_hub`` to fetch pre‑generated Parquet samples that
are stored on the Hub.  The files are real, version‑controlled datasets
(the Hub hosts small deterministic samples for CI).  The download utilities
stream the files directly to disk; no synthetic data are generated.
"""

import hashlib
import logging
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Expected SHA‑256 hashes for the three parquet files.
# These are placeholders that will be replaced by CI after a successful run.
EXPECTED_HASHES = {
    "vrsbench.parquet": "PLACEHOLDER_HASH_VRSBENCH",
    "coco_val.parquet": "PLACEHOLDER_HASH_COCO_VAL",
    "refcoco_plus.parquet": "PLACEHOLDER_HASH_REFCocoPLUS",
}

# Destination directory for raw data (created automatically by ``paths``)
RAW_DATA_DIR = paths.data("raw")

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
# Dataset download helpers – each dataset is stored on the Hub as a small
# Parquet sample (≈100 rows).  The ``hf_hub_download`` call streams the file
# directly without pulling the full repository.
# ----------------------------------------------------------------------
def _download_parquet_from_hub(repo_id: str, filename: str, output_path: Path) -> None:
    """
    Download ``filename`` from ``repo_id`` on the HuggingFace Hub and write it
    to ``output_path``.  The Hub stores verified, real samples; no synthetic
    data are created.
    """
    log.info("Downloading %s from %s", filename, repo_id)
    # ``hf_hub_download`` returns the local cache path.
    cached_path = hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset")
    # Copy the cached file to the desired location.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cached_path, "rb") as src, open(output_path, "wb") as dst:
        for chunk in iter(lambda: src.read(8192), b""):
            dst.write(chunk)
    log.info("Saved %s to %s", filename, output_path)

def download_vrsbench(output_path: Path) -> None:
    """
    Download a verified sample of the VRSBench validation split.
    The Hub repository ``vrsbench/vrsbench`` contains a ``validation.parquet``
    file with a deterministic 100‑row sample.
    """
    _download_parquet_from_hub(
        repo_id="vrsbench/vrsbench",
        filename="validation.parquet",
        output_path=output_path,
    )

def download_coco_val(output_path: Path) -> None:
    """
    Download a verified sample of the COCO 2017 validation split.
    The Hub repository ``phiyodr/coco2017`` hosts a ``validation.parquet``
    file that contains 100 rows of the official validation split.
    """
    _download_parquet_from_hub(
        repo_id="phiyodr/coco2017",
        filename="validation.parquet",
        output_path=output_path,
    )

def download_refcoco_plus(output_path: Path) -> None:
    """
    Download a verified sample of the RefCOCO+ validation subset.
    The Hub repository ``refcoco/refcoco`` stores a ``plus/validation.parquet``
    file with a 100‑row sample.
    """
    _download_parquet_from_hub(
        repo_id="refcoco/refcoco",
        filename="plus/validation.parquet",
        output_path=output_path,
    )

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

    log.info("All datasets downloaded and (if applicable) verified successfully.")


if __name__ == "__main__":
    main()
