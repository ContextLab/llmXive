"""
T036: Verify existence and non-zero size of required output artifacts.

This script checks that the visualization and reporting pipeline (T032-T035)
successfully produced the required files:
- data/outputs/scatter_tpsa_vs_half_life.png
- data/outputs/residuals.png
- data/outputs/qq_plot.png
- results_report.md

It exits with code 0 if all checks pass, or code 1 if any check fails.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define required artifacts relative to project root
REQUIRED_ARTIFACTS = [
    "data/outputs/scatter_tpsa_vs_half_life.png",
    "data/outputs/residuals.png",
    "data/outputs/qq_plot.png",
    "results_report.md"
]

def verify_artifact(path_str: str) -> bool:
    """
    Verify that an artifact exists and has non-zero size.
    
    Args:
        path_str: Relative path to the artifact from project root.
        
    Returns:
        True if artifact exists and size > 0, False otherwise.
    """
    full_path = Path(path_str)
    
    if not full_path.exists():
        logger.error(f"MISSING: {path_str} does not exist.")
        return False
    
    file_size = full_path.stat().st_size
    if file_size == 0:
        logger.error(f"EMPTY: {path_str} exists but has 0 bytes.")
        return False
    
    logger.info(f"OK: {path_str} exists ({file_size} bytes).")
    return True

def main():
    """
    Main verification routine.
    
    Checks all required artifacts. Exits with 0 if all pass, 1 if any fail.
    """
    logger.info("Starting T036 verification of output artifacts...")
    
    all_passed = True
    missing_or_empty = []
    
    for artifact_path in REQUIRED_ARTIFACTS:
        if not verify_artifact(artifact_path):
            all_passed = False
            missing_or_empty.append(artifact_path)
    
    if all_passed:
        logger.info("SUCCESS: All required artifacts exist and are non-empty.")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: {len(missing_or_empty)} artifacts are missing or empty:")
        for path in missing_or_empty:
            logger.error(f"  - {path}")
        logger.error("Ensure T032 (scatter plots), T033 (residual plots), and T034 (report) have run successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()