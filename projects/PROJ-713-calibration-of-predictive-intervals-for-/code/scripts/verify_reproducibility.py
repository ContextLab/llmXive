"""
Verification script for T034b: Reproducibility Hash Comparison.

This script runs the evaluation pipeline twice with pinned seeds and
compares the content hashes of the resulting artifacts to ensure
deterministic, reproducible execution.

Output:
  results/reproducibility_report.json: Contains hashes from Run 1 and Run 2
  and a boolean 'verified' flag indicating if they match.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, set_seed, ensure_dirs
from utils.logger import get_logger
from utils.checksum import compute_file_checksum
from evaluation.runner import main as run_evaluation_main

logger = get_logger(__name__)

RESULTS_DIR = PROJECT_ROOT / "results"
TEMP_RUN1_DIR = PROJECT_ROOT / "results" / "run1_backup"
TEMP_RUN2_DIR = PROJECT_ROOT / "results" / "run2_backup"
REPORT_PATH = RESULTS_DIR / "reproducibility_report.json"

# Files to track for reproducibility
TARGET_FILES = [
    "coverage.csv",
    "distributional_metrics.csv",
    # Add other deterministic outputs if they exist
    # "significance_test.csv",
    # "conformal_results.csv",
]

def compute_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not filepath.exists():
        return None
    return compute_file_checksum(str(filepath))

def backup_results(run_name: str):
    """Backup current results to a temporary directory."""
    if not RESULTS_DIR.exists():
        return
    backup_path = PROJECT_ROOT / "results" / run_name
    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(RESULTS_DIR, backup_path)
    logger.info(f"Backed up results to {backup_path}")

def restore_results(run_name: str):
    """Restore results from a backup if it exists."""
    backup_path = PROJECT_ROOT / "results" / run_name
    if backup_path.exists():
        # Clear current results
        for f in RESULTS_DIR.glob("*.csv"):
            f.unlink()
        # Restore
        for item in backup_path.iterdir():
            dest = RESULTS_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        logger.info(f"Restored results from {backup_path}")
        shutil.rmtree(backup_path)

def run_pipeline(run_id: int):
    """Execute the evaluation pipeline."""
    logger.info(f"--- Starting Pipeline Run {run_id} ---")
    set_seed(Config.SEED)  # Ensure seed is pinned
    
    # Clear previous results to ensure clean state
    if RESULTS_DIR.exists():
        for f in RESULTS_DIR.glob("*.csv"):
            f.unlink()
    
    # Construct args for the runner
    # We assume the runner uses config.yaml which is already set up
    # The runner's main() usually handles its own args, but we can simulate a call
    # by setting sys.argv or calling the core logic directly if exposed.
    # Based on API: evaluation.runner::main
    # We will call it with a config path if needed, or let it default.
    
    try:
        # Simulate command line args for the runner
        sys.argv = [
            "scripts/verify_reproducibility.py", 
            "--config", str(PROJECT_ROOT / "code" / "config.yaml")
        ]
        # We need to call the actual logic, not just main which might parse sys.argv again
        # Assuming run_evaluation() is the core logic or main() handles it cleanly.
        # Let's try calling main() with a clean sys.argv context.
        
        # To avoid sys.argv side effects in a loop, we'll use a subprocess or 
        # carefully manage the state. However, for this task, we assume the 
        # runner is robust.
        
        # Direct call attempt (assuming main() is idempotent and reads config)
        # Note: In a real scenario, we might need to invoke the script via subprocess
        # to ensure a fresh Python interpreter state for seed resetting.
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "evaluation.runner", "--config", str(PROJECT_ROOT / "code" / "config.yaml")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Run {run_id} failed: {result.stderr}")
            raise RuntimeError(f"Pipeline run {run_id} failed")
        
        logger.info(f"--- Pipeline Run {run_id} Completed Successfully ---")
    except Exception as e:
        logger.error(f"Error during run {run_id}: {e}")
        raise

def collect_hashes(run_id: int) -> Dict[str, str]:
    """Collect hashes of target files."""
    hashes = {}
    for fname in TARGET_FILES:
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            h = compute_hash(fpath)
            hashes[fname] = h
            logger.debug(f"Hash for {fname} (Run {run_id}): {h}")
        else:
            logger.warning(f"Target file {fname} not found for Run {run_id}")
            hashes[fname] = None
    return hashes

def compare_hashes(run1_hashes: Dict[str, str], run2_hashes: Dict[str, str]) -> bool:
    """Compare hashes from two runs."""
    if set(run1_hashes.keys()) != set(run2_hashes.keys()):
        return False
    
    for fname, h1 in run1_hashes.items():
        h2 = run2_hashes.get(fname)
        if h1 != h2:
            logger.warning(f"Mismatch for {fname}: Run1={h1}, Run2={h2}")
            return False
    return True

def main():
    logger.info("Starting Reproducibility Verification (T034b)")
    
    # Ensure directories exist
    ensure_dirs()
    
    # Run 1
    try:
        run_pipeline(1)
        run1_hashes = collect_hashes(1)
    except Exception as e:
        logger.critical(f"Run 1 failed. Aborting verification.")
        sys.exit(1)

    # Run 2
    try:
        run_pipeline(2)
        run2_hashes = collect_hashes(2)
    except Exception as e:
        logger.critical(f"Run 2 failed. Aborting verification.")
        sys.exit(1)

    # Compare
    is_verified = compare_hashes(run1_hashes, run2_hashes)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "seed": Config.SEED,
        "verified": is_verified,
        "run_1_hashes": run1_hashes,
        "run_2_hashes": run2_hashes,
        "target_files": TARGET_FILES
    }

    # Save Report
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reproducibility report saved to {REPORT_PATH}")
    
    if is_verified:
        logger.info("SUCCESS: Outputs are identical across runs.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Outputs differ between runs. Reproducibility check failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
