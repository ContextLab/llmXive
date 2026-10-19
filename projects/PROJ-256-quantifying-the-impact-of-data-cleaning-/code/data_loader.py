"""
Data acquisition utilities for T005.
Downloads a set of verified datasets (via OpenML or direct URLs),
writes each to CSV in the raw data directory, computes SHA‑256 checksums,
validates the generated metadata against ``contracts/dataset.schema.yaml``,
and writes a consolidated ``dataset_metadata.json`` file to the processed
data directory.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict

import openml
import pandas as pd
import jsonschema

from config import get_config
from utils import setup_logging, compute_file_checksum

logger = setup_logging(log_level="INFO")

# ----------------------------------------------------------------------
# Dataset specifications
# ----------------------------------------------------------------------
# Each entry defines:
#   - name: human‑readable identifier
#   - openml_id: OpenML dataset identifier (or None if a direct URL is used)
#   - outcome_column: documented outcome variable name
#   - url: optional direct download URL for CSV datasets
# ----------------------------------------------------------------------
DATASET_SPECS: List[Dict] = [
    {
        "name": "Iris",
        "openml_id": 61,
        "outcome_column": "outcome",
        "url": None,
    },
    {
        "name": "Wine Quality",
        "openml_id": 1862,
        "outcome_column": "quality",
        "url": None,
    },
    {
        "name": "Breast Cancer Wisconsin Diagnostic",
        "openml_id": 151,
        "outcome_column": "diagnosis",
        "url": None,
    },
    {
        "name": "Heart Disease",
        "openml_id": 53,
        "outcome_column": "target",
        "url": None,
    },
    {
        "name": "Parkinsons Telemonitoring",
        "openml_id": 167124,
        "outcome_column": "total_UPDRS",
        "url": None,
    },
    {
        "name": "Diabetes",
        "openml_id": 531,
        "outcome_column": "progression",
        "url": None,
    },
    {
        "name": "German Credit",
        "openml_id": 31,
        "outcome_column": "credit_risk",
        "url": None,
    },
    {
        "name": "Adult Income",
        "openml_id": 1590,
        "outcome_column": "income",
        "url": None,
    },
    {
        "name": "Student Performance",
        "openml_id": 40945,
        "outcome_column": "G",
        "url": None,
    },
    # Two additional example CSV datasets from UCI (direct URLs)
    {
        "name": "Ionosphere",
        "openml_id": None,
        "outcome_column": "target",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
    },
    {
        "name": "Car Evaluation",
        "openml_id": None,
        "outcome_column": "class_value",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/car/car.data",
    },
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_openml_dataset(openml_id: int, raw_dir: Path) -> Path:
    """
    Download a dataset from OpenML, store it as ``<openml_id>.csv`` in ``raw_dir``,
    and return the path to the written CSV file.
    """
    logger.info(f"Downloading OpenML dataset ID {openml_id}")
    dataset = openml.datasets.get_dataset(openml_id)
    X, y, _, _ = dataset.get_data(dataset_format="dataframe")
    df = X.copy()
    # Ensure the target column exists; name it ``outcome`` if not already present.
    if y.name not in df.columns:
        df[y.name] = y
    csv_path = raw_dir / f"{openml_id}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"OpenML dataset {openml_id} written to {csv_path}")
    return csv_path

def _download_csv_from_url(url: str, dest_path: Path) -> Path:
    """
    Download a raw CSV file from ``url`` and write it to ``dest_path``.
    """
    logger.info(f"Downloading CSV from URL: {url}")
    # pandas can read directly from HTTP URLs.
    df = pd.read_csv(url, header=None)
    # Preserve the original header‑less nature of the UCI files.
    df.to_csv(dest_path, index=False, header=False)
    logger.info(f"CSV downloaded to {dest_path}")
    return dest_path

def _load_schema() -> Dict:
    """
    Load the JSON‑Schema for dataset metadata.
    The schema lives under the project ``specs`` directory.
    """
    # The repository layout places contract schemas under
    # ``specs/<project‑id>/contracts``.
    schema_path = Path("specs") / "001-quantifying-the-impact-of-data-cleaning" / "contracts" / "dataset.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    import yaml  # PyYAML is available in the base environment.

    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return schema

def _validate_metadata(metadata: Dict, schema: Dict) -> None:
    """
    Validate a single metadata dictionary against the dataset schema.
    Raises ``jsonschema.ValidationError`` on failure.
    """
    jsonschema.validate(instance=metadata, schema=schema)

# ----------------------------------------------------------------------
# Core acquisition routine
# ----------------------------------------------------------------------
def ensure_data_exists() -> None:
    """
    Ensure that all datasets defined in ``DATASET_SPECS`` exist in the raw
    data directory. For each dataset:
    * Download (OpenML or direct URL) if missing.
    * Compute SHA‑256 checksum.
    * Build a metadata entry and validate it against the JSON‑Schema.
    * Append the entry to the consolidated ``dataset_metadata.json`` file.
    """
    config = get_config()
    raw_dir = Path(config.get("RAW_DATA_PATH", "data/raw"))
    processed_dir = Path(config.get("PROCESSED_DATA_PATH", "data/processed"))

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    schema = _load_schema()
    metadata_entries: List[Dict] = []

    for spec in DATASET_SPECS:
        name = spec["name"]
        outcome_col = spec["outcome_column"]
        csv_path: Path

        if spec["openml_id"] is not None:
            csv_path = raw_dir / f"{spec['openml_id']}.csv"
            if not csv_path.is_file():
                csv_path = _download_openml_dataset(spec["openml_id"], raw_dir)
        else:
            # Direct URL case – derive a safe filename from the dataset name.
            safe_name = name.lower().replace(" ", "_")
            csv_path = raw_dir / f"{safe_name}.csv"
            if not csv_path.is_file():
                csv_path = _download_csv_from_url(spec["url"], csv_path)

        # Load the CSV to compute metadata.
        df = pd.read_csv(csv_path)

        # Verify that the documented outcome column exists.
        if outcome_col not in df.columns:
            raise ValueError(
                f"Outcome column '{outcome_col}' not found in dataset '{name}' (file {csv_path})"
            )

        n_samples = int(len(df))
        missing_outcome = int(df[outcome_col].isna().sum())
        missingness_proportion = (
            missing_outcome / n_samples if n_samples > 0 else 0.0
        )
        checksum = compute_file_checksum(str(csv_path))

        metadata = {
            "name": name,
            "outcome_column": outcome_col,
            "n_samples": n_samples,
            "missingness_proportion": round(missingness_proportion, 6),
            "checksum": checksum,
        }

        # Validate against schema (will raise if invalid)
        _validate_metadata(metadata, schema)

        metadata_entries.append(metadata)
        logger.info(f"Metadata for dataset '{name}' validated and recorded.")

    # Write consolidated metadata JSON.
    metadata_path = processed_dir / "dataset_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata_entries, f, indent=2)
    logger.info(f"Consolidated dataset metadata written to {metadata_path}")

def main() -> None:
    """
    CLI entry point for manual data acquisition.
    """
    ensure_data_exists()

if __name__ == "__main__":
    main()