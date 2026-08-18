"""
Runner script for T021c: Metric collection for covariate adjustment.
Executes radon and cloc to gather LOC and Cyclomatic Complexity.
"""
import os
import sys
import json
import logging
import subprocess
import shutil
from pathlib import Path
from validation import collect_metrics_for_covariates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure data/raw directory exists."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)

def check_dependencies():
    """Check if radon and cloc are installed."""
    for cmd in ['radon', 'cloc']:
        if not shutil.which(cmd):
            logger.error(f"Dependency '{cmd}' not found in PATH. Please install it.")
            sys.exit(1)
    logger.info("Dependencies (radon, cloc) verified.")

def main():
    """
    Main entry point for T021c.
    Collects LOC and CC metrics for candidate repos and writes to data/raw/repo_metrics.json.
    """
    logger.info("Starting T021c: Metric Collection for Covariate Adjustment")
    
    ensure_dirs()
    check_dependencies()

    # The validation module contains the logic to scan repos and call radon/cloc
    # We assume candidate repos are defined in a config or hardcoded list for this phase
    # based on T021a's selection logic.
    # For this pilot, we expect the candidate list to be populated or read from a file.
    # If no candidates exist, we must fail loudly rather than fabricate.
    
    candidates_path = "data/raw/candidate_repos.json"
    if not os.path.exists(candidates_path):
        logger.error(f"Candidate repo list not found at {candidates_path}. "
                     "T021a must run first to populate this.")
        sys.exit(1)

    with open(candidates_path, 'r') as f:
        candidates = json.load(f)

    if not candidates:
        logger.error("No candidate repositories found. Cannot proceed with metrics.")
        sys.exit(1)

    logger.info(f"Processing {len(candidates)} candidate repositories...")

    # Collect metrics using the function from validation.py
    # This function internally runs: radon cc -a -s and cloc --json
    metrics_data = collect_metrics_for_covariates(candidates)

    output_path = "data/raw/repo_metrics.json"
    try:
        with open(output_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        logger.info(f"Successfully wrote metrics to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write metrics to {output_path}: {e}")
        sys.exit(1)

    # Verification: Assert the file exists and contains numeric data
    if not os.path.exists(output_path):
        logger.error("Verification failed: Output file missing.")
        sys.exit(1)

    with open(output_path, 'r') as f:
        data = json.load(f)
    
    for repo_id, metrics in data.items():
        if 'loc' not in metrics or 'cc' not in metrics:
            logger.error(f"Verification failed: Missing 'loc' or 'cc' for {repo_id}")
            sys.exit(1)
        if not isinstance(metrics['loc'], (int, float)) or not isinstance(metrics['cc'], (int, float)):
            logger.error(f"Verification failed: Non-numeric metrics for {repo_id}")
            sys.exit(1)

    logger.info("T021c completed successfully. Metrics validated.")

if __name__ == "__main__":
    main()
