"""
Ingestion script for Task T002 – Cyberball dataset (ds000208).

This script downloads a verified OpenNeuro parquet file, verifies that the
download does not exceed the RAM limit (7 GB), computes a SHA‑256 checksum,
writes a metadata JSON file, creates a human‑readable citation, and adds a
``task`` column with the value ``"cyberball"`` to every record.

The script is deliberately simple because only a single dataset is
required for the current pipeline.  It accepts the following CLI:

  --dataset-url   URL of the parquet file to download (required)
  --output-dir    Directory where the raw files should be stored
                  (defaults to the project ``data/raw`` folder)
  --dataset-id    Identifier used for naming output files
                  (defaults to ``ds000208``)

All artefacts are written under the project root using the ``paths``
helpers from ``llmxive_toolkit`` (via ``config.get_path`` for consistency).

Exit code ``0`` indicates success; any problem results in a logged error
and ``sys.exit(1)``.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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

                    # Periodic size guard – abort if we somehow exceed the limit
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

    if "task" not in df.columns:
        df["task"] = task_value
    else:
        df["task"] = task_value  # overwrite if somehow present

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
    parser.add_argument(
        "--dataset-url",
        required=True,
        help="Direct URL to the parquet file to download.",
    )
    parser.add_argument(
        "--output-dir",
        default=get_path("raw"),
        help="Directory where raw data should be stored (default: project raw folder).",
    )
    parser.add_argument(
        "--dataset-id",
        default="ds000208",
        help="Identifier used for naming output files (default: ds000208).",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    args = parse_cli()

    output_dir = Path(args.output_dir)
    dataset_id = args.dataset_id
    url = args.dataset_url

    # Destination parquet file
    parquet_path = output_dir / f"{dataset_id}.parquet"

    # ------------------------------------------------------------------
    # 1. Download the parquet file (with size guard)
    # ------------------------------------------------------------------
    bytes_written = download_file(url, parquet_path, MAX_RAM_GB)

    # ------------------------------------------------------------------
    # 2. Compute SHA‑256 checksum
    # ------------------------------------------------------------------
    checksum = compute_sha256(parquet_path)

    # ------------------------------------------------------------------
    # 3. Write metadata JSON
    # ------------------------------------------------------------------
    metadata = {
        "dataset_id": dataset_id,
        "download_url": url,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "size_bytes": bytes_written,
        "sha256": checksum,
    }
    metadata_path = output_dir / f"metadata_{dataset_id}.json"
    write_metadata(metadata_path, metadata)

    # ------------------------------------------------------------------
    # 4. Write citation file
    # ------------------------------------------------------------------
    citation_path = output_dir / "CITATION.md"
    write_citation(citation_path)

    # ------------------------------------------------------------------
    # 5. Add ``task`` column to the parquet file
    # ------------------------------------------------------------------
    add_task_column(parquet_path, task_value="cyberball")

    logger.info("Ingestion completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()