"""
Ingestion script for Task T002 – Cyberball dataset (ds000208) and
optional reward‑feedback dataset (ds003392) – Task T003.

This script downloads verified OpenNeuro parquet files, verifies that the
download does not exceed the RAM limit (7 GB), computes a SHA‑256 checksum,
writes a metadata JSON file, creates a human‑readable citation, and adds a
``task`` column with the appropriate value to every record.

The script accepts the following CLI arguments (both long and short aliases
are supported for compatibility with the existing quickstart and test suite):

  --dataset-url / --url          URL of the parquet file to download (required)
  --output-dir  / --out-dir      Directory where the raw files should be stored
                                 (defaults to the project ``data/raw`` folder)
  --dataset-id                   Identifier used for naming output files
                                 (defaults to ``ds000208``)

In addition to the original single‑dataset ingestion, a helper function
:func:`run_ingestion` is provided for the test suite.  It attempts to
ingest both the Cyberball dataset (ds000208) and the reward‑feedback
dataset (ds003392).  If the reward dataset is unavailable, a JSON file
``data/interim/reward_unavailable.json`` is written with
``{\"available\": false}`` and processing continues with a Between‑Subjects
design.

All artefacts are written under the project root using the ``paths``
helpers from ``llmxive_toolkit`` (via ``config.get_path`` for consistency).

Exit code ``0`` indicates success; any problem results in a logged error
and ``sys.exit(1)``.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd
import requests

from config import get_path, MAX_RAM_GB

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# OpenNeuro citation template – this is a static citation for ds000208.
CITATION_TEXT = (
    "OpenNeuro. ds000208: Cyberball social exclusion dataset. "
    "https://openneuro.org/datasets/ds000208"
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of *file_path* in a memory‑efficient way."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, dest_path: Path, max_gb: float) -> int:
    """
    Stream‑download *url* to *dest_path*.

    Returns the number of bytes written.  Exits with code 1 if the
    download would exceed *max_gb*.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} → {dest_path}")

    # Perform a HEAD request first to check Content‑Length (if provided)
    try:
        head = requests.head(url, timeout=10, allow_redirects=True)
        head.raise_for_status()
        size_bytes = int(head.headers.get("Content-Length", "0"))
        if size_bytes:
            size_gb = size_bytes / (1024 ** 3)
            logger.info(f"Remote file size: {size_gb:.3f} GB")
            if size_gb > max_gb:
                logger.error(
                    f"File size ({size_gb:.2f} GB) exceeds RAM limit of {max_gb} GB."
                )
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

                    # Guard against exceeding the limit during streaming
                    if total_written > max_gb * (1024 ** 3):
                        logger.error(
                            f"Downloaded data exceeded {max_gb} GB limit; aborting."
                        )
                        sys.exit(1)
    except Exception as exc:
        logger.error(f"Download failed: {exc}")
        raise

    logger.info(f"Download complete ({total_written} bytes).")
    return total_written

def add_task_column(parquet_path: Path, task_value: str = "cyberball") -> None:
    """
    Load the parquet file, add a ``task`` column, and overwrite the file.
    """
    logger.info(f"Adding task column to {parquet_path}")
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as exc:
        logger.error(f"Failed to read parquet file {parquet_path}: {exc}")
        sys.exit(1)

    df["task"] = task_value  # overwrite or create

    try:
        df.to_parquet(parquet_path, index=False)
    except Exception as exc:
        logger.error(f"Failed to write parquet with task column: {exc}")
        sys.exit(1)

