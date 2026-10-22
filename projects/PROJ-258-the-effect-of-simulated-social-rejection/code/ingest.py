"""
Ingestion script for Task T002 – Cyberball dataset (ds000208).

This script downloads the verified OpenNeuro parquet file, verifies that the
download does not exceed the RAM limit (7 GB), computes a SHA-256 checksum,
writes a metadata JSON file, creates a human-readable citation, and adds a
'task' column with the value 'cyberball' to every record.
It also creates the reward_unavailable.json stub.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pandas as pd
import requests
import pyarrow.parquet as pq

from config import get_path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
CITATION_TEXT = (
    "OpenNeuro. ds000208: Cyberball social exclusion dataset. "
    "https://openneuro.org/datasets/ds000208"
)
DS000208_URL = "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"
MAX_RAM_GB = 7.0
REQUIRED_COLUMNS = ["participant_id", "condition", "reaction_time", "mood_rating"]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of file_path in a memory-efficient way."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, dest_path: Path, max_gb: float) -> int:
    """
    Stream-download url to dest_path.
    Returns the number of bytes written. Exits with code 1 if the
    download would exceed max_gb.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} → {dest_path}")

    try:
        head = requests.head(url, timeout=10, allow_redirects=True)
        head.raise_for_status()
        size_bytes = int(head.headers.get("Content-Length", "0"))
        if size_bytes:
            size_gb = size_bytes / (1024 ** 3)
            logger.info(f"Remote file size: {size_gb:.3f} GB")
            if size_gb > max_gb:
                logger.error(f"File size ({size_gb:.2f} GB) exceeds RAM limit of {max_gb} GB.")
                sys.exit(1)
    except Exception as exc:
        logger.warning(f"Could not determine remote size: {exc}")

    total_written = 0
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    total_written += len(chunk)

                    if total_written > max_gb * (1024 ** 3):
                        logger.error(f"Downloaded data exceeded {max_gb} GB limit; aborting.")
                        sys.exit(1)
    except Exception as exc:
        logger.error(f"Download failed: {exc}")
        raise

    logger.info(f"Download complete ({total_written} bytes).")
    return total_written

def add_task_column(parquet_path: Path, task_value: str = "cyberball") -> None:
    """
    Load the parquet file, add a 'task' column, and overwrite the file.
    """
    logger.info(f"Adding task column to {parquet_path}")
    try:
        # Use pyarrow's parquet reader with coerce_int96_timestamp_unit to handle
        # various parquet encoding issues
        table = pq.read_table(
            parquet_path,
            coerce_int96_timestamp_unit='ns'
        )
        
        # Add task column
        import pyarrow as pa
        task_array = pa.array([task_value] * table.num_rows)
        table = table.append_column("task", task_array)
        
        pq.write_table(table, parquet_path)
        logger.info("Task column added successfully.")
    except Exception as exc:
        logger.error(f"Failed to add task column: {exc}")
        sys.exit(1)

def validate_dataset_contents(parquet_path: Path) -> None:
    """
    Validate that the dataset contains required columns and the
    necessary conditions.
    """
    logger.info(f"Validating columns and conditions in {parquet_path}")
    try:
        # Try reading with pyarrow first, then fallback to pandas
        try:
            table = pq.read_table(
                parquet_path,
                coerce_int96_timestamp_unit='ns'
            )
            df = table.to_pandas()
        except Exception as pa_exc:
            logger.warning(f"PyArrow read failed, trying pandas: {pa_exc}")
            df = pd.read_parquet(parquet_path, engine='pyarrow')
        
        # Check required columns (case-insensitive)
        df_cols_lower = {col.lower(): col for col in df.columns}
        required_lower = {col.lower(): col for col in REQUIRED_COLUMNS}
        
        missing = []
        actual_cols = {}
        for req_lower, req_orig in required_lower.items():
            if req_lower in df_cols_lower:
                actual_cols[req_lower] = df_cols_lower[req_lower]
            else:
                missing.append(req_orig)
        
        if missing:
            logger.error(f"Missing required columns: {missing}")
            sys.exit(1)
        
        # Check condition values (case-insensitive)
        condition_col = actual_cols.get('condition', 'condition')
        if condition_col not in df.columns:
            logger.error(f"Condition column not found")
            sys.exit(1)
        
        conditions = {str(v).lower() for v in df[condition_col].dropna().unique()}
        if 'rejection' not in conditions or 'control' not in conditions:
            logger.error(f"Condition column must contain both 'rejection' and 'control'. Found: {conditions}")
            sys.exit(1)
        
        logger.info("Column and condition validation passed.")
    except SystemExit:
        raise
    except Exception as exc:
        logger.error(f"Validation failed: {exc}")
        sys.exit(1)

