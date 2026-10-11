"""
Ingestion script for the Social Rejection project (Task T003).

This script downloads one or more dataset files given via ``--dataset-url``,
streams them to the specified ``--output-dir`` (defaulting to the project's
raw data folder), and writes a ``dataset_manifest.json`` that records basic
metadata for each downloaded file.

The original implementation attempted to use the OpenNeuro CRN API, but the
endpoint is no longer reliable.  The revised version works with any HTTP(S)
URL (including the HuggingFace mirror used in the quick‑start) and respects
the RAM limit (``MAX_RAM_GB``) by checking the ``Content‑Length`` header when
available.

The script exits with status ``1`` if any dataset is estimated to exceed the
RAM limit; otherwise it returns ``0`` after successful download and manifest
creation.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

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
# Helper utilities
# ----------------------------------------------------------------------
def get_filename_from_url(url: str) -> str:
    """Extract the final path component from a URL."""
    return Path(url).name or f"download_{abs(hash(url))}"

def estimate_size_gb(url: str) -> float:
    """
    Perform a HEAD request to obtain the ``Content‑Length`` header (if present)
    and return the size in gigabytes.  Returns ``0.0`` when the size cannot be
    determined.
    """
    try:
        response = requests.head(
            url,
            timeout=15,
            allow_redirects=True,
            headers={"User-Agent": "python-requests"},
        )
        response.raise_for_status()
        length = response.headers.get("Content-Length")
        if length is None:
            logger.warning(f"Content‑Length header missing for {url}; size unknown.")
            return 0.0
        size_bytes = int(length)
        size_gb = size_bytes / (1024 ** 3)
        logger.info(f"Estimated size for {url}: {size_gb:.3f} GB")
        return size_gb
    except requests.RequestException as exc:
        logger.error(f"Failed to perform HEAD request for {url}: {exc}")
        # Propagate the error – the caller will exit with code 1.
        raise

def download_file(url: str, dest_path: Path) -> int:
    """
    Stream‑download ``url`` to ``dest_path``.  Returns the number of bytes written.
    """
    logger.info(f"Downloading {url} → {dest_path}")
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "python-requests"}) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            total_written = 0
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                total_written += len(chunk)
    logger.info(f"Finished download ({total_written} bytes)")
    return total_written

# ----------------------------------------------------------------------
# Main ingestion routine
# ----------------------------------------------------------------------
def run_ingestion(urls: List[str], output_dir: Path) -> None:
    """
    Download each URL, enforce the RAM limit, and write a manifest file.

    Parameters
    ----------
    urls: List[str]
        One or more HTTP(S) URLs pointing to dataset files.
    output_dir: Path
        Directory where files will be stored.  It is created if missing.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: List[Dict[str, Any]] = []

    for url in urls:
        # ---- Size check -------------------------------------------------
        try:
            size_gb = estimate_size_gb(url)
        except Exception:
            logger.error("Aborting ingestion due to size‑estimation failure.")
            sys.exit(1)

        if size_gb > MAX_RAM_GB:
            logger.error(
                f"Dataset at {url} estimated size ({size_gb:.2f} GB) exceeds the "
                f"memory limit of {MAX_RAM_GB} GB. Halting."
            )
            sys.exit(1)

        # ---- Download ----------------------------------------------------
        filename = get_filename_from_url(url)
        dest_path = output_dir / filename
        try:
            size_bytes = download_file(url, dest_path)
        except Exception as exc:
            logger.error(f"Download failed for {url}: {exc}")
            sys.exit(1)

        # ---- Manifest entry -----------------------------------------------
        dataset_id = Path(filename).stem  # use filename without extension as id
        entry = {
            "url": url,
            "sha256": None,
            "size_bytes": size_bytes,
            "file_count": 1,
            "dataset_id": dataset_id,
        }
        manifest_entries.append(entry)

    # ---- Write manifest -------------------------------------------------
    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download dataset files and produce a manifest (Task T003)."
    )
    parser.add_argument(
        "--dataset-url",
        action="append",
        required=True,
        help="URL of a dataset file to download. Can be provided multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        default=get_path("raw"),
        help="Directory to store downloaded files (default: project raw data folder).",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_cli()
    output_dir = Path(args.output_dir)
    run_ingestion(args.dataset_url, output_dir)

if __name__ == "__main__":
    main()