"""
Quickstart validation script for PROJ-465.

This script validates the entire pipeline by:
1. Ensuring event data is available (fetching from GWOSC if necessary)
2. Running the full downsampling and inference pipeline
3. Generating checksums for all artifacts
4. Verifying artifact integrity

Usage:
    python code/validation/run_quickstart.py
"""

import os
import sys
import logging
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR, RESULTS_DIR, ensure_directories
from utils.seeds import set_global_seed
from utils.logging_config import setup_logging, get_derivation_logger
from utils.hash_artifact import compute_file_hash, save_hash_manifest, load_hash_manifest, verify_artifact_integrity
from data.download import fetch_high_snr_events, download_strain_data, save_strain_data
from data.transform import generate_all_resolutions
from inference.run_bilby import run_inference
from analysis.metrics import compute_metrics_for_resolution
from analysis.aggregate import aggregate_results, save_aggregation_report

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)
derivation_logger = get_derivation_logger("quickstart_validation")

def ensure_event_data(event_id: str = "GW150914") -> Path:
    """
    Ensure event data is available. Fetch from GWOSC if not present.

    Args:
        event_id: The event ID to fetch (default: GW150914)

    Returns:
        Path to the downloaded strain data file
    """
    ensure_directories()
    strain_dir = DATA_DIR / "raw" / "strain"
    strain_dir.mkdir(parents=True, exist_ok=True)

    expected_file = strain_dir / f"{event_id}_strain.h5"

    if expected_file.exists():
        logger.info(f"Event data already exists: {expected_file}")
        return expected_file

    logger.info(f"Fetching event data for {event_id} from GWOSC...")
    try:
        # Fetch high SNR events
        events = fetch_high_snr_events(min_snr=20, event_ids=[event_id])
        if not events:
            raise ValueError(f"No high-SNR data found for {event_id}")

        event_data = events[0]
        strain_file = download_strain_data(event_data)
        saved_path = save_strain_data(strain_file, event_id)

        logger.info(f"Successfully downloaded and saved strain data: {saved_path}")
        return saved_path

    except Exception as e:
        logger.error(f"Failed to fetch event data: {e}")
        raise

def run_pipeline(event_id: str, resolutions: List[int] = [4096, 2048, 1024]) -> Dict[str, Any]:
    """
    Run the full downsampling and inference pipeline for an event.

    Args:
        event_id: The event ID to process
        resolutions: List of sampling rates to test

    Returns:
        Dictionary containing pipeline results
    """
    logger.info(f"Starting pipeline for event {event_id} with resolutions: {resolutions}")

    # Ensure data is available
    strain_path = ensure_event_data(event_id)

    # Generate all resolutions
    resolution_results = generate_all_resolutions(strain_path, resolutions)

    # Run inference for each resolution
    posterior_files = []
    for res_config, strain_data in resolution_results.items():
        logger.info(f"Running inference for resolution: {res_config}")

        posterior_path = run_inference(
            strain_data=strain_data,
            resolution_config=res_config,
            event_id=event_id
        )

        if posterior_path:
            posterior_files.append(posterior_path)
            logger.info(f"Generated posterior: {posterior_path}")

    # Compute metrics for each resolution
    metrics_results = {}
    baseline_path = None
    for res_config in resolutions:
        # Find the posterior file for this resolution
        res_posteriors = [p for p in posterior_files if str(res_config) in str(p)]
        if not res_posteriors:
            logger.warning(f"No posterior found for resolution {res_config}")
            continue

        posterior_path = res_posteriors[0]

        # Calculate metrics
        metrics = compute_metrics_for_resolution(
            posterior_path=posterior_path,
            resolution_config=res_config,
            event_id=event_id
        )

        if metrics:
            metrics_results[res_config] = metrics
            if res_config == 4096:
                baseline_path = posterior_path

    # Aggregate results
    if metrics_results:
        aggregation = aggregate_results(metrics_results, event_id)
        report_path = save_aggregation_report(aggregation, event_id)
        logger.info(f"Saved aggregation report: {report_path}")

    return {
        "event_id": event_id,
        "posterior_files": posterior_files,
        "metrics_results": metrics_results,
        "aggregation_report": report_path if metrics_results else None
    }

