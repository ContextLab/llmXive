"""
Download module for the UQ pipeline.
Fetches three materials datasets from HuggingFace using the `datasets` library,
caps them to a deterministic 5 000‑row subset, computes SHA‑256 checksums,
and writes accompanying metadata JSON files.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

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
    Cap the dataframe to a deterministic 5 000‑row subset.
    Uses a fixed random seed (42) for reproducibility.
    """
    max_rows = 5000
    if len(df) <= max_rows:
        return df

    df = df.sample(n=max_rows, random_state=42).reset_index(drop=True)
    log.info(f"Capped dataframe to {max_rows} rows")
    return df


def save_dataframe(df: pd.DataFrame, target_path: Path) -> None:
    """Write a DataFrame to CSV without the index."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    log.info(f"Wrote CSV to {target_path}")


def write_metadata(
    dataset_id: str,
    source_url: str,
    original_n: int,
    used_n: int,
    checksum: str,
    metadata_path: Path,
    property_name: str,
) -> None:
    """Write a JSON metadata file with the required fields."""
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
    log.info(f"Wrote metadata to {metadata_path}")


# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
_DATASET_SPECS: Dict[str, Dict[str, Any]] = {
    "band_gap": {
        "repo": "oqmd/band_gap",
        "property_name": "band_gap",
        "source_url": "https://huggingface.co/datasets/oqmd/band_gap",
    },
    "formation_energy": {
        "repo": "oqmd/formation_energy",
        "property_name": "formation_energy",
        "source_url": "https://huggingface.co/datasets/oqmd/formation_energy",
    },
    "thermal_conductivity": {
        "repo": "aflow/thermal_conductivity",
        "property_name": "thermal_conductivity",
        "source_url": "https://huggingface.co/datasets/aflow/thermal_conductivity",
    },
}


def _download_and_save(dataset_id: str, repo: str, dest_path: Path) -> pd.DataFrame:
    """
    Download a dataset from the HuggingFace hub using the ``datasets`` library,
    convert it to a pandas DataFrame, and write it as CSV to ``dest_path``.
    Returns the loaded DataFrame.
    """
    log.info(f"Downloading dataset '{dataset_id}' from repo '{repo}'")
    # Load the full training split (most datasets expose a single split named 'train')
    ds = load_dataset(repo, split="train")
    df = ds.to_pandas()
    save_dataframe(df, dest_path)
    return df


def download_all() -> None:
    """
    Download all required datasets, cap them to 5 000 rows,
    compute checksums, and write metadata JSON files.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for dataset_id, spec in _DATASET_SPECS.items():
        csv_path = raw_dir / f"{dataset_id}.csv"
        metadata_path = raw_dir / f"{dataset_id}_metadata.json"

        # Step 1 – download raw CSV (or fetch via datasets)
        df = _download_and_save(dataset_id, spec["repo"], csv_path)

        # Record original size before capping
        original_n = len(df)

        # Step 2 – cap to deterministic 5 000 rows
        df_capped = cap_dataframe(df)

        # Overwrite the CSV with the capped version
        save_dataframe(df_capped, csv_path)

        # Step 3 – compute checksum of the capped CSV
        checksum = compute_sha256(csv_path)

        # Step 4 – write metadata JSON
        write_metadata(
            dataset_id=dataset_id,
            source_url=spec["source_url"],
            original_n=original_n,
            used_n=len(df_capped),
            checksum=checksum,
            metadata_path=metadata_path,
            property_name=spec["property_name"],
        )
