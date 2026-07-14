from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, log_and_exit

# Constants
BENCHMARK_DIR = Path("data/raw/benchmark")
METADATA_FILE = Path("datasets/metadata.yaml")
SOURCES_FILE = Path("datasets/sources.yaml")

logger = get_logger("benchmark_downloader")


def load_sources_config() -> Dict[str, Any]:
    """Load the sources configuration file."""
    if not SOURCES_FILE.exists():
        raise PipelineError(f"Sources configuration file not found: {SOURCES_FILE}")
    
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_file(url: str, dest_path: Path) -> None:
    """Download a file from a URL to the destination path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
    except Exception as e:
        raise PipelineError(f"Failed to download {url}: {e}")


def update_metadata(file_name: str, checksum: str, source_url: str, file_size: int) -> None:
    """Update the metadata file with the new file information."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {}

    if "benchmark_files" not in metadata:
        metadata["benchmark_files"] = {}

    metadata["benchmark_files"][file_name] = {
        "checksum": checksum,
        "source_url": source_url,
        "file_size": file_size,
        "downloaded_at": str(Path.cwd())  # Placeholder for timestamp logic if needed
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    logger.info(f"Updated metadata for {file_name}")


def main() -> int:
    """Main entry point for downloading benchmark data."""
    parser = argparse.ArgumentParser(description="Download benchmark data for T056")
    parser.add_argument(
        "--config",
        type=Path,
        default=SOURCES_FILE,
        help="Path to sources configuration file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BENCHMARK_DIR,
        help="Output directory for downloaded files"
    )
    args = parser.parse_args()

    try:
        sources_config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    except Exception as e:
        log_and_exit(f"Failed to load sources config: {e}", logger)
        return 1

    benchmark_sources = sources_config.get("benchmark", [])
    if not benchmark_sources:
        log_and_exit("No benchmark sources found in configuration", logger)
        return 1

    logger.info(f"Processing {len(benchmark_sources)} benchmark sources")

    for source in benchmark_sources:
        file_name = source.get("file")
        url = source.get("url")
        expected_checksum = source.get("checksum")

        if not all([file_name, url]):
            logger.warning(f"Skipping invalid source entry: {source}")
            continue

        dest_path = args.output_dir / file_name

        if dest_path.exists():
            logger.info(f"File already exists: {dest_path}")
            current_checksum = compute_sha256(dest_path)
            if expected_checksum and current_checksum != expected_checksum:
                logger.warning(f"Checksum mismatch for {file_name}. Re-downloading.")
                dest_path.unlink()
                download_file(url, dest_path)
            else:
                continue
        else:
            download_file(url, dest_path)

        # Verify checksum
        actual_checksum = compute_sha256(dest_path)
        file_size = dest_path.stat().st_size

        if expected_checksum and actual_checksum != expected_checksum:
            log_and_exit(
                f"Checksum verification failed for {file_name}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}",
                logger
            )
            return 1

        logger.info(f"Successfully downloaded and verified {file_name} (SHA256: {actual_checksum})")
        update_metadata(file_name, actual_checksum, url, file_size)

    logger.info("All benchmark files downloaded and verified successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
