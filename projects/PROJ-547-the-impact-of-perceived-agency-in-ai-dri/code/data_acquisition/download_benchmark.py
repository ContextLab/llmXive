from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, Union

import yaml

from logging.pipeline_logger import get_logger

# Constants
BENCHMARK_DIR = Path("data/raw/benchmark")
SOURCES_FILE = Path("datasets/sources.yaml")
METADATA_FILE = Path("datasets/metadata.yaml")

logger = get_logger(__name__)


def load_sources_config(sources_path: Path) -> Dict[str, Any]:
    """Load the sources configuration YAML."""
    if not sources_path.exists():
        logger.error(f"Sources configuration file not found: {sources_path}")
        raise FileNotFoundError(f"Sources configuration file not found: {sources_path}")

    with open(sources_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_file(url: str, dest_path: Path, expected_checksum: str | None = None) -> bool:
    """Download a file from a URL to a destination path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading {url} to {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Downloaded {url} successfully")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

    if expected_checksum:
        actual_checksum = compute_sha256(dest_path)
        if actual_checksum != expected_checksum:
            logger.error(
                f"Checksum mismatch for {dest_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            return False
        logger.info(f"Checksum verified for {dest_path}")

    return True


def update_metadata(metadata_path: Path, dataset_name: str, file_path: Path, checksum: str) -> None:
    """Update the metadata YAML file with the new dataset entry."""
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}

    metadata[dataset_name] = {
        "path": str(file_path),
        "checksum": checksum,
        "downloaded_at": "now"  # In a real implementation, use datetime.now().isoformat()
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    logger.info(f"Updated metadata for {dataset_name} in {metadata_path}")


def main() -> None:
    """Main entry point for downloading the benchmark dataset."""
    parser = argparse.ArgumentParser(description="Download benchmark dataset")
    parser.add_argument(
        "--sources",
        type=Path,
        default=SOURCES_FILE,
        help="Path to sources.yaml configuration file",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=METADATA_FILE,
        help="Path to metadata.yaml file for recording checksums",
    )
    args = parser.parse_args()

    sources_config = load_sources_config(args.sources)

    # Assume the benchmark dataset is under a 'benchmark' key in sources.yaml
    if "benchmark" not in sources_config:
        logger.error("No 'benchmark' entry found in sources.yaml")
        sys.exit(1)

    benchmark_entries: Dict[str, Dict[str, Any]] = sources_config["benchmark"]

    success = True
    for name, entry in benchmark_entries.items():
        url = entry.get("url")
        expected_checksum = entry.get("checksum")

        if not url:
            logger.error(f"Missing URL for benchmark entry: {name}")
            success = False
            continue

        # Construct destination path
        filename = url.split("/")[-1]
        dest_path = BENCHMARK_DIR / filename

        if download_file(url, dest_path, expected_checksum):
            actual_checksum = compute_sha256(dest_path)
            update_metadata(args.metadata, name, dest_path, actual_checksum)
        else:
            success = False

    if success:
        logger.info("Benchmark dataset download completed successfully")
        sys.exit(0)
    else:
        logger.error("Benchmark dataset download failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
