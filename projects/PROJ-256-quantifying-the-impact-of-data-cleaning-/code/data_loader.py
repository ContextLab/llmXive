"""
Data acquisition utilities.
Downloads a verified dataset (Iris via OpenML) if the raw data directory is empty,
writes it to CSV, and records basic metadata.
"""
import json
import logging
import os
from pathlib import Path
from typing import List

import openml
import pandas as pd

from config import get_config
from utils import setup_logging

logger = setup_logging(log_level="INFO")


def _download_iris_dataset(raw_dir: Path) -> Path:
    """
    Download the Iris dataset (OpenML ID 61) and store it as ``iris.csv`` in ``raw_dir``.
    Returns the path to the written CSV file.
    """
    logger.info("Downloading Iris dataset from OpenML (ID 61)")
    dataset = openml.datasets.get_dataset(61)
    X, y, _, _ = dataset.get_data(dataset_format="dataframe")
    df = X.copy()
    df["outcome"] = y

    csv_path = raw_dir / "iris.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Iris dataset written to {csv_path}")
    return csv_path


def write_dataset_metadata(df: pd.DataFrame, raw_path: Path) -> None:
    """
    Write ``dataset_metadata.json`` to the processed data directory.
    The metadata includes:
        - outcome column name
        - number of records (sample size)
        - proportion of missing values in the outcome column
    """
    processed_dir = Path(
        get_config().get("PROCESSED_DATA_PATH", "data/processed")
    )
    processed_dir.mkdir(parents=True, exist_ok=True)

    outcome_col = "outcome"
    n_rows = len(df)
    missing_outcome = df[outcome_col].isna().sum()
    missing_proportion = missing_outcome / n_rows if n_rows > 0 else 0.0

    metadata = {
        "outcome_column": outcome_col,
        "sample_size": n_rows,
        "outcome_missing_proportion": missing_proportion,
    }

    metadata_path = processed_dir / "dataset_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Dataset metadata written to {metadata_path}")


def ensure_data_exists() -> None:
    """
    Ensure that at least one CSV file exists in the raw data directory.
    If the directory is empty, download the Iris dataset via OpenML,
    write it to CSV, and generate accompanying metadata.
    """
    config = get_config()
    raw_dir = Path(config.get("RAW_DATA_PATH", "data/raw"))
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_files = list(raw_dir.glob("*.csv"))
    if csv_files:
        logger.info(
            f"Raw data already present ({len(csv_files)} CSV file(s) in {raw_dir})"
        )
        return  # Nothing to do

    # No raw CSVs – download the default dataset.
    csv_path = _download_iris_dataset(raw_dir)

    # Load the just‑downloaded CSV to compute metadata.
    df = pd.read_csv(csv_path)
    write_dataset_metadata(df, csv_path)


def main() -> None:
    """
    CLI entry point for manual data acquisition.
    """
    ensure_data_exists()


if __name__ == "__main__":
    main()
