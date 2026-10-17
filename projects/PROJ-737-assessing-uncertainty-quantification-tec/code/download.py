"""
Download and prepare raw material property datasets.

This module provides utilities to download three verified CSV datasets
(Band Gap, Formation Energy, Thermal Conductivity) from HuggingFace,
cap them to a maximum of 5 000 rows deterministically, compute a SHA‑256
checksum, and write accompanying metadata JSON files as well as a
checksum manifest.

The public API matches the signatures declared in the project
specification and is used by ``code/main.py`` and the test suite
``code/tests/test_download.py``.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict

import pandas as pd
import requests

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants & Public aliases (required by the test suite)
# ----------------------------------------------------------------------
# Internal mapping used by the implementation
_DATASETS_INFO = {
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

# Public constants expected by ``code/tests/test_download.py``
DATASETS: Dict[str, Dict[str, str]] = {
    dataset_id: {"url": info["url"], "filename": f"{dataset_id}.csv"}
    for dataset_id, info in _DATASETS_INFO.items()
}

# Directory where raw CSVs are stored
DATA_RAW_DIR: Path = Path(__file__).parents[1] / "data" / "raw"

# Path to the checksum manifest file
CHECKSUM_MANIFEST: Path = DATA_RAW_DIR / "checksum_manifest.txt"

# Maximum number of rows to retain after capping
MAX_ROWS = 5_000  # hard cap for the thin pipeline (as required by T002)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(filepath: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    filepath: Path
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with filepath.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    logger.debug(f"Computed SHA‑256 for {filepath}: {checksum}")
    return checksum


def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deterministically cap a DataFrame to ``MAX_ROWS`` rows.

    The first ``MAX_ROWS`` rows are retained; this operation is
    deterministic because it does not involve any random sampling.

    Parameters
    ----------
    df: pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        Possibly truncated DataFrame with at most ``MAX_ROWS`` rows.
    """
    if len(df) <= MAX_ROWS:
        logger.debug(f"Dataset already within cap ({len(df)} ≤ {MAX_ROWS})")
        return df
    capped = df.iloc[:MAX_ROWS].reset_index(drop=True)
    logger.info(f"Capped dataset from {len(df)} to {MAX_ROWS} rows")
    return capped


def save_dataframe(df: pd.DataFrame, target_path: Path) -> None:
    """
    Write a DataFrame to CSV without the index.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame to write.
    target_path: Path
        Destination file path (including filename).
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    logger.info(f"Wrote CSV to {target_path}")


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
    Write a JSON metadata file for a downloaded dataset.

    The JSON contains the fields required by the task specification.

    Parameters
    ----------
    dataset_id: str
        Identifier of the dataset (e.g., ``band_gap``).
    source_url: str
        Exact URL used for the download.
    original_n: int
        Number of rows in the original, un‑capped CSV.
    used_n: int
        Number of rows actually written to the capped CSV.
    checksum: str
        SHA‑256 checksum of the written CSV file.
    metadata_path: Path
        Path where the JSON file will be saved.
    property_name: str
        Human‑readable name of the target property.
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
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata JSON to {metadata_path}")


def _download_csv(url: str) -> pd.DataFrame:
    """
    Download a CSV file from ``url`` using ``requests`` and return a DataFrame.

    Any HTTP error raises an exception; the caller must handle it.

    Parameters
    ----------
    url: str
        Direct URL to the CSV file.

    Returns
    -------
    pd.DataFrame
        Parsed CSV data.
    """
    logger.info(f"Downloading CSV from {url}")
    response = requests.get(url, stream=True, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.error(f"Failed to download {url}: {exc}")
        raise

    # Read the CSV directly from the response content.
    # ``pd.read_csv`` can accept a file‑like object; we use BytesIO.
    from io import BytesIO

    content = BytesIO(response.content)
    df = pd.read_csv(content)
    logger.debug(f"Downloaded {len(df)} rows from {url}")
    return df


def _download_and_save(dataset_id: str, url: str, dest_path: Path) -> pd.DataFrame:
    """
    Download a dataset CSV, write the **capped** version to ``dest_path``,
    and return the original (un‑capped) DataFrame.

    Parameters
    ----------
    dataset_id: str
        Identifier of the dataset.
    url: str
        URL to download.
    dest_path: Path
        Destination path for the capped CSV.

    Returns
    -------
    pd.DataFrame
        Original (full) DataFrame before capping.
    """
    df_full = _download_csv(url)
    original_n = len(df_full)
    df_capped = cap_dataframe(df_full)
    used_n = len(df_capped)

    # Write the capped CSV (this is what downstream code expects in ``data/raw``)
    save_dataframe(df_capped, dest_path)

    # Compute checksum of the written file
    checksum = compute_sha256(dest_path)

    # Write metadata JSON
    metadata_path = dest_path.with_name(f"{dest_path.stem}_metadata.json")
    property_name = _DATASETS_INFO[dataset_id]["property_name"]
    write_metadata(
        dataset_id=dataset_id,
        source_url=url,
        original_n=original_n,
        used_n=used_n,
        checksum=checksum,
        metadata_path=metadata_path,
        property_name=property_name,
    )
    return df_full


def download_all() -> None:
    """
    Download all required datasets, cap them, compute checksums,
    and write accompanying metadata JSON files and a checksum manifest.

    The function aborts loudly on any failure (e.g., network error,
    HTTP error, or unexpected file format) by propagating the exception.
    """
    raw_dir = DATA_RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    for dataset_id, info in _DATASETS_INFO.items():
        url = info["url"]
        dest_csv = raw_dir / f"{dataset_id}.csv"
        logger.info(f"Processing dataset '{dataset_id}'")
        # Download, cap, write CSV & metadata
        _download_and_save(dataset_id, url, dest_csv)

        # Record entry for the manifest (checksum of the capped CSV)
        checksum = compute_sha256(dest_csv)
        manifest_entries.append(f"{dataset_id},{dest_csv.name},{checksum}")

    # Write (or overwrite) the checksum manifest
    CHECKSUM_MANIFEST.write_text("\n".join(manifest_entries) + "\n")
    logger.info(f"Wrote checksum manifest to {CHECKSUM_MANIFEST}")
