"""
src/data/download_test_split.py
---------------------------------
Downloads the CodeSearchNet Python **test** split from HuggingFace Hub,
writes the raw records to `data/raw_test_snippets.jsonl`, and records the
SHA‑256 checksum of the downloaded parquet file in `data/artifact_hashes.yaml`.

The script mirrors the retry‑and‑checksum logic of `src/data/download.py`
(three attempts with exponential back‑off).  It deliberately performs **no
further validation** of the records – the test split is only required for
metric‑calculation fixtures in the test suite.

Execution:
    python -m src.data.download_test_split

The script exits with status 0 on success and raises on any unrecoverable
error (download failure, I/O error, etc.).
"""
import json
import time
import hashlib
import os
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml
from huggingface_hub import hf_hub_download

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration (mirrors the values used in the plan/spec)
# ----------------------------------------------------------------------
REPO_ID = "kejian/codesearchnet-python-rebalanced"
FILE_NAME = "data/test-00000-of-00001-3967e86c21fe91c3.parquet"
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 60  # exponential back‑off base

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_hash_manifest() -> Dict[str, str]:
    """Load (or bootstrap) the artifact hash manifest."""
    manifest_path = paths.data("artifact_hashes.yaml")
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def _save_hash_manifest(manifest: Dict[str, str]) -> None:
    """Persist the artifact hash manifest."""
    manifest_path = paths.data("artifact_hashes.yaml")
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=True)

def _download_parquet() -> Path:
    """
    Download the parquet file with a retry loop.
    Returns the local Path to the downloaded file.
    Raises on final failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"Attempt {attempt}/{MAX_RETRIES}: downloading {FILE_NAME} from {REPO_ID}")
            local_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=FILE_NAME,
                repo_type="dataset",
            )
            log.info(f"Successfully downloaded to {local_path}")
            return Path(local_path)
        except Exception as exc:
            log.error(f"Download attempt {attempt} failed: {exc}")
            if attempt == MAX_RETRIES:
                raise
            sleep_seconds = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            log.info(f"Waiting {sleep_seconds}s before next retry...")
            time.sleep(sleep_seconds)

def _write_jsonl(records, out_path: Path) -> None:
    """Write an iterable of dicts to a JSON‑Lines file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Download the test split, record its checksum, and dump the raw records
    as JSON Lines.
    """
    # 1. Download parquet
    parquet_path = _download_parquet()

    # 2. Compute and record checksum
    checksum = _sha256(parquet_path)
    manifest = _load_hash_manifest()
    manifest[FILE_NAME] = checksum
    _save_hash_manifest(manifest)
    log.info(f"Recorded SHA‑256 checksum for {FILE_NAME}: {checksum}")

    # 3. Load parquet into a DataFrame
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as exc:
        log.error(f"Failed to read parquet file {parquet_path}: {exc}")
        raise

    # 4. Convert each row to a plain dict and write JSONL
    records = df.to_dict(orient="records")
    out_path = paths.data("raw_test_snippets.jsonl")
    _write_jsonl(records, out_path)
    log.info(f"Wrote {len(records)} raw test records to {out_path}")

if __name__ == "__main__":
    main()
