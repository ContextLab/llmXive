"""
Ingestion script for the Social Rejection project (Task T003).

This script queries the OpenNeuro API for specific dataset IDs, verifies that
the total size of each dataset does not exceed the memory limit (MAX_RAM_GB),
stream-downloads the files while preserving the directory structure, and
writes a manifest file recording the metadata.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import quote

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
# OpenNeuro API Helpers
# ----------------------------------------------------------------------
def get_dataset_files(dataset_id: str) -> List[Dict[str, Any]]:
    """
    Query the OpenNeuro API to get the list of files for a dataset.
    """
    url = f"https://openneuro.org/api/datasets/{dataset_id}/files"
    logger.info(f"Querying OpenNeuro API for {dataset_id} files: {url}")
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": "llmXive-research-agent"})
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.error(f"Failed to query OpenNeuro API for {dataset_id}: {exc}")
        sys.exit(1)

def download_openneuro_file(dataset_id: str, file_path: str, dest_path: Path) -> int:
    """
    Stream-download a specific file from an OpenNeuro dataset.
    """
    # The file path in the API request must be URL-encoded
    encoded_path = quote(file_path, safe='')
    url = f"https://openneuro.org/api/datasets/{dataset_id}/files/{encoded_path}"
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {file_path} → {dest_path}")
    try:
        with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "llmXive-research-agent"}) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                total_written = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    total_written += len(chunk)
        return total_written
    except Exception as exc:
        logger.error(f"Download failed for {file_path} at {url}: {exc}")
        raise

# ----------------------------------------------------------------------
# Main ingestion routine
# ----------------------------------------------------------------------
def run_ingestion(dataset_ids: List[str], output_dir: Path) -> None:
    """
    Implement T003:
    1. Query API, sum sizes, halt if > 7GB.
    2. Stream-download preserving filenames.
    3. Write manifest.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries: List[Dict[str, Any]] = []

    for ds_id in dataset_ids:
        # ---- 1. Query and Size Check ----------------------------------
        files_list = get_dataset_files(ds_id)
        total_size_bytes = sum(f.get('size', 0) for f in files_list)
        total_size_gb = total_size_bytes / (1024 ** 3)
        
        logger.info(f"Dataset {ds_id} total estimated size: {total_size_gb:.3f} GB")
        
        if total_size_gb > MAX_RAM_GB:
            logger.error(
                f"Dataset {ds_id} size ({total_size_gb:.2f} GB) exceeds "
                f"the memory limit of {MAX_RAM_GB} GB. Halting."
            )
            sys.exit(1)

        # ---- 2. Stream-Download ----------------------------------------
        file_count = 0
        for file_info in files_list:
            rel_path = file_info['name']
            # We store under data/raw/{ds_id}/{rel_path} to avoid collisions
            # and preserve the original dataset structure.
            dest_path = output_dir / ds_id / rel_path
            try:
                download_openneuro_file(ds_id, rel_path, dest_path)
                file_count += 1
            except Exception:
                logger.error(f"Critical failure downloading {rel_path}. Aborting.")
                sys.exit(1)

        # ---- 3. Manifest entry ------------------------------------------
        # URL is the dataset landing page
        entry = {
            "url": f"https://openneuro.org/datasets/{ds_id}",
            "sha256": None,
            "size_bytes": total_size_bytes,
            "file_count": file_count,
            "dataset_id": ds_id,
        }
        manifest_entries.append(entry)

    # ---- Write manifest -----------------------------------------------
    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download OpenNeuro datasets and produce a manifest (Task T003)."
    )
    parser.add_argument(
        "--dataset-ids",
        nargs="+",
        required=True,
        help="List of OpenNeuro dataset IDs to download (e.g., ds000208 ds003392).",
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
    run_ingestion(args.dataset_ids, output_dir)

if __name__ == "__main__":
    main()
