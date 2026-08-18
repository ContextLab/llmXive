"""
T052: Determinism Verification Script

Runs the smoke test (T050) twice with the same seed and verifies that
the SHA-256 checksums of all output CSVs and the final report are identical.

Usage:
    python code/scripts/verify_determinism.py
"""
import hashlib
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.scripts.run_smoke_test_with_profiling import run_smoke_test_with_profiling

# Configuration
SEED = 42
RUNS = 2
RESULTS_DIR = project_root / "results"
SMOKETEMP_DIR = project_root / "results_smoke_tmp"

# Files to verify checksums for
TARGET_FILES = [
    "raw_evaluations.csv",
    "stability_metrics.csv",
    "correlation_results.csv",
    "permutation_results.csv",
    "final_report.md"
]

def setup_logger():
    """Configure logging for the script."""
    return setup_logging("verify_determinism", level=logging.INFO)

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_pipeline_run(run_id: int, logger: logging.Logger) -> Dict[str, str]:
    """
    Run the smoke test pipeline once.
    Returns a dictionary of file paths -> checksums.
    """
    logger.info(f"--- Starting Determinism Run {run_id + 1} ---")
    
    # Set seed for reproducibility
    set_seed(SEED)
    
    # Clean previous results to ensure fresh generation
    if RESULTS_DIR.exists():
        for f in TARGET_FILES:
            p = RESULTS_DIR / f
            if p.exists():
                p.unlink()
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the smoke test
    # Note: run_smoke_test_with_profiling is expected to orchestrate the full pipeline
    # on a small subset of datasets.
    try:
        run_smoke_test_with_profiling(seed=SEED)
    except Exception as e:
        logger.error(f"Pipeline run {run_id + 1} failed: {e}")
        raise

    # Compute checksums for target files
    checksums = {}
    for filename in TARGET_FILES:
        filepath = RESULTS_DIR / filename
        if not filepath.exists():
            logger.error(f"Expected output file missing: {filename}")
            raise FileNotFoundError(f"Missing output: {filename}")
        
        checksum = compute_file_hash(filepath)
        checksums[filename] = checksum
        logger.info(f"  {filename}: {checksum[:16]}...")
    
    logger.info(f"--- Run {run_id + 1} completed successfully ---")
    return checksums

def compare_checksums(
    run1_checksums: Dict[str, str], 
    run2_checksums: Dict[str, str]
) -> Tuple[bool, List[str]]:
    """
    Compare checksums from two runs.
    Returns (is_deterministic, list_of_differences).
    """
    differences = []
    for filename in TARGET_FILES:
        c1 = run1_checksums.get(filename)
        c2 = run2_checksums.get(filename)
        
        if c1 != c2:
            differences.append(f"{filename}: Run1={c1[:16]}... vs Run2={c2[:16]}...")
    
    return len(differences) == 0, differences

def main():
    """Main entry point for the determinism verification."""
    logger = setup_logger()
    logger.info("Starting Determinism Verification (T052)")
    logger.info(f"Seed: {SEED}, Runs: {RUNS}")
    
    all_checksums = []
    
    try:
        for i in range(RUNS):
            checksums = run_pipeline_run(i, logger)
            all_checksums.append(checksums)
        
        if len(all_checksums) < 2:
            logger.error("Not enough runs completed to compare.")
            sys.exit(1)
        
        logger.info("--- Comparing Results ---")
        is_deterministic, differences = compare_checksums(all_checksums[0], all_checksums[1])
        
        if is_deterministic:
            logger.info("SUCCESS: All output files are identical across runs.")
            logger.info("Determinism verified: Random seed pinning is effective.")
            sys.exit(0)
        else:
            logger.error("FAILURE: Output files differ between runs.")
            for diff in differences:
                logger.error(f"  DIFF: {diff}")
            logger.error("Determinism verification failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Verification process failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()