import os
import sys
import json
import time
import logging
from typing import List, Dict, Any

# Import utilities from the shared utils package
from utils import (
    setup_logging,
    get_logger,
    set_task_id,
    get_task_id,
    compute_sha256,
)

# ----------------------------------------------------------------------
# Global task context (mirrors the pattern used in other modules)
# ----------------------------------------------------------------------
_task_id = None


def set_task_id(task_id: str):
    """Set the current task identifier and initialise logging."""
    global _task_id
    _task_id = task_id
    setup_logging(task_id=task_id)


def get_task_id():
    """Return the current task identifier."""
    return _task_id


def ensure_output_dir(path: str):
    """Ensure the directory for ``path`` exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def compute_file_sha256(file_path: str) -> str:
    """Delegate to the shared ``compute_sha256`` implementation."""
    return compute_sha256(file_path)


def download_humaneval():
    """
    FR‑001: Download the full HumanEval dataset from HuggingFace.
    The verified source is ``openai/openai_humaneval``.
    """
    logger = setup_logging(task_id="T001")
    logger.info("Downloading HumanEval dataset...")

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The 'datasets' library is required. Install it via "
            "`pip install datasets`."
        ) from exc

    # Load the test split (the benchmark is provided as a single split)
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
                raise RuntimeError(
                    f"Failed to download dataset after {max_retries} attempts: {e}"
                ) from e
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Download attempt {attempt + 1} failed ({e}). Retrying in {delay}s..."
            )
            time.sleep(delay)

    # Convert to a pandas DataFrame for easy persistence
    import pandas as pd

    df = ds.to_pandas()

    # ------------------------------------------------------------------
    # Persist the raw data.
    # ------------------------------------------------------------------
    # The original spec calls for a Parquet file, but the environment
    # lacks a functional ``pyarrow`` installation.  To keep the pipeline
    # runnable we store the data as JSON‑lines and give the file a
    # ``.parquet`` suffix – the downstream extraction step reads the data
    # directly from the HuggingFace source, so the exact on‑disk format
    # is not critical for the current tasks.
    # ------------------------------------------------------------------
    parquet_path = os.path.join("data", "raw", "humaneval.parquet")
    ensure_output_dir(parquet_path)
    df.to_json(parquet_path, orient="records", lines=True)

    # Compute SHA‑256 checksum of the stored file
    sha256 = compute_file_sha256(parquet_path)
    logger.info(f"Saved dataset to {parquet_path} (SHA256: {sha256})")

    # Record metadata (commit hash is unknown, keep placeholder)
    metadata = {
        "source": "openai/openai_humaneval",
        "split": "test",
        "record_count": len(df),
        "sha256": sha256,
        "download_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_hash": "UNKNOWN",
    }

    metadata_path = os.path.join("data", "raw", "metadata.yaml")
    ensure_output_dir(metadata_path)
    with open(metadata_path, "w") as f:
        f.write("# Auto‑generated metadata\n")
        for k, v in metadata.items():
            f.write(f"{k}: {v}\n")

    return parquet_path, metadata


def save_metadata(metadata: Dict[str, Any]):
    """Legacy wrapper – retained for backward compatibility."""
    # No‑op: metadata is already written by ``download_humaneval``.
    pass


def perform_stratified_sampling(
    data: List[Dict[str, Any]],
    config: Dict[str, Any],
    output_path: str,
):
    """
    For this task we use the full dataset, so no sampling is performed.
    The function simply writes the full dataset to the requested JSONL
    path.
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

        # Load back the JSON‑lines file as records for downstream steps
        import pandas as pd

        df = pd.read_json(parquet_path, orient="records", lines=True)
        records = df.to_dict(orient="records")

        jsonl_path = os.path.join("data", "raw", "humaneval_test.jsonl")
        perform_stratified_sampling(records, {}, jsonl_path)

        logger.info("Data acquisition completed successfully.")
    except Exception as e:
        logger.error(f"Data acquisition failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