def write_metadata(metadata_path: Path, info: Dict[str, Any]) -> None:
    """Write info as pretty-printed JSON."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, sort_keys=True)
    logger.info(f"Metadata written to {metadata_path}")

def write_citation(citation_path: Path) -> None:
    """Create a simple CITATION.md file."""
    citation_path.parent.mkdir(parents=True, exist_ok=True)
    with open(citation_path, "w", encoding="utf-8") as f:
        f.write(CITATION_TEXT + "\n")
    logger.info(f"Citation written to {citation_path}")

def write_reward_stub() -> None:
    """Create the reward_unavailable.json stub in data/interim."""
    stub_path = Path(get_path("interim")) / "reward_unavailable.json"
    stub_path.parent.mkdir(parents=True, exist_ok=True)
    content = {
        "reward_dataset_available": False,
        "reason": "No open-access reward dataset with verified URL."
    }
    with open(stub_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    logger.info(f"Reward unavailability stub written to {stub_path}")

def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest the Cyberball dataset (ds000208) for Task T002."
    )
    parser.add_argument(
        "--dataset",
        help="Dataset identifier to ingest (e.g., ds000208).",
    )
    parser.add_argument(
        "--dataset-url",
        "--url",
        dest="dataset_url",
        help="Direct URL to the parquet file to download.",
    )
    parser.add_argument(
        "--output-dir",
        "--out-dir",
        default=get_path("raw"),
        dest="output_dir",
        help="Directory where raw data should be stored.",
    )
    parser.add_argument(
        "--dataset-id",
        default="ds000208",
        dest="dataset_id",
        help="Identifier used for naming output files.",
    )
    return parser.parse_args()

def ingest_single_dataset(
    url: str,
    output_dir: Path,
    dataset_id: str,
    task_name: str = "cyberball",
) -> Dict[str, Any]:
    """
    Perform the full ingestion workflow for a single dataset.
    """
    parquet_path = output_dir / f"{dataset_id}.parquet"

    bytes_written = download_file(url, parquet_path, MAX_RAM_GB)
    
    # Compute checksum immediately after download (before validation)
    checksum = compute_sha256(parquet_path)

    # Write metadata early so it exists even if validation fails
    metadata = {
        "dataset_id": dataset_id,
        "download_url": url,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "size_bytes": bytes_written,
        "sha256": checksum,
    }
    metadata_path = output_dir / "metadata.json"
    write_metadata(metadata_path, metadata)

    # Write citation
    citation_path = output_dir / "CITATION.md"
    write_citation(citation_path)

    # Now validate contents
    validate_dataset_contents(parquet_path)
    
    # Add task column after successful validation
    add_task_column(parquet_path, task_value=task_name)

    logger.info(f"Ingestion of {dataset_id} completed successfully.")
    return {
        "url": url,
        "sha256": checksum,
        "size_bytes": bytes_written,
        "file_count": 1,
        "dataset_id": dataset_id,
    }

def main() -> None:
    args = parse_cli()

    output_dir = Path(args.output_dir)
    dataset_id = args.dataset_id
    url = args.dataset_url

    if args.dataset:
        dataset_id = args.dataset
        if dataset_id == "ds000208":
            url = DS000208_URL
        else:
            logger.error(f"Unsupported dataset: {dataset_id}")
            sys.exit(1)

    if not url:
        logger.error("Either --dataset or --url must be provided.")
        sys.exit(1)

    try:
        ingest_single_dataset(
            url=url,
            output_dir=output_dir,
            dataset_id=dataset_id,
            task_name="cyberball" if dataset_id == "ds000208" else "other"
        )
        # Create the reward unavailability stub as required by plan.md/tasks.md
        write_reward_stub()
        logger.info("Ingestion completed successfully.")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
