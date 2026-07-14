import os
import sys
import subprocess
import logging
from utils import setup_logging

logger = logging.getLogger(__name__)

def run_script(script_name: str) -> bool:
    """Run a single script."""
    cmd = [sys.executable, os.path.join("code", script_name)]
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

def main():
    """Quickstart fix: ensure critical artifacts are generated."""
    setup_logging("INFO")
    
    # Ensure data exists
    if not run_script("t011_ensure_data.py"):
        logger.error("Failed to ensure data.")
        sys.exit(1)
    
    # Run baseline analysis
    if not run_script("t012_run_baseline_analysis.py"):
        logger.error("Failed to run baseline analysis.")
        sys.exit(1)
    
    # Record baseline metrics (T013)
    if not run_script("t013_record_baseline_metrics.py"):
        logger.error("Failed to record baseline metrics.")
        sys.exit(1)
    
    # Run Null FPR (T032) to generate null_fpr_metrics.json
    if not run_script("t032_permutation_null_fpr.py"):
        logger.error("Failed to run null FPR analysis.")
        sys.exit(1)

    logger.info("Quickstart fix completed. Critical artifacts generated.")

if __name__ == "__main__":
    main()
