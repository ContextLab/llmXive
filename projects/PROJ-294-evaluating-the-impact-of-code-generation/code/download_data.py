import os
import sys
import json
import time
import logging
import hashlib
from typing import List, Dict, Any
from utils import setup_logging, get_logger, set_task_id, get_task_id, compute_sha256

# Global task context
_task_id = None

def set_task_id(task_id: str):
    global _task_id
    _task_id = task_id
    setup_logging(task_id=task_id)

def get_task_id():
    return _task_id

def setup_logging(task_id: str = None, level: int = logging.INFO) -> logging.Logger:
    global _task_id
    if task_id:
        _task_id = task_id
    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    logger = logging.getLogger(__name__)
    if not any(isinstance(f, logging.Filter) for f in logger.filters):
        class TaskFilter(logging.Filter):
            def filter(self, record):
                record.task_id = _task_id or "UNKNOWN"
                return True
        logger.addFilter(TaskFilter())
    return logger

def ensure_output_dir(path: str):
    """Ensure the directory for the given file path exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def compute_file_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file using the shared utility."""
    return compute_sha256(file_path)

def download_humaneval():
    """
    FR-001: Download the full HumanEval dataset from HuggingFace.
    Uses verified source: openai/openai_humaneval
    """
    logger = setup_logging(task_id="T001")
    logger.info("Downloading HumanEval dataset...")

    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("datasets library is required. Install with: pip install datasets") from e

    # Load dataset with retry logic
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            ds = load_dataset("openai/openai_humaneval", split="test")
            if len(ds) == 0:
                raise RuntimeError("Loaded dataset contains zero records")
            logger.info(f"Loaded {len(ds)} records from HumanEval")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to download dataset after {max_retries} attempts: {e}") from e
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Download attempt {attempt + 1} failed ({e}). Retrying in {delay}s...")
            time.sleep(delay)

    # Convert to DataFrame and save as Parquet
    import pandas as pd
    df = ds.to_pandas()

    parquet_path = os.path.join("data", "raw", "humaneval.parquet")
    ensure_output_dir(parquet_path)
    df.to_parquet(parquet_path, index=False)

    # Compute SHA256 checksum
    sha256 = compute_file_sha256(parquet_path)
    logger.info(f"Saved dataset to {parquet_path} (SHA256: {sha256})")

    # Record metadata
    metadata = {
        "source": "openai/openai_humaneval",
        "split": "test",
        "record_count": len(df),
        "sha256": sha256,
        "download_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        # Commit hash is not directly exposed; placeholder kept for schema compliance
        "commit_hash": "UNKNOWN"
    }

    metadata_path = os.path.join("data", "raw", "metadata.yaml")
    ensure_output_dir(metadata_path)
    with open(metadata_path, "w") as f:
        f.write("# Auto-generated metadata\n")
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")

    return parquet_path, metadata

def save_metadata(metadata: Dict[str, Any]):
    """Legacy wrapper – metadata is saved inside download_humaneval."""
    pass  # No-op; kept for backward compatibility

def perform_stratified_sampling(data: List[Dict[str, Any]], config: Dict[str, Any], output_path: str):
    """
    For this task we use the full dataset, so no sampling is performed.
    The function simply writes the full dataset to the requested JSONL path.
    """
    logger = setup_logging(task_id="T001")
    logger.info("Using full dataset (no stratified sampling required).")

    ensure_output_dir(output_path)

    with open(output_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    logger = setup_logging(task_id="T001")
    logger.info("Starting Data Acquisition (T001)")

    try:
        parquet_path, metadata = download_humaneval()

        # Load back as JSON for downstream tasks
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        data = df.to_dict(orient="records")

        jsonl_path = os.path.join("data", "raw", "humaneval_test.jsonl")
        perform_stratified_sampling(data, {}, jsonl_path)

        logger.info("Data acquisition completed successfully.")
    except Exception as e:
        logger.error(f"Data acquisition failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
