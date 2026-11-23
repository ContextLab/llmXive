"""
Dataset Ingestion Module for PROJ-230.

This script streams the raw code translation datasets from HuggingFace
and writes each row to a JSON Lines file under ``data/raw/``. It also
records a log (``ingestion_log.json``) containing the dataset identifier,
split name, and row count for each successfully fetched split.

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

from huggingface_hub import hf_hub_download, RepositoryNotFoundError, HfHubHTTPError

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

# Candidate filenames for the default split. Most HF code translation datasets expose a
# ``train.jsonl`` file; we fall back to other common extensions if needed.
CANDIDATE_FILENAMES = [
    "train.jsonl",
    "train.parquet",
    "train.csv",
    "train.txt",
]

def ensure_dirs() -> None:
    """Create the data/raw directory if it does not exist."""
    try:
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured raw data directory exists: {DATA_RAW_DIR}")
    except Exception as exc:
        logger.error(f"Failed to create raw data directory: {exc}")
        raise

def download_split(dataset_id: str, filename: str) -> Path:
    """
    Download a specific file from a HuggingFace dataset repository.

    Args:
        dataset_id: The repository identifier on the Hub (e.g., ``codeparrot/code-trans-py-js``).
        filename: The name of the file to download (e.g., ``train.jsonl``).

    Returns:
        Path to the downloaded file in the local cache.

    Raises:
        RuntimeError: If the file cannot be downloaded.
    """
    try:
        logger.info(f"Attempting to download {filename} from {dataset_id}")
        local_path = hf_hub_download(
            repo_id=dataset_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(PROJECT_ROOT / ".cache" / "huggingface"),
            force_download=False,
            resume_download=True,
        )
        logger.info(f"Successfully downloaded {filename} to {local_path}")
        return Path(local_path)
    except (RepositoryNotFoundError, HfHubHTTPError) as exc:
        logger.warning(f"File {filename} not found in {dataset_id}: {exc}")
        raise RuntimeError(f"Could not find {filename} in {dataset_id}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error while downloading {filename} from {dataset_id}: {exc}")
        raise RuntimeError(f"Failed to download {filename} from {dataset_id}") from exc

def stream_jsonl_to_output(source_path: Path, dest_path: Path) -> int:
    """
    Stream a JSONL file line‑by‑line into another JSONL file.

    Args:
        source_path: Path to the source JSONL file (downloaded from HF).
        dest_path: Path where the streamed output should be written.

    Returns:
        Number of rows written.
    """
    row_count = 0
    with source_path.open("r", encoding="utf-8") as src_f, dest_path.open(
        "w", encoding="utf-8"
    ) as dst_f:
        for line in src_f:
            line = line.strip()
            if not line:
                continue
            # Validate that the line is valid JSON; if not, skip.
            try:
                json_obj = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(f"Skipping malformed JSON line at {source_path}:{row_count + 1}")
                continue
            dst_f.write(json.dumps(json_obj, ensure_ascii=False) + "\n")
            row_count += 1
    logger.info(f"Wrote {row_count} rows to {dest_path}")
    return row_count

def process_dataset(dataset_id: str) -> Dict[str, object]:
    """
    Process a single dataset: download the default split and stream it to
    ``data/raw/<safe_name>_<split>.jsonl``.

    Returns a dictionary suitable for inclusion in the ingestion log.
    """
    safe_name = dataset_id.replace("/", "_").replace("-", "_")
    # The default split for these translation datasets is ``train``.
    split_name = "train"

    # Find a candidate file that exists in the repository.
    downloaded_path: Path | None = None
    for candidate in CANDIDATE_FILENAMES:
        try:
            downloaded_path = download_split(dataset_id, candidate)
            # If we successfully downloaded, break.
            break
        except RuntimeError:
            continue

    if downloaded_path is None:
        raise RuntimeError(
            f"Could not locate a default split file for {dataset_id}. Tried: {CANDIDATE_FILENAMES}"
        )

    # Destination path under data/raw
    dest_path = DATA_RAW_DIR / f"{safe_name}_{split_name}.jsonl"
    logger.info(f"Streaming {downloaded_path} to {dest_path}")

    row_count = stream_jsonl_to_output(downloaded_path, dest_path)

    return {
        "dataset_id": dataset_id,
        "split": split_name,
        "row_count": row_count,
    }

def main() -> None:
    """Entry point for the ingestion script."""
    logger.info("Starting dataset ingestion (streaming mode)...")
    ensure_dirs()

    ingestion_log: List[Dict[str, object]] = []

    for dataset_id in DATASET_IDS:
        try:
            metadata = process_dataset(dataset_id)
            ingestion_log.append(metadata)
            logger.info(
                f"Successfully processed {dataset_id} (rows: {metadata['row_count']})"
            )
        except Exception as exc:
            logger.error(f"Aborting ingestion due to error with {dataset_id}: {exc}")
            # Propagate the exception as required by the task spec.
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
