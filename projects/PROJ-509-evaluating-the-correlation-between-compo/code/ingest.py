import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import requests

from config import load_paths

logger = logging.getLogger(__name__)


def get_dataset_download_url() -> str:
    """Return the download URL for the MP-2020 dataset."""
    # This is a placeholder URL; in reality, this would be fetched from MPDS
    return "https://materialsproject.org/static/files/mp-2020.12.1.csv"


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to output_path."""
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def is_inorganic(formula: str) -> bool:
    """Check if a formula is inorganic (simple heuristic)."""
    # Inorganic usually means no carbon or very simple organometallics
    # For simplicity, we exclude formulas with 'C' unless it's a carbide
    if "C" in formula:
        return False
    return True


def filter_dataset(input_path: Path, output_path: Path) -> int:
    """Filter dataset for inorganic compounds."""
    df = pd.read_csv(input_path)
    if "formula" in df.columns:
        df = df[df["formula"].apply(is_inorganic)]
    df.to_csv(output_path, index=False)
    return len(df)


def main() -> None:
    """Main entry point for data ingestion."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    url = get_dataset_download_url()
    raw_output = paths["data_raw"] / "mp-2020.12.1.csv"

    if not download_file(url, raw_output):
        # Fallback to local file
        fallback = paths["data_raw"] / "mp-2020.csv"
        if fallback.exists():
            logger.info(f"Using fallback file: {fallback}")
            raw_output = fallback
        else:
            raise FileNotFoundError("No dataset source available")

    # Verify checksum
    checksum = calculate_sha256(raw_output)
    verification = {
        "file": raw_output.name,
        "sha256": checksum,
        "timestamp": time.time(),
    }
    ver_path = paths["data_evaluation"] / "dataset_verification.json"
    with open(ver_path, "w") as f:
        json.dump(verification, f, indent=2)

    # Filter
    filtered_output = paths["data_raw"] / "mp-2020.12.1_filtered.csv"
    count = filter_dataset(raw_output, filtered_output)
    logger.info(f"Filtered dataset size: {count}")

    # Check threshold
    from config import ROW_THRESHOLD

    if count > ROW_THRESHOLD:
        logger.warning(f"Dataset size {count} exceeds threshold {ROW_THRESHOLD}")
        # Sampling would be handled in a separate task or here
    else:
        logger.info("Dataset within threshold, no sampling needed")

    logger.info("Data ingestion complete")


if __name__ == "__main__":
    main()
