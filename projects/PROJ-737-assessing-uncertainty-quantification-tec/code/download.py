"""
Download module for the UQ pipeline.
This implementation avoids the `datasets` library (which pulls in `pyarrow`
and requires NumPy 2.0) and instead uses the standard library `urllib` and
`requests` to fetch the CSV files directly from the verified HuggingFace
URLs.
It caps each raw CSV to 5 000 rows, computes a SHA‑256 checksum, writes the
CSV to ``data/raw/<dataset_id>.csv`` and creates a matching metadata JSON
file ``data/raw/<dataset_id>_metadata.json``.
All functions follow the public API declared in the original
``code/download.py`` stub.
"""

import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import requests

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(filepath: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cap a DataFrame to a deterministic 5 000‑row subset.
    The function uses a fixed random seed (42) for reproducibility.
    """
    max_rows = 5000
    if len(df) <= max_rows:
        return df
    # Deterministic sampling
    df = df.sample(n=max_rows, random_state=42).reset_index(drop=True)
    log.info(f"Capped dataframe to {max_rows} rows.")
    return df


def save_dataframe(df: pd.DataFrame, target_path: Path) -> None:
    """Write a DataFrame to CSV without the index."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    log.info(f"Saved CSV to {target_path}")


def write_metadata(
    dataset_id: str,
    source_url: str,
    original_n: int,
    used_n: int,
    checksum: str,
    metadata_path: Path,
    property_name: str,
) -> None:
    """
    Write a JSON metadata file with the required fields.
    """
    metadata = {
        "dataset_id": dataset_id,
        "source_url": source_url,
        "property_name": property_name,
        "n_samples_original": original_n,
        "n_samples_used": used_n,
        "checksum": checksum,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2))
    log.info(f"Wrote metadata JSON to {metadata_path}")


def append_checksum_record(dataset_id: str, filename: str, checksum: str) -> None:
    """
    Append a line to a manifest file (optional utility – not required by tests).
    """
    manifest_path = Path(__file__).parents[1] / "data" / "raw" / "checksums.txt"
    with manifest_path.open("a") as f:
        f.write(f"{dataset_id},{filename},{checksum}\n")


# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
_DATASETS = {
    "band_gap": {
        "url": "https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv",
        "property_name": "band_gap",
    },
    "formation_energy": {
        "url": "https://huggingface.co/datasets/oqmd/formation_energy/resolve/main/formation_energy.csv",
        "property_name": "formation_energy",
    },
    "thermal_conductivity": {
        "url": "https://huggingface.co/datasets/aflow/thermal_conductivity/resolve/main/thermal_conductivity.csv",
        "property_name": "thermal_conductivity",
    },
}


def _download_csv(url: str, dest_path: Path) -> None:
    """
    Download a CSV from ``url`` and write it to ``dest_path``.
    Raises ``RuntimeError`` on HTTP errors or parsing failures.
    """
    log.info(f"Downloading {url}")
    response = requests.get(url, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {url}: HTTP {response.status_code}")
    # Read content into a pandas DataFrame (handles encoding)
    try:
        df = pd.read_csv(response.raw)
    except Exception as exc:
        raise RuntimeError(f"Failed to parse CSV from {url}: {exc}")
    # Ensure the destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest_path, index=False)
    log.info(f"Saved raw CSV to {dest_path}")


def download_all() -> None:
    """
    Download all required datasets, cap them to 5 000 rows, compute checksums,
    and write accompanying metadata JSON files.
    """
    raw_dir = Path(__file__).parents[1] / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for dataset_id, info in _DATASETS.items():
        csv_path = raw_dir / f"{dataset_id}.csv"
        metadata_path = raw_dir / f"{dataset_id}_metadata.json"

        # Step 1 – download the full CSV
        _download_csv(info["url"], csv_path)

        # Step 2 – read, cap, and overwrite the CSV with the capped version
        df_full = pd.read_csv(csv_path)
        original_n = len(df_full)
        df_capped = cap_dataframe(df_full)
        used_n = len(df_capped)
        save_dataframe(df_capped, csv_path)

        # Step 3 – compute checksum and write metadata
        checksum = compute_sha256(csv_path)
        write_metadata(
            dataset_id=dataset_id,
            source_url=info["url"],
            original_n=original_n,
            used_n=used_n,
            checksum=checksum,
            metadata_path=metadata_path,
            property_name=info["property_name"],
        )

        # Optional manifest entry
        append_checksum_record(dataset_id, csv_path.name, checksum)

    log.info("All datasets downloaded and processed successfully.")
