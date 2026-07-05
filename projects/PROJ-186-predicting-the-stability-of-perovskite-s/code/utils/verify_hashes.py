"""
Script to generate and save content hashes for all artifacts in data/ and results/.
This script ensures reproducibility by creating a manifest of SHA256 hashes.
"""
import os
import sys
import logging
from pathlib import Path

from utils.logging_config import get_logger, log_pipeline_event
from utils.hashing import generate_hashes_for_artifacts

logger = get_logger(__name__)

def main():
    """Main entry point for hash generation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    results_dir = project_root / "results"
    manifest_path = project_root / "results" / "artifact_hashes.json"

    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
    if not results_dir.exists():
        logger.warning(f"Results directory not found: {results_dir}")

    log_pipeline_event("Running artifact hash verification (T044)")

    try:
        hashes = generate_hashes_for_artifacts(
            data_dir=data_dir,
            results_dir=results_dir,
            manifest_path=manifest_path
        )

        total_files = len(hashes["data"]) + len(hashes["results"])
        logger.info(f"Successfully generated hashes for {total_files} artifacts.")
        logger.info(f"Manifest saved to: {manifest_path}")

        # Print summary
        print(f"\nArtifact Hash Summary (T044):")
        print(f"  Data files: {len(hashes['data'])}")
        print(f"  Results files: {len(hashes['results'])}")
        print(f"  Total: {total_files}")
        print(f"  Manifest: {manifest_path}")

    except Exception as e:
        logger.error(f"Failed to generate hashes: {e}")
        raise

if __name__ == "__main__":
    main()
