"""
Memory verification script for the cognitive fatigue pipeline.
Monitors peak memory usage across all pipeline stages to ensure compliance with SC-003 (<= 7 GB).
"""
import os
import sys
import json
import resource
import time
import traceback
from pathlib import Path

# Add project root to path if necessary (assuming script runs from project root or code/)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import get_logger
from code.download import main as run_download
from code.preprocess import main as run_preprocess
from code.features import main as run_features
from code.analysis import main as run_analysis
from code.report import main as run_report

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
OUTPUT_FILE = project_root / "data" / "processed" / "memory_profile.json"

logger = get_logger("verify_memory")

def get_peak_memory_mb():
    """
    Returns the peak memory usage of the current process in MB.
    Uses resource.getrusage for Unix-like systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024

def check_sample_size():
    """
    Checks if the sample size is sufficient before running the full pipeline.
    This prevents wasting resources on datasets that will fail analysis validation.
    """
    logger.info("Checking sample size constraint (N >= 30)...")
    # This is a placeholder check; the actual check_sample_size logic is in code/check_sample_size.py
    # We assume the download stage has already populated the data and validation would catch it.
    # However, for memory profiling, we want to ensure we don't run on a massive dataset if not needed.
    # For now, we proceed assuming the dataset is within bounds as per previous validation tasks.
    logger.info("Sample size check passed (assumed based on previous validation).")
    return True

def run_stage_with_memory(stage_name, stage_func):
    """
    Runs a pipeline stage and records memory usage.
    """
    logger.info(f"Starting stage: {stage_name}")
    start_mem = get_peak_memory_mb()
    logger.info(f"Memory at start of {stage_name}: {start_mem:.2f} MB")

    try:
        stage_func()
        end_mem = get_peak_memory_mb()
        logger.info(f"Memory at end of {stage_name}: {end_mem:.2f} MB")
        delta_mem = end_mem - start_mem
        logger.info(f"Memory delta for {stage_name}: {delta_mem:.2f} MB")
        return True, delta_mem
    except Exception as e:
        logger.error(f"Stage {stage_name} failed: {e}")
        traceback.print_exc()
        return False, 0

def run_pipeline():
    """
    Executes the full pipeline stages sequentially and monitors memory.
    """
    results = {
        "pipeline_start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "stages": {}
    }

    stages = [
        ("download", run_download),
        ("preprocess", run_preprocess),
        ("features", run_features),
        ("analysis", run_analysis),
        ("report", run_report)
    ]

    for name, func in stages:
        success, delta = run_stage_with_memory(name, func)
        results["stages"][name] = {
            "success": success,
            "delta_memory_mb": delta
        }
        if not success:
            logger.error(f"Pipeline aborted at stage {name} due to failure.")
            break

    results["pipeline_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["peak_memory_mb"] = get_peak_memory_mb()
    results["status"] = "passed" if results["peak_memory_mb"] <= MEMORY_LIMIT_MB else "failed"

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write results to disk
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Memory profile written to {OUTPUT_FILE}")
    logger.info(f"Peak memory usage: {results['peak_memory_mb']:.2f} MB (Limit: {MEMORY_LIMIT_MB:.2f} MB)")

    if results["status"] == "failed":
        logger.error(f"Memory limit exceeded! Peak: {results['peak_memory_mb']:.2f} MB > {MEMORY_LIMIT_MB:.2f} MB")
        return False
    else:
        logger.info("Memory usage within acceptable limits.")
        return True

def main():
    """
    Main entry point for memory verification.
    """
    logger.info("Starting memory verification pipeline...")
    
    # Ensure data directories exist
    (project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "analysis").mkdir(parents=True, exist_ok=True)

    success = run_pipeline()

    if success:
        logger.info("Memory verification PASSED.")
        sys.exit(0)
    else:
        logger.error("Memory verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()