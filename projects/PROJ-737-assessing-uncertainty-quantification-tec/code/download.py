"""
Download module for fetching real materials datasets.

This implementation follows the specification for task T002:
- Downloads three CSV files from the verified HuggingFace URLs using the
  `datasets` library (which handles authentication and streaming).
- Writes each file to ``data/raw/<dataset_id>.csv``.
- Caps each dataset to 5 000 samples deterministically (seed 42) using
  ``pandas.DataFrame.sample``.
- Computes a SHA‑256 checksum for the saved (capped) file.
- Writes a JSON metadata file ``data/raw/<dataset_id>_metadata.json`` with
  the required fields: ``dataset_id``, ``source_url``, ``property_name``,
  ``n_samples_original``, ``n_samples_used``, ``checksum``.
- Appends a line to ``data/raw/sha256_manifest.txt`` containing
  ``dataset_id,filename,checksum``.
- Raises an exception on persistent failure *after* any successfully
  downloaded files have been written, satisfying the specification's
  “raise after writing any successfully downloaded files” requirement.

The URLs are kept in ``DATASETS`` for provenance; the actual download is
performed via ``datasets.load_dataset`` which reliably fetches the public
CSVs without needing manual HTTP authentication.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DATA_RAW_DIR: Path = paths.data("raw")
CHECKSUM_MANIFEST: Path = DATA_RAW_DIR / "sha256_manifest.txt"

SAMPLE_CAP: int = 5_000
RANDOM_SEED: int = 42

# ----------------------------------------------------------------------
# Mapping of internal dataset identifiers to their public URLs and target filenames
# ----------------------------------------------------------------------
DATASETS: Dict[str, Dict[str, Any]] = {
    "band_gap": {
        "source_url": "https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv",
        "filename": "band_gap.csv",
        "property_name": "band_gap",
        "description": "OQMD band gap dataset",
    },
    "formation_energy": {
        "source_url": "https://huggingface.co/datasets/oqmd/formation_energy/resolve/main/formation_energy.csv",
        "filename": "formation_energy.csv",
        "property_name": "formation_energy_per_atom",
        "description": "OQMD formation energy dataset (per atom)",
    },
    "thermal_conductivity": {
        "source_url": "https://huggingface.co/datasets/aflow/thermal_conductivity/resolve/main/thermal_conductivity.csv",
        "filename": "thermal_conductivity.csv",
        "property_name": "thermal_conductivity",
        "description": "AFLOW thermal conductivity dataset",
    },
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(filepath: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Cap a DataFrame to ``SAMPLE_CAP`` rows using a deterministic seed."""
    original_len = len(df)
    if original_len > SAMPLE_CAP:
        logger.info(
            f"Capping dataset from {original_len} to {SAMPLE_CAP} rows (seed={RANDOM_SEED})"
        )
        df_capped = df.sample(
            n=SAMPLE_CAP, random_state=RANDOM_SEED
        ).reset_index(drop=True)
        return df_capped
    else:
        logger.info(f"Dataset size ({original_len}) within cap; no capping applied")
        return df


def save_dataframe(df: pd.DataFrame, target_path: Path) -> None:
    """Write a DataFrame to CSV without the index."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    logger.info(f"Saved dataset to {target_path}")


def write_metadata(
    dataset_id: str,
    source_url: str,
    original_n: int,
    used_n: int,
    checksum: str,
    metadata_path: Path,
    property_name: str,
) -> None:
    """Write the required JSON metadata file."""
    metadata = {
        "dataset_id": dataset_id,
        "source_url": source_url,
        "property_name": property_name,
        "n_samples_original": original_n,
        "n_samples_used": used_n,
        "checksum": checksum,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata JSON to {metadata_path}")


def append_checksum_record(dataset_id: str, filename: str, checksum: str) -> None:
    """Append a line to the SHA‑256 manifest file."""
    CHECKSUM_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_MANIFEST, "a", encoding="utf-8") as f:
        f.write(f"{dataset_id},{filename},{checksum}\\n")
    logger.info(f"Appended checksum record for {filename}")


# ----------------------------------------------------------------------
# Main public function
# ----------------------------------------------------------------------
def download_all() -> None:
    """
    Download all required datasets, enforce the deterministic cap, compute
    checksums, and write metadata files.

    On persistent failure for any dataset, an exception is raised **after**
    any successfully downloaded files have been written, satisfying the
    specification's “raise after writing any successfully downloaded files”
    requirement.
    """
    logger.info("Starting download of all required datasets.")

    # Ensure the raw data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Reset manifest file
    if CHECKSUM_MANIFEST.exists():
        CHECKSUM_MANIFEST.unlink()

    for dataset_id, cfg in DATASETS.items():
        source_url = cfg["source_url"]
        filename = cfg["filename"]
        property_name = cfg.get("property_name", "")
        csv_path = DATA_RAW_DIR / filename
        metadata_path = DATA_RAW_DIR / f"{dataset_id}_metadata.json"

        try:
            # ------------------------------------------------------------------
            # 1. Load the dataset via the HuggingFace `datasets` library.
            #    The identifier for the library is the part after the domain,
            #    e.g. "oqmd/band_gap".
            # ------------------------------------------------------------------
            hf_identifier = source_url.split("datasets/")[1].split("/resolve")[0]
            logger.info(f"Loading dataset '{hf_identifier}' via `datasets` library.")
            # Load the full split (usually named 'train'); streaming is not needed
            # because we later cap to 5 000 rows.
            ds = load_dataset(hf_identifier, split="train")
            df_raw = ds.to_pandas()
            original_n = int(df_raw.shape[0])

            # ------------------------------------------------------------------
            # 2. Apply deterministic cap
            # ------------------------------------------------------------------
            df_capped = cap_dataframe(df_raw)
            used_n = int(df_capped.shape[0])

            # ------------------------------------------------------------------
            # 3. Write the capped CSV (overwrites any previous version)
            # ------------------------------------------------------------------
            save_dataframe(df_capped, csv_path)

            # ------------------------------------------------------------------
            # 4. Compute checksum on the saved (capped) file
            # ------------------------------------------------------------------
            checksum = compute_sha256(csv_path)

            # ------------------------------------------------------------------
            # 5. Record checksum manifest
            # ------------------------------------------------------------------
            append_checksum_record(dataset_id, filename, checksum)

            # ------------------------------------------------------------------
            # 6. Write metadata JSON
            # ------------------------------------------------------------------
            write_metadata(
                dataset_id=dataset_id,
                source_url=source_url,
                original_n=original_n,
                used_n=used_n,
                checksum=checksum,
                metadata_path=metadata_path,
                property_name=property_name,
            )
        except Exception as e:
            logger.error(f"Failed processing dataset '{dataset_id}': {e}")
            # Propagate as a RuntimeError to satisfy the contract.
            raise RuntimeError(f"Dataset download failed for '{dataset_id}'") from e

    logger.info("All datasets downloaded, capped, and metadata written successfully.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    download_all()
