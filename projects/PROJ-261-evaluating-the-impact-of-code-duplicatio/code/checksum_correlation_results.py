"""
T036: Add checksum computation for correlation results and record in artifact_hashes state manifest.

This script computes SHA256 checksums for correlation analysis outputs and records them
in the checksum manifest for reproducibility and version tracking (SC-006, Constitution Principle V).
"""
import logging
import sys
from pathlib import Path

# Import from existing checksum_manifest module
from checksum_manifest import (
    setup_logging,
    compute_file_checksum,
    load_manifest,
    save_manifest,
    record_artifact_checksums,
)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent

# Output path for correlation results (from T034)
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "analysis" / "correlation_results.csv"

# Manifest path
MANIFEST_PATH = PROJECT_ROOT / "data" / "analysis" / "checksum_manifest.json"

def main():
    """
    Main entry point for T036: compute and record checksums for correlation results.
    """
    # Setup logging
    logger = setup_logging("T036_checksum_correlation")
    logger.info("Starting checksum computation for correlation results (T036)")

    # Verify correlation results file exists
    if not CORRELATION_RESULTS_PATH.exists():
        logger.error(f"Correlation results file not found: {CORRELATION_RESULTS_PATH}")
        logger.error("Please ensure T034 has completed and saved correlation_results.csv")
        sys.exit(1)

    logger.info(f"Found correlation results at: {CORRELATION_RESULTS_PATH}")

    # Load existing manifest or create new one
    if MANIFEST_PATH.exists():
        logger.info(f"Loading existing manifest from: {MANIFEST_PATH}")
        manifest = load_manifest(MANIFEST_PATH)
    else:
        logger.info(f"Creating new manifest at: {MANIFEST_PATH}")
        manifest = {
            "version": "1.0",
            "created_at": None,
            "updated_at": None,
            "artifact_hashes": {},
            "metadata": {
                "project": "PROJ-261-evaluating-the-impact-of-code-duplication",
                "task": "T036",
                "description": "Checksum computation for correlation results",
            },
        }

    # Compute checksum for correlation results
    logger.info(f"Computing checksum for: {CORRELATION_RESULTS_PATH}")
    checksum = compute_file_checksum(CORRELATION_RESULTS_PATH, algorithm="sha256")

    if checksum is None:
        logger.error(f"Failed to compute checksum for: {CORRELATION_RESULTS_PATH}")
        sys.exit(1)

    logger.info(f"Checksum computed: {checksum[:16]}...")

    # Record the artifact checksum
    artifact_key = "correlation_results.csv"
    artifact_info = {
        "path": str(CORRELATION_RESULTS_PATH.relative_to(PROJECT_ROOT)),
        "checksum": checksum,
        "algorithm": "sha256",
        "size_bytes": CORRELATION_RESULTS_PATH.stat().st_size,
        "task": "T036",
        "description": "Correlation analysis results with Spearman coefficients and p-values",
    }

    record_artifact_checksums(manifest, artifact_key, artifact_info)

    # Save updated manifest
    logger.info(f"Saving updated manifest to: {MANIFEST_PATH}")
    save_manifest(manifest, MANIFEST_PATH)

    logger.info("T036 completed successfully")
    logger.info(f"Artifact recorded: {artifact_key} -> {checksum[:32]}...")

    return 0

if __name__ == "__main__":
    sys.exit(main())
