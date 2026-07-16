"""
Module: 01_data_download.py
Description:
    Handles downloading the QM9 dataset from the verified HuggingFace repository
    (`lisn/QM9`), validates its integrity, and parses/filters the raw data into a
    cleaned parquet file ready for downstream processing.
This implementation removes any debug ``print`` statements and adds comprehensive
type hints for all public functions.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import load_dataset
from huggingface_hub import hf_hub_download

# Configure module‑level logger
logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified hashing algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm supported by :pymod:`hashlib` (default ``sha256``).

    Returns:
        Hexadecimal checksum string.
    """
    logger.debug("Computing %s checksum for %s", algorithm, file_path)
    hasher = hashlib.new(algorithm)
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    checksum = hasher.hexdigest()
    logger.debug("Checksum for %s: %s", file_path, checksum)
    return checksum


def validate_data_integrity(parquet_path: Path, required_columns: Optional[List[str]] = None) -> bool:
    """
    Validate that the parquet file contains the required QM9 columns.

    Args:
        parquet_path: Path to the parquet file.
        required_columns: List of column names that must be present. If ``None``,
            a default set of DFT‑related columns is used.

    Returns:
        ``True`` if all required columns exist and contain no NaNs, ``False`` otherwise.
    """
    logger.info("Validating data integrity for %s", parquet_path)
    df = pd.read_parquet(parquet_path)
    if required_columns is None:
        required_columns = ["dipole_moment", "homo", "lumo"]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error("Missing required columns: %s", missing)
        return False

    # Ensure no NaNs in required columns
    if df[required_columns].isnull().any().any():
        logger.error("NaN values found in required columns.")
        return False

    logger.info("Data integrity check passed.")
    return True


def download_qm9_dataset(destination: Path) -> Path:
    """
    Download the QM9 dataset from HuggingFace and store it as a parquet file.

    Args:
        destination: Directory where the dataset file will be saved.

    Returns:
        Path to the downloaded parquet file.

    Raises:
        RuntimeError: If the download fails.
    """
    logger.info("Downloading QM9 dataset from HuggingFace (lisn/QM9).")
    destination.mkdir(parents=True, exist_ok=True)

    # The HF repo provides a parquet file named ``qm9.parquet``.
    # Using ``hf_hub_download`` ensures we get the exact file without needing the
    # ``datasets`` library to materialise the whole dataset in memory.
    try:
        parquet_file = hf_hub_download(
            repo_id="lisn/QM9",
            filename="qm9.parquet",
            cache_dir=str(destination),
        )
    except Exception as exc:
        logger.exception("Failed to download QM9 dataset.")
        raise RuntimeError("Could not download QM9 dataset.") from exc

    target_path = destination / "qm9_full.parquet"
    # Move the cached file to the canonical location
    Path(parquet_file).rename(target_path)
    logger.info("Dataset downloaded to %s", target_path)
    return target_path


def parse_and_validate(raw_parquet: Path, cleaned_parquet: Path) -> None:
    """
    Parse the raw QM9 parquet file, drop rows with missing DFT labels or invalid
    geometry, and write the cleaned result.

    Args:
        raw_parquet: Path to the raw dataset parquet file.
        cleaned_parquet: Path where the cleaned parquet will be written.
    """
    logger.info("Parsing and validating %s", raw_parquet)
    df = pd.read_parquet(raw_parquet)

    # Required columns for downstream tasks
    required = ["dipole_moment", "homo", "lumo", "coordinates"]
    # Keep rows where required columns are non‑null
    before = len(df)
    df_clean = df.dropna(subset=required)
    after = len(df_clean)
    logger.info("Dropped %d rows with missing required data.", before - after)

    # Simple geometry sanity check: ensure coordinates shape is (n_atoms, 3)
    def geometry_is_valid(coord: Any) -> bool:
        try:
            arr = pd.DataFrame(coord).values
            return arr.ndim == 2 and arr.shape[1] == 3
        except Exception:
            return False

    df_clean = df_clean[df_clean["coordinates"].apply(geometry_is_valid)]
    logger.info("Rows after geometry validation: %d", len(df_clean))

    df_clean.to_parquet(cleaned_parquet, index=False)
    logger.info("Cleaned dataset written to %s", cleaned_parquet)


def main() -> None:
    """
    Entry point for the data‑download pipeline.
    Executes the full workflow: download → checksum → integrity validation →
    parsing/cleaning.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )

    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download
    raw_parquet = download_qm9_dataset(raw_dir)

    # 2. Compute & store checksum
    checksum = compute_file_checksum(raw_parquet)
    checksum_path = Path("data/checksums.json")
    checksum_path.write_text(json.dumps({str(raw_parquet): checksum}, indent=2))
    logger.info("Checksum saved to %s", checksum_path)

    # 3. Validate raw integrity
    if not validate_data_integrity(raw_parquet):
        raise RuntimeError("Raw QM9 data failed integrity checks.")

    # 4. Parse, clean, and write filtered dataset
    cleaned_path = processed_dir / "molecules_cleaned.parquet"
    parse_and_validate(raw_parquet, cleaned_path)

    # 5. Final integrity check on cleaned data
    if not validate_data_integrity(cleaned_path):
        raise RuntimeError("Cleaned QM9 data failed integrity checks.")

    logger.info("Data download and preprocessing completed successfully.")


if __name__ == "__main__":
    main()
