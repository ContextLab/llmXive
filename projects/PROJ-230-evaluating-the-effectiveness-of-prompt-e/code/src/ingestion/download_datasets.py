"""
Dataset Ingestion Module for PROJ-230.

This module streams the raw code translation datasets from HuggingFace and
writes each row to a JSON Lines file under ``data/raw/``. It also records a
log (``ingestion_log.json``) containing the dataset identifier, split name,
and row count for each successfully fetched split.

Datasets:
- codeparrot/code-trans-py-js
- bigcode/evaluation

Outputs (per dataset/split):
- data/raw/<safe_dataset_name>_<split>.jsonl   (one JSON object per line)
- data/raw/ingestion_log.json                  (metadata about ingestion)
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

from datasets import load_dataset, DatasetDict, IterableDataset

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Resolve project root (four levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOG_PATH = DATA_RAW_DIR / "ingestion_log.json"

# Datasets to ingest
DATASET_IDS = [
    "codeparrot/code-trans-py-js",
    "bigcode/evaluation",
]

def ensure_dirs() -> None:
    """Create the data/raw directory if it does not exist."""
    try:
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured raw data directory exists: {DATA_RAW_DIR}")
    except Exception as exc:
        logger.error(f"Failed to create raw data directory: {exc}")
        raise

def select_default_split(dataset_id: str) -> str:
    """
    Load the dataset metadata (without streaming) and return the first
    available split name. This is a lightweight operation because the
    library only downloads the dataset card and split information.
    """
    try:
        meta = load_dataset(dataset_id, streaming=False)
        # ``meta`` can be a DatasetDict or a single Dataset
        if isinstance(meta, DatasetDict):
            split_name = list(meta.keys())[0]
        else:
            # Single split dataset – treat as ``train`` for naming purposes
            split_name = "train"
        logger.info(f"Selected default split '{split_name}' for {dataset_id}")
        return split_name
    except Exception as exc:
        logger.error(f"Unable to determine default split for {dataset_id}: {exc}")
        raise

def stream_and_write(dataset_id: str, split: str) -> int:
    """
    Stream the specified split of a dataset and write each row as a JSON
    line to ``data/raw/<safe_name>_<split>.jsonl``.

    Returns the number of rows written.
    """
    safe_name = dataset_id.replace("/", "_").replace("-", "_")
    out_path = DATA_RAW_DIR / f"{safe_name}_{split}.jsonl"

    logger.info(f"Streaming dataset '{dataset_id}' split '{split}' to {out_path}")

    # Open the output file in text mode with UTF‑8 encoding
    with out_path.open("w", encoding="utf-8") as out_f:
        # Load dataset in streaming mode
        try:
            ds_iter: IterableDataset = load_dataset(
                dataset_id,
                split=split,
                streaming=True,
                trust_remote_code=True,
            )
        except Exception as exc:
            logger.error(f"Failed to stream dataset {dataset_id} split {split}: {exc}")
            raise

        row_count = 0
        for row in ds_iter:
            # Each ``row`` is a dict; write it as a JSON line
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            row_count += 1

            # Periodic progress logging (every 10k rows)
            if row_count % 10_000 == 0:
                logger.info(f"  {row_count} rows written for {dataset_id}/{split}")

    logger.info(f"Completed streaming {dataset_id}/{split}: {row_count} rows")
    return row_count

def main() -> None:
    """Entry point for the ingestion script."""
    logger.info("Starting dataset ingestion (streaming mode)...")
    ensure_dirs()

    ingestion_log: List[Dict[str, object]] = []

    for dataset_id in DATASET_IDS:
        try:
            # Determine which split to use
            split = select_default_split(dataset_id)

            # Stream the dataset and write rows
            row_count = stream_and_write(dataset_id, split)

            # Record metadata for this dataset/split
            ingestion_log.append(
                {
                    "dataset_id": dataset_id,
                    "split": split,
                    "row_count": row_count,
                }
            )
        except Exception as exc:
            # Any failure must be propagated – the task specification requires
            # the script to raise on fetch failure.
            logger.error(f"Aborting ingestion due to error with {dataset_id}: {exc}")
            raise

    # Write the ingestion log as JSON
    try:
        with LOG_PATH.open("w", encoding="utf-8") as log_f:
            json.dump(ingestion_log, log_f, indent=2, ensure_ascii=False)
        logger.info(f"Ingestion log written to {LOG_PATH}")
    except Exception as exc:
        logger.error(f"Failed to write ingestion log: {exc}")
        raise

    logger.info("Dataset ingestion completed successfully.")

if __name__ == "__main__":
    main()
