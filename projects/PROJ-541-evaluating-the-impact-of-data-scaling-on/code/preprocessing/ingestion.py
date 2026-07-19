"""Real-world dataset ingestion and processing pipeline.

Implements T056: Ingest Full Dataset Set.
Reads dataset configuration from `data/config/datasets.yaml`.
Streams data from Hugging Face datasets, samples if necessary,
and writes `results/real_world_ingestion_log.csv`.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml
from datasets import load_dataset

# Add project root to path if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.logger import setup_logger

logger = setup_logger("preprocessing.ingestion")

# Constants
CONFIG_PATH = Path("data/config/datasets.yaml")
OUTPUT_LOG_PATH = Path("results/real_world_ingestion_log.csv")
RAW_DATA_DIR = Path("data/raw")

# Sampling limit to prevent OOM on large datasets (T051 requirement)
MAX_ROWS = 50000


class RealWorldDataset:
    """Entity representing a real-world dataset with metadata."""

    def __init__(
        self,
        dataset_id: str,
        name: str,
        source: str,
        type: str,
        description: str,
        streaming_compatible: bool,
        config: str,
        splits: List[str],
        target_column: Optional[str],
        features: List[str],
        verification_status: str,
        last_verified: str,
        source_url: Optional[str] = None
    ):
        self.dataset_id = dataset_id
        self.name = name
        self.source = source
        self.type = type
        self.description = description
        self.streaming_compatible = streaming_compatible
        self.config = config
        self.splits = splits
        self.target_column = target_column
        self.features = features
        self.verification_status = verification_status
        self.last_verified = last_verified
        self.source_url = source_url or f"https://huggingface.co/datasets/{dataset_id}"
        self.row_count: Optional[int] = None
        self.checksum: Optional[str] = None
        self.status: str = "pending"
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_url": self.source_url,
            "status": self.status,
            "row_count": self.row_count,
            "checksum": self.checksum,
            "error_message": self.error_message
        }


def load_dataset_config(config_path: Path = CONFIG_PATH) -> List[Dict[str, Any]]:
    """Load dataset configuration from YAML."""
    if not config_path.exists():
        raise FileNotFoundError(f"Dataset config not found at {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return data.get("datasets", [])


def download_dataset(
    dataset_id: str,
    streaming: bool = True,
    max_rows: int = MAX_ROWS
) -> Tuple[pd.DataFrame, int]:
    """
    Download and stream a dataset from Hugging Face.

    Implements T024 (Streaming) and T051 (Sampling).
    Raises RuntimeError if download fails (T025).
    """
    try:
        logger.info(f"Attempting to stream dataset: {dataset_id}")

        # Use streaming mode to avoid loading full dataset into memory
        ds = load_dataset(dataset_id, split="train", streaming=streaming)

        # Convert to pandas, limiting rows if necessary
        if streaming:
            # Sample using itertools.islice logic via to_pandas with streaming
            # HuggingFace datasets streaming iterator
            rows = []
            count = 0
            for item in ds:
                rows.append(item)
                count += 1
                if count >= max_rows:
                    break

            df = pd.DataFrame(rows)
            actual_rows = count
        else:
            # Fallback for non-streaming if requested (should not happen with T024)
            df = ds.to_pandas()
            actual_rows = len(df)

        logger.info(f"Successfully loaded {actual_rows} rows from {dataset_id}")
        return df, actual_rows

    except Exception as e:
        # T025: Fail loudly, never fallback to synthetic
        raise RuntimeError(f"Failed to download dataset {dataset_id}: {str(e)}")


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataset: handle missing values, ensure types.

    Simple imputation for numeric columns, drop non-numeric for now.
    """
    # Drop rows with all NaN
    df = df.dropna(how='all')

    # Convert to numeric where possible, coerce errors to NaN
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to convert to numeric, keep as object if fails
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass

    # Drop columns that are entirely NaN after conversion
    df = df.dropna(axis=1, how='all')

    # Drop rows where target is NaN if target column exists
    # (Assume first column is target if not specified, or just clean generally)
    return df


