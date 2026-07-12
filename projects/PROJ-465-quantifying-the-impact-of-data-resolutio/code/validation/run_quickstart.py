"""
Quickstart Validation Script for PROJ-465.

This script validates the end-to-end pipeline by:
1. Ensuring all required directories exist.
2. Running the data download, transformation, inference, and analysis pipeline
   on a single high-SNR event (GW150914) if data is not present.
3. Generating checksums for all produced artifacts (posteriors, metrics, reports).
4. Verifying artifact integrity.

Usage:
    python code/validation/run_quickstart.py
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.config import DATA_DIR, RESULTS_DIR, ensure_directories
from code.utils.logging_config import setup_logging, get_derivation_logger
from code.utils.hash_artifact import compute_file_hash, save_hash_manifest, verify_artifact_integrity
from code.utils.seeds import set_global_seed
from code.data.download import fetch_high_snr_events, download_strain_data
from code.data.transform import apply_resolution_transforms
from code.inference.run_bilby import run_inference
from code.analysis.metrics import compute_metrics_for_resolution
from code.analysis.aggregate import aggregate_results, save_aggregation_report

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
setup_logging(log_level=logging.INFO, log_dir=str(LOG_DIR))
logger = get_derivation_logger("quickstart_validation")

# Constants
TARGET_EVENT = "GW150914"
SAMPLE_RATE = 4096
RESOLUTIONS = [4096, 2048, 1024]
BIT_DEPTHS = [32, 16]
MAX_STEPS = 5000
DLOGZ_THRESHOLD = 0.1
SEED = 42

def ensure_event_data(event_id: str) -> Optional[Path]:
    """
    Fetches or locates strain data for a specific event.
    Returns the path to the data file, or None if unavailable.
    """
    logger.info(f"Checking for data for event: {event_id}")
    
    # Try to find existing data
    raw_dir = DATA_DIR / "raw"
    if raw_dir.exists():
        candidates = list(raw_dir.glob(f"*{event_id}*"))
        if candidates:
            logger.info(f"Found existing data: {candidates[0]}")
            return candidates[0]

    # Attempt to download
    logger.info(f"Attempting to fetch high-SNR events from GWOSC for {event_id}...")
    try:
        events = fetch_high_snr_events(min_snr=20, max_results=1)
        if not events:
            logger.warning("No high-SNR events found in catalog.")
            return None
        
        # Filter for our target or take the first
        target_event = next((e for e in events if event_id in e.get('name', '')), events[0])
        event_name = target_event.get('name')
        
        logger.info(f"Downloading strain data for {event_name}...")
        data_path = download_strain_data(event_name, start_time=target_event.get('gps_start'), 
                                         end_time=target_event.get('gps_end'),
                                         sampling_rate=SAMPLE_RATE)
        return data_path
    except Exception as e:
        logger.error(f"Failed to download data: {e}", exc_info=True)
        return None

def run_pipeline(data_path: Path) -> Dict[str, Any]:
    """
    Executes the full pipeline: Transform -> Inference -> Metrics -> Aggregation.
    """
    logger.info("Starting Pipeline Execution")
    
    # 1. Transform: Generate all resolutions
    logger.info("Applying resolution transforms...")
    transformed_data = apply_resolution_transforms(
        input_path=data_path,
        resolutions=RESOLUTIONS,
        bit_depths=BIT_DEPTHS
    )
    
    results = {}
    
    # 2. Inference & Metrics
    for res_config, file_path in transformed_data.items():
        sample_rate = res_config['sampling_rate']
        bit_depth = res_config['bit_depth']
        logger.info(f"Running inference for {sample_rate}Hz, {bit_depth}-bit...")
        
        # Run Inference
        posterior_path = run_inference(
            strain_file=str(file_path),
            sample_rate=sample_rate,
            event_id=TARGET_EVENT,
            max_steps=MAX_STEPS,
            dlogz_threshold=DLOGZ_THRESHOLD,
            seed=SEED
        )
        
        if not posterior_path:
            logger.warning(f"Inference failed for {res_config}. Skipping metrics.")
            continue
        
        # Compute Metrics
        logger.info(f"Computing metrics for {res_config}...")
        metrics = compute_metrics_for_resolution(
            posterior_file=str(posterior_path),
            resolution_config=res_config,
            baseline_sampling_rate=4096
        )
        
        results[str(res_config)] = {
            "posterior_file": str(posterior_path),
            "metrics": metrics
        }

    # 3. Aggregate
    logger.info("Aggregating results...")
    metrics_dir = RESULTS_DIR / "metrics"
    if not metrics_dir.exists():
        metrics_dir.mkdir(parents=True)
        
    # Save individual metrics files first (if not already done by compute_metrics_for_resolution)
    # Assuming compute_metrics_for_resolution saves to RESULTS_DIR/metrics
    
    aggregation_report = save_aggregation_report(
        output_path=str(RESULTS_DIR / "metrics" / "aggregation_report.json"),
        results_dir=str(metrics_dir)
    )
    
    return results

def generate_checksums() -> Dict[str, str]:
    """
    Generates SHA-256 checksums for all artifacts in data/derived and results/.
    """
    logger.info("Generating checksums for all artifacts...")
    manifest = {}
    
    artifact_dirs = [
        DATA_DIR / "derived",
        RESULTS_DIR / "posteriors",
        RESULTS_DIR / "metrics",
        RESULTS_DIR / "figures"
    ]
    
    for dir_path in artifact_dirs:
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".sha256"):
                file_hash = compute_file_hash(file_path)
                rel_path = file_path.relative_to(Path.cwd())
                manifest[str(rel_path)] = file_hash
    
    # Save manifest
    manifest_path = Path("artifacts_manifest.json")
    save_hash_manifest(manifest, str(manifest_path))
    logger.info(f"Checksum manifest saved to {manifest_path}")
    
    return manifest

def verify_artifacts(manifest: Dict[str, str]) -> bool:
    """
    Verifies the integrity of all artifacts against the manifest.
    """
    logger.info("Verifying artifact integrity...")
    is_valid = True
    for rel_path, expected_hash in manifest.items():
        file_path = Path(rel_path)
        if not file_path.exists():
            logger.error(f"Missing artifact: {file_path}")
            is_valid = False
            continue
        
        actual_hash = compute_file_hash(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Integrity check failed for {file_path}: Expected {expected_hash}, Got {actual_hash}")
            is_valid = False
        else:
            logger.debug(f"Verified: {file_path}")
    
    return is_valid

def main():
    """
    Main entry point for validation.
    """
    logger.info("=== Starting Quickstart Validation ===")
    
    # 1. Setup
    ensure_directories()
    set_global_seed(SEED)
    
    # 2. Data Acquisition
    data_path = ensure_event_data(TARGET_EVENT)
    if not data_path:
        logger.error("Could not acquire data. Validation cannot proceed.")
        # If we can't get data, we might still want to check if the structure exists,
        # but the task implies running the pipeline.
        # For the sake of this task, we assume if data is missing, we fail gracefully.
        return 1
    
    # 3. Pipeline Execution
    try:
        results = run_pipeline(data_path)
        if not results:
            logger.error("Pipeline produced no results.")
            return 1
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1
    
    # 4. Checksum Generation
    try:
        manifest = generate_checksums()
        if not manifest:
            logger.warning("No artifacts found to checksum.")
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}", exc_info=True)
        return 1
    
    # 5. Verification
    if not verify_artifacts(manifest):
        logger.error("Artifact verification failed.")
        return 1
    
    logger.info("=== Quickstart Validation PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