def generate_checksums(results_dir: Path) -> Path:
    """
    Generate checksums for all artifacts in the results directory.

    Args:
        results_dir: Path to the results directory

    Returns:
        Path to the checksum manifest file
    """
    logger.info(f"Generating checksums for artifacts in {results_dir}")

    manifest = {
        "version": "1.0",
        "generated_at": "",
        "artifacts": []
    }

    # Walk through all files in results directory
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(results_dir)

            try:
                file_hash = compute_file_hash(file_path)
                manifest["artifacts"].append({
                    "path": str(rel_path),
                    "hash": file_hash,
                    "size": file_path.stat().st_size
                })
                logger.debug(f"Checksummed: {rel_path} -> {file_hash[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to checksum {file_path}: {e}")

    manifest["generated_at"] = str(Path(__file__).parent.parent.parent / "data" / "derived" / "checksums")
    manifest_path = results_dir / "checksum_manifest.json"

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Saved checksum manifest: {manifest_path}")
    return manifest_path

def verify_artifacts(results_dir: Path) -> bool:
    """
    Verify artifact integrity using checksums.

    Args:
        results_dir: Path to the results directory

    Returns:
        True if all artifacts are valid, False otherwise
    """
    manifest_path = results_dir / "checksum_manifest.json"

    if not manifest_path.exists():
        logger.error(f"Checksum manifest not found: {manifest_path}")
        return False

    logger.info(f"Verifying artifacts using manifest: {manifest_path}")

    try:
        manifest = load_hash_manifest(manifest_path)
        all_valid = True

        for artifact in manifest["artifacts"]:
            file_path = results_dir / artifact["path"]
            if not file_path.exists():
                logger.error(f"Artifact missing: {artifact['path']}")
                all_valid = False
                continue

            current_hash = compute_file_hash(file_path)
            if current_hash != artifact["hash"]:
                logger.error(f"Hash mismatch for {artifact['path']}: expected {artifact['hash']}, got {current_hash}")
                all_valid = False
            else:
                logger.debug(f"Verified: {artifact['path']}")

        if all_valid:
            logger.info("All artifacts verified successfully!")
        else:
            logger.error("Some artifacts failed verification!")

        return all_valid

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def main():
    """
    Main entry point for quickstart validation.
    """
    logger.info("=" * 80)
    logger.info("Starting Quickstart Validation for PROJ-465")
    logger.info("=" * 80)

    # Set global seed for reproducibility
    set_global_seed(42)

    # Ensure directories exist
    ensure_directories()

    # Run pipeline for GW150914
    event_id = "GW150914"
    try:
        results = run_pipeline(event_id)

        if not results["posterior_files"]:
            logger.error("Pipeline failed to generate any posterior files")
            sys.exit(1)

        logger.info(f"Pipeline completed successfully for {event_id}")
        logger.info(f"Generated {len(results['posterior_files'])} posterior files")

        # Generate checksums
        checksum_path = generate_checksums(RESULTS_DIR)

        # Verify artifacts
        if verify_artifacts(RESULTS_DIR):
            logger.info("=" * 80)
            logger.info("Quickstart Validation PASSED")
            logger.info("=" * 80)
            logger.info(f"Checksum manifest: {checksum_path}")
            logger.info(f"Results directory: {RESULTS_DIR}")
            return 0
        else:
            logger.error("=" * 80)
            logger.error("Quickstart Validation FAILED - Artifact verification failed")
            logger.error("=" * 80)
            return 1

    except Exception as e:
        logger.error(f"Quickstart validation failed with error: {e}")
        logger.exception("Full traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