def compute_checksum(df: pd.DataFrame) -> str:
    """Compute a deterministic checksum for the dataframe content."""
    # Convert to string representation (sorted columns for determinism)
    sorted_cols = sorted(df.columns)
    data_str = df[sorted_cols].to_csv(index=False)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()[:16]


def update_manifest(
    dataset: RealWorldDataset,
    df: pd.DataFrame
) -> None:
    """Update dataset metadata with row count and checksum."""
    dataset.row_count = len(df)
    dataset.checksum = compute_checksum(df)
    dataset.status = "success"


def process_real_world_dataset(
    dataset_config: Dict[str, Any]
) -> RealWorldDataset:
    """
    Process a single dataset: download, clean, compute stats.
    """
    # Instantiate entity
    ds = RealWorldDataset(
        dataset_id=dataset_config["id"],
        name=dataset_config["name"],
        source=dataset_config["source"],
        type=dataset_config["type"],
        description=dataset_config.get("description", ""),
        streaming_compatible=dataset_config.get("streaming_compatible", True),
        config=dataset_config.get("config", "default"),
        splits=dataset_config.get("splits", ["train"]),
        target_column=dataset_config.get("target_column"),
        features=dataset_config.get("features", []),
        verification_status=dataset_config.get("verification_status", "unknown"),
        last_verified=dataset_config.get("last_verified", "")
    )

    try:
        # Download and stream
        df, row_count = download_dataset(ds.dataset_id)

        # Clean
        df_clean = clean_dataset(df)

        # Update metadata
        update_manifest(ds, df_clean)

        # Save raw data for verification (optional but good practice)
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = ds.dataset_id.replace("/", "_").replace(":", "_")
        output_file = RAW_DATA_DIR / f"{safe_name}.parquet"
        df_clean.to_parquet(output_file, index=False)

        logger.info(f"Processed {ds.dataset_id}: {ds.row_count} rows, checksum: {ds.checksum}")
        return ds

    except Exception as e:
        ds.status = "failed"
        ds.error_message = str(e)
        logger.error(f"Failed to process {ds.dataset_id}: {str(e)}")
        return ds


def run_ingestion_pipeline(
    config_path: Path = CONFIG_PATH,
    output_path: Path = OUTPUT_LOG_PATH
) -> List[RealWorldDataset]:
    """
    Main pipeline: load config, process all datasets, write log.
    Implements T056 deliverable: results/real_world_ingestion_log.csv
    """
    logger.info("Starting real-world dataset ingestion pipeline")

    # Load config
    configs = load_dataset_config(config_path)
    logger.info(f"Found {len(configs)} datasets to process")

    results: List[RealWorldDataset] = []

    for cfg in configs:
        ds = process_real_world_dataset(cfg)
        results.append(ds)

    # Write log
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "dataset_id", "source_url", "status", "row_count", "checksum"
        ])
        writer.writeheader()
        for ds in results:
            writer.writerow({
                "dataset_id": ds.dataset_id,
                "source_url": ds.source_url,
                "status": ds.status,
                "row_count": ds.row_count,
                "checksum": ds.checksum
            })

    logger.info(f"Ingestion log written to {output_path}")
    return results


def validate_dataset_availability(
    config_path: Path = CONFIG_PATH
) -> Tuple[List[str], List[str]]:
    """
    T027a: Validate which datasets are accessible.
    Returns (available_ids, failed_ids).
    Does NOT raise if < 10 available; logs warning instead.
    """
    configs = load_dataset_config(config_path)
    available = []
    failed = []

    for cfg in configs:
        ds_id = cfg["id"]
        try:
            # Quick metadata check by attempting a small stream
            ds = load_dataset(ds_id, split="train", streaming=True)
            # Try to get one item to verify access
            next(iter(ds))
            available.append(ds_id)
        except Exception as e:
            failed.append(ds_id)
            logger.warning(f"Dataset {ds_id} not accessible: {str(e)}")

    if len(available) < 10:
        logger.warning(
            f"Only {len(available)} datasets available (threshold: 10). "
            f"Proceeding with available set."
        )

    return available, failed


if __name__ == "__main__":
    # Run pipeline if executed directly
    run_ingestion_pipeline()
