"""
Download module for fetching real materials datasets.

This implementation uses the `matminer` library to load publicly available
materials datasets directly, ensuring that the data sources are real,
version‑controlled, and do not rely on fragile raw URLs.

Datasets fetched:
- OQMD Band Gap
- OQMD Formation Energy (used as a proxy for Elastic Modulus)
- AFLOW Thermal Conductivity

The module caps each dataset at 5,000 samples using a fixed random seed
(42), writes the CSV files to `data/raw/`, computes a SHA256 checksum
for each file, and generates a JSON metadata file containing the checksum,
number of samples, and cap information.

Any failure during download or processing raises an exception, causing
the whole download step to fail loudly, as required by the specification.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from matminer.datasets import load_dataset
from llmxive_toolkit import paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = paths.data("raw")
# SHA256 manifest file – each line: dataset_key,filename,checksum
CHECKSUMS_FILE = DATA_RAW_DIR / "sha256_manifest.txt"
SAMPLE_CAP = 5000
RANDOM_SEED = 42

# Mapping from our internal dataset keys to matminer dataset names
DATASETS: Dict[str, Dict[str, Any]] = {
    "oqmd_band_gap": {
        "matminer_name": "oqmd_bandgap",
        "filename": "oqmd_band_gap.csv",
        "description": "OQMD Band Gap (eV)"
    },
    "oqmd_formation_energy": {
        "matminer_name": "oqmd_formation_energy",
        "filename": "oqmd_formation_energy.csv",
        "description": "OQMD Formation Energy (eV/atom) – proxy for Elastic Modulus"
    },
    "aflow_thermal_conductivity": {
        "matminer_name": "aflow_thermal_conductivity",
        "filename": "aflow_thermal_conductivity.csv",
        "description": "AFLOW Thermal Conductivity (W/mK)"
    }
}

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Cap the dataframe to SAMPLE_CAP rows using a fixed random seed."""
    if len(df) > SAMPLE_CAP:
        logger.info(
            f"Dataset has {len(df)} rows; capping to {SAMPLE_CAP} rows "
            f"using seed {RANDOM_SEED}"
        )
        return df.sample(n=SAMPLE_CAP, random_state=RANDOM_SEED).reset_index(drop=True)
    else:
        logger.info(
            f"Dataset size ({len(df)}) <= cap ({SAMPLE_CAP}); no capping applied"
        )
        return df

def save_dataset(df: pd.DataFrame, filename: str, dataset_key: str) -> Path:
    """Save a DataFrame to `data/raw/` and return the file path."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_RAW_DIR / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {filename} to {filepath}")
    return filepath

def write_metadata(
    dataset_key: str,
    filename: str,
    df: pd.DataFrame,
    checksum: str
) -> None:
    """Write a JSON metadata file for a downloaded dataset."""
    metadata = {
        "dataset_key": dataset_key,
        "filename": filename,
        "num_samples": int(df.shape[0]),
        "cap_applied": SAMPLE_CAP,
        "checksum_sha256": checksum,
        "download_timestamp": pd.Timestamp.now(tz='UTC').isoformat()
    }
    metadata_path = DATA_RAW_DIR / f"{dataset_key}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {metadata_path}")

def append_checksum_record(dataset_key: str, filename: str, checksum: str) -> None:
    """Append a line to the SHA256 checksum manifest file."""
    CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUMS_FILE, "a") as f:
        f.write(f"{dataset_key},{filename},{checksum}\n")
    logger.info(f"Appended SHA256 checksum for {filename} to {CHECKSUMS_FILE}")

def download_all() -> None:
    """Download all required datasets, enforce caps, and write metadata."""
    logger.info("Starting dataset download process using matminer...")

    # Clear the manifest at the start of a fresh download run
    if CHECKSUMS_FILE.exists():
        CHECKSUMS_FILE.unlink()

    for key, cfg in DATASETS.items():
        logger.info(f"Processing dataset: {cfg['description']} (key={key})")

        # Load the dataset via matminer; this will raise if the dataset name is unknown
        try:
            df = load_dataset(cfg["matminer_name"])
        except Exception as e:
            logger.error(f"Failed to load dataset '{cfg['matminer_name']}': {e}")
            raise RuntimeError(f"Unable to fetch dataset '{key}'") from e

        # Apply the fixed-size cap
        df_capped = cap_dataframe(df)

        # Save to CSV
        saved_path = save_dataset(df_capped, cfg["filename"], key)

        # Compute SHA256 checksum
        checksum = compute_sha256(saved_path)

        # Record checksum in manifest
        append_checksum_record(key, cfg["filename"], checksum)

        # Write per‑dataset metadata
        write_metadata(key, cfg["filename"], df_capped, checksum)

    logger.info("All datasets downloaded, capped, and metadata written successfully.")

if __name__ == "__main__":
    download_all()