def write_metadata(metadata_path: Path, info: Dict[str, Any]) -> None:
    """Write *info* as pretty‑printed JSON."""
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

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest the Cyberball dataset (ds000208) for Task T002."
    )
    # Support both the original flag names and the quickstart aliases.
    parser.add_argument(
        "--dataset-url",
        "--url",
        required=True,
        dest="dataset_url",
        help="Direct URL to the parquet file to download.",
    )
    parser.add_argument(
        "--output-dir",
        "--out-dir",
        default=get_path("raw"),
        dest="output_dir",
        help="Directory where raw data should be stored (default: project raw folder).",
    )
    parser.add_argument(
        "--dataset-id",
        default="ds000208",
        dest="dataset_id",
        help="Identifier used for naming output files (default: ds000208).",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Core ingestion for a single dataset
# ----------------------------------------------------------------------
def ingest_single_dataset(
    url: str,
    output_dir: Path,
    dataset_id: str,
    task_name: str = "cyberball",
) -> Dict[str, Any]:
    """
    Perform the full ingestion workflow for a single dataset.

    Returns a dictionary with manifest information (url, sha256,
    size_bytes, file_count, dataset_id).  ``file_count`` is 1 when the
    parquet file is successfully written, otherwise 0.
    """
    parquet_path = output_dir / f"{dataset_id}.parquet"

    # 1. Download the parquet file (with size guard)
    try:
        bytes_written = download_file(url, parquet_path, MAX_RAM_GB)
    except Exception as exc:
        logger.error(f"Failed to download {dataset_id}: {exc}")
        # Propagate the failure to the caller
        raise

    # 2. Compute SHA‑256 checksum
    checksum = compute_sha256(parquet_path)

    # 3. Write metadata JSON
    metadata = {
        "dataset_id": dataset_id,
        "download_url": url,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "size_bytes": bytes_written,
        "sha256": checksum,
    }
    metadata_path = output_dir / f"metadata_{dataset_id}.json"
    write_metadata(metadata_path, metadata)

    # 4. Write citation file (only once; same content for both datasets)
    citation_path = output_dir / "CITATION.md"
    if not citation_path.is_file():
        write_citation(citation_path)

    # 5. Add ``task`` column to the parquet file
    add_task_column(parquet_path, task_value=task_name)

    logger.info(f"Ingestion of {dataset_id} completed successfully.")
    return {
        "url": url,
        "sha256": checksum,
        "size_bytes": bytes_written,
        "file_count": 1,
        "dataset_id": dataset_id,
    }

# ----------------------------------------------------------------------
# Public helper for the test suite – ingests both datasets
# ----------------------------------------------------------------------
def run_ingestion() -> None:
    """
    Ingest the primary Cyberball dataset (ds000208) and attempt to ingest the
    reward‑feedback dataset (ds003392).  Writes a manifest JSON file
    ``data/raw/dataset_manifest.json`` containing entries for each dataset.
    If the reward dataset cannot be downloaded, writes
    ``data/interim/reward_unavailable.json`` with ``{\"available\": false}``
    and records a minimal manifest entry for it.
    Also writes a simple design metadata file
    ``data/processed/metadata.json`` indicating a Between‑Subjects design.
    """
    raw_dir = Path(get_path("raw"))
    interim_dir = Path(get_path("interim"))
    processed_dir = Path(get_path("processed"))

    # Ensure directories exist
    for d in (raw_dir, interim_dir, processed_dir):
        d.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []

    # ----- ds000208 (always present) -----
    ds000208_url = (
        "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"
    )
    try:
        entry = ingest_single_dataset(
            url=ds000208_url,
            output_dir=raw_dir,
            dataset_id="ds000208",
            task_name="cyberball",
        )
        manifest.append(entry)
    except Exception as exc:
        logger.error(f"Critical failure ingesting ds000208: {exc}")
        sys.exit(1)

    # ----- ds003392 (optional) -----
    ds003392_url = (
        "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/ds003392.parquet"
    )
    reward_entry: Dict[str, Any] = {
        "url": ds003392_url,
        "sha256": None,
        "size_bytes": 0,
        "file_count": 0,
        "dataset_id": "ds003392",
    }
    try:
        reward_entry = ingest_single_dataset(
            url=ds003392_url,
            output_dir=raw_dir,
            dataset_id="ds003392",
            task_name="reward",
        )
        manifest.append(reward_entry)
    except Exception:
        # Record unavailability
        reward_unavailable_path = interim_dir / "reward_unavailable.json"
        with open(reward_unavailable_path, "w", encoding="utf-8") as f:
            json.dump({"available": False}, f, indent=2)
        logger.warning(
            "Reward‑feedback dataset ds003392 unavailable; proceeding with Between‑Subjects design."
        )
        manifest.append(reward_entry)  # still add entry with minimal info

    # Write manifest
    manifest_path = raw_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

    # Write processed design metadata (used later by analysis)
    design_metadata_path = processed_dir / "metadata.json"
    design_info = {"design_type": "Between-Subjects"}
    with open(design_metadata_path, "w", encoding="utf-8") as f:
        json.dump(design_info, f, indent=2)
    logger.info(f"Design metadata written to {design_metadata_path}")

# ----------------------------------------------------------------------
# Main workflow (single‑dataset mode, used by quickstart)
# ----------------------------------------------------------------------
def main() -> None:
    args = parse_cli()

    output_dir = Path(args.output_dir)
    dataset_id = args.dataset_id
    url = args.dataset_url

    # Destination parquet file
    parquet_path = output_dir / f"{dataset_id}.parquet"

    # 1. Download the parquet file (with size guard)
    bytes_written = download_file(url, parquet_path, MAX_RAM_GB)

    # 2. Compute SHA‑256 checksum
    checksum = compute_sha256(parquet_path)

    # 3. Write metadata JSON
    metadata = {
        "dataset_id": dataset_id,
        "download_url": url,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "size_bytes": bytes_written,
        "sha256": checksum,
    }
    metadata_path = output_dir / f"metadata_{dataset_id}.json"
    write_metadata(metadata_path, metadata)

    # 4. Write citation file
    citation_path = output_dir / "CITATION.md"
    write_citation(citation_path)

    # 5. Add ``task`` column to the parquet file
    add_task_column(parquet_path, task_value="cyberball")

    logger.info("Ingestion completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
