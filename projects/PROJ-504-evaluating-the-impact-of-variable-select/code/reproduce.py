from __future__ import annotations

import os
import sys
import hashlib
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import project modules
from utils.logger import get_logger
from config import get_config
from data.downloader import fetch_datasets, main as downloader_main
from data.simulators import generate_synthetic_outcomes, main as simulators_main
from analysis.selectors import lasso_selection, select_variables_lasso, main as selectors_main
from analysis.metrics import calculate_empirical_power, main as metrics_main
from data.storage import save_simulation_manifest, main as storage_main

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger(__name__)


def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Compute SHA-256 checksum of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksums(checksum_file: str, expected_checksums: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verify that current file checksums match expected ones.

    Args:
        checksum_file: Path to the manifest file containing checksums
        expected_checksums: Dictionary of {relative_path: expected_checksum}

    Returns:
        Tuple of (all_match, list_of_mismatches)
    """
    if not os.path.exists(checksum_file):
        logger.error(f"Checksum file not found: {checksum_file}")
        return False, [f"Checksum file not found: {checksum_file}"]

    with open(checksum_file, "r") as f:
        stored_checksums = json.load(f)

    mismatches = []
    all_match = True

    for rel_path, expected in expected_checksums.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(full_path):
            mismatches.append(f"File missing: {rel_path}")
            all_match = False
            continue

        try:
            actual = compute_file_checksum(full_path)
            if actual != expected:
                mismatches.append(f"Checksum mismatch for {rel_path}: expected {expected}, got {actual}")
                all_match = False
            else:
                logger.info(f"Checksum verified: {rel_path}")
        except Exception as e:
            mismatches.append(f"Error computing checksum for {rel_path}: {str(e)}")
            all_match = False

    return all_match, mismatches


def run_pipeline_stage(stage_name: str, stage_func: callable, args: Optional[List[Any]] = None) -> bool:
    """
    Run a specific pipeline stage with error handling and logging.

    Args:
        stage_name: Name of the stage for logging
        stage_func: Function to execute
        args: Optional list of arguments to pass to the function

    Returns:
        True if stage completed successfully, False otherwise
    """
    logger.info(f"Starting pipeline stage: {stage_name}")
    start_time = time.time()

    try:
        if args:
            stage_func(*args)
        else:
            stage_func()

        elapsed = time.time() - start_time
        logger.info(f"Stage {stage_name} completed successfully in {elapsed:.2f}s")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Stage {stage_name} failed after {elapsed:.2f}s: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_checksum_manifest(output_path: str, files_to_checksum: List[str]) -> Dict[str, str]:
    """
    Generate a checksum manifest for specified files.

    Args:
        output_path: Path to save the manifest JSON
        files_to_checksum: List of relative file paths to checksum

    Returns:
        Dictionary of {relative_path: checksum}
    """
    checksums = {}
    for rel_path in files_to_checksum:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if os.path.exists(full_path):
            checksums[rel_path] = compute_file_checksum(full_path)
            logger.info(f"Checksum generated for {rel_path}: {checksums[rel_path]}")
        else:
            logger.warning(f"File not found for checksum: {rel_path}")

    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)

    return checksums


def main():
    """
    Main reproducibility verification routine.

    This function:
    1. Loads configuration with pinned seeds
    2. Re-runs the entire pipeline (download, simulate, analyze)
    3. Computes checksums of all output files
    4. Compares against a previous run's checksums (if available)
    5. Reports pass/fail status
    """
    logger.info("=" * 60)
    logger.info("REPRODUCIBILITY VERIFICATION PIPELINE")
    logger.info("=" * 60)

    # Load configuration
    config = get_config()
    logger.info(f"Configuration loaded. Seed: {config.seed}")

    # Define files to checksum
    output_files = [
        "data/processed/simulation_results.csv",
        "data/processed/simulation_manifest.json",
        "results/final_report.md",
        "results/sensitivity_report.csv"
    ]

    # Create checksum directory if needed
    checksum_dir = PROJECT_ROOT / "state"
    checksum_dir.mkdir(exist_ok=True)
    previous_checksums_file = checksum_dir / "previous_run_checksums.json"
    current_checksums_file = checksum_dir / "current_run_checksums.json"

    # Check if previous checksums exist
    previous_checksums = {}
    if previous_checksums_file.exists():
        with open(previous_checksums_file, "r") as f:
            previous_checksums = json.load(f)
        logger.info(f"Previous checksums loaded from {previous_checksums_file}")
    else:
        logger.warning(f"No previous checksums found at {previous_checksums_file}. "
                     "This run will establish the baseline.")

    # Step 1: Download datasets
    success = run_pipeline_stage(
        "Download Datasets",
        downloader_main,
        [config]
    )
    if not success:
        logger.error("Pipeline aborted: Download stage failed")
        return 1

    # Step 2: Generate synthetic outcomes
    success = run_pipeline_stage(
        "Generate Synthetic Outcomes",
        simulators_main,
        [config]
    )
    if not success:
        logger.error("Pipeline aborted: Simulation stage failed")
        return 1

    # Step 3: Run selection methods
    success = run_pipeline_stage(
        "Run Selection Methods",
        selectors_main,
        [config]
    )
    if not success:
        logger.error("Pipeline aborted: Selection stage failed")
        return 1

    # Step 4: Calculate metrics
    success = run_pipeline_stage(
        "Calculate Metrics",
        metrics_main,
        [config]
    )
    if not success:
        logger.error("Pipeline aborted: Metrics stage failed")
        return 1

    # Step 5: Save results
    success = run_pipeline_stage(
        "Save Results",
        storage_main,
        [config]
    )
    if not success:
        logger.error("Pipeline aborted: Storage stage failed")
        return 1

    # Generate current checksums
    logger.info("Generating checksums for output files...")
    current_checksums = generate_checksum_manifest(
        str(current_checksums_file),
        output_files
    )

    # Compare with previous if available
    if previous_checksums:
        logger.info("Comparing checksums with previous run...")
        all_match, mismatches = verify_checksums(
            str(previous_checksums_file),
            current_checksums
        )

        if all_match:
            logger.info("=" * 60)
            logger.info("REPRODUCIBILITY CHECK: PASSED")
            logger.info("All output files match previous run checksums.")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("=" * 60)
            logger.error("REPRODUCIBILITY CHECK: FAILED")
            logger.error("Checksum mismatches detected:")
            for mismatch in mismatches:
                logger.error(f"  - {mismatch}")
            logger.error("=" * 60)
            return 1
    else:
        logger.info("=" * 60)
        logger.info("REPRODUCIBILITY BASELINE ESTABLISHED")
        logger.info("No previous run to compare against. "
                   f"Checksums saved to {current_checksums_file}")
        logger.info("Re-run this task to verify reproducibility.")
        logger.info("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
