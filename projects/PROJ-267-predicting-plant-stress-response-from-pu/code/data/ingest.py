"""
Ingestion orchestrator.

This script is the public entry point used by the quick‑start
(`python code/data/ingest.py --species <species> --stress <stress>`).
It delegates the actual download work to ``code.data.download`` and
then creates a SHA‑256 checksum manifest for the ``data/raw`` folder.
The ``--species`` and ``--stress`` arguments are kept for API stability;
the current implementation does not filter URLs because the test
dataset (GSE14784) is a generic example covering all species/stress
combinations.
"""

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths
from utils.logging_config import get_logger

# Import the download helper we just implemented
from code.data.download import main as download_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Download raw GEO/ProteomeXchange files and generate checksums."
    )
    parser.add_argument(
        "--species",
        type=str,
        required=True,
        help="Target plant species (e.g., Arabidopsis).",
    )
    parser.add_argument(
        "--stress",
        type=str,
        required=True,
        help="Target abiotic stress condition (e.g., Drought).",
    )
    return parser.parse_args()

def run_ingest():
    """
    Run the ingestion pipeline.

    Steps:
    1. Ensure ``data/raw`` exists.
    2. Call the download routine (which writes files into ``data/raw``).
    3. Verify that each downloaded file is larger than 1 KB
       (the ``download_file`` helper already enforces this).
    4. The download routine also writes ``checksums.sha256``.
    """
    raw_dir: Path = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Starting ingestion for species={args.species}, stress={args.stress}"
    )
    # The download_main function performs the full download + checksum creation.
    download_main()

    # Simple sanity check – ensure at least one file > 1 KB exists.
    files = list(raw_dir.iterdir())
    if not files:
        raise RuntimeError("No files were downloaded into the raw data directory.")

    large_files = [f for f in files if f.is_file() and f.stat().st_size > 1024]
    if not large_files:
        raise RuntimeError(
            "Downloaded files exist but none are larger than 1 KB. "
            "This likely indicates a problem with the data source."
        )

    logger.info(
        f"Ingestion completed: {len(large_files)} file(s) >1 KB in {raw_dir}"
    )
    print(f"Ingestion successful. Raw data directory: {raw_dir}")

if __name__ == "__main__":
    try:
        args = parse_args()
        run_ingest()
    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}")
        sys.exit(1)